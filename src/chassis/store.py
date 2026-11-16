"""Local, transport-independent record mutations. Caller identity is explicit."""

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import TypeAdapter

from chassis.atomic import vault_lock
from chassis.errors import ConflictError, WriteError
from chassis.git import Identity, commit_file, ensure_clean, ensure_repository, has_record_changes
from chassis.markdown import ParsedRecord, RecordFileError, parse_record, read_frontmatter
from chassis.models import RECORD_TYPES, Record, RecordId, RecordType
from chassis.policy import authorize_writer, require_grant
from chassis.templates import expand_template, template_sections
from chassis.transactions import persist_record, refresh_committed
from chassis.validation import load_vault, read_vault, validate_records

IMMUTABLE = {"id", "version", "updated_at"}


class RecordStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def _find_path(self, identifier: str) -> Path:
        paths = []
        for kind in RECORD_TYPES:
            path = self.root / "records" / f"{kind}s" / f"{identifier}.md"
            for part in (path.parent.parent, path.parent, path):
                if part.is_symlink():
                    raise RecordFileError(f"{part}: record paths cannot be symlinks")
            if path.is_file():
                paths.append(path)
        if len(paths) != 1:
            reason = "record not found" if not paths else "duplicate ID"
            raise WriteError(f"{identifier}: {reason}", id=identifier)
        return paths[0]

    def _read_current(self, identifier: str) -> tuple[ParsedRecord, bytes]:
        path = self._find_path(identifier)
        original = path.read_bytes()
        try:
            return parse_record(original.decode("utf-8"), path), original
        except (RecordFileError, UnicodeError):
            ensure_clean(self.root, path)
            raise

    def _check_scopes(self, identifier, changes, policy, agent) -> None:
        fields = read_frontmatter(self._find_path(identifier))
        venture, kind = TypeAdapter(tuple[RecordId, RecordType]).validate_python(
            (fields.get("venture"), fields.get("type")))
        require_grant(policy, agent, venture, kind)
        venture, kind = changes.get("venture", venture), changes.get("type", kind)
        if isinstance(venture, str) and isinstance(kind, str):
            require_grant(policy, agent, venture, kind)

    def update_record(self, identifier: str, changes: Mapping, expected_version: int,
                      agent: str) -> dict:
        policy = authorize_writer(self.root, agent)
        if not isinstance(changes, Mapping):
            raise WriteError("changes must be an object")
        changes = dict(changes)
        forbidden = sorted(IMMUTABLE.intersection(changes))
        if forbidden:
            raise WriteError(f"immutable fields: {', '.join(forbidden)}", fields=forbidden)
        TypeAdapter(RecordId).validate_python(identifier)
        if type(expected_version) is not int or expected_version < 1:
            raise WriteError("expected_version must be a positive integer")
        if "body" in changes and not isinstance(changes["body"], str):
            raise WriteError("body must be a string")
        # Authorize both scopes from frontmatter before reading any record body.
        self._check_scopes(identifier, changes, policy, agent)
        identity = Identity.from_env("AGENT")
        with vault_lock(self.root):
            policy = authorize_writer(self.root, agent)
            self._check_scopes(identifier, changes, policy, agent)
            current, original = self._read_current(identifier)
            path = current.path
            require_grant(policy, agent, current.record.venture, current.record.type)
            if current.record.version != expected_version:
                raise ConflictError(identifier, expected_version, current.record.version)
            ensure_repository(self.root)
            ensure_clean(self.root, path)
            body = changes.pop("body", current.body)
            timestamp = max(datetime.now(timezone.utc), current.record.updated_at + timedelta(microseconds=1))
            fields = current.record.model_dump() | changes | {
                "version": current.record.version + 1, "updated_at": timestamp}
            record = Record.model_validate(fields)
            if record.type != current.record.type:
                raise WriteError("type cannot change the stable record path")
            require_grant(policy, agent, record.venture, record.type)
            proposed = ParsedRecord(path, record, body)
            items = read_vault(self.root)
            validate_records(self.root, [proposed if item.record.id == identifier else item
                                         for item in items], policy)
            return persist_record(self.root, proposed, original, identity,
                                  f"chassis: update {identifier} v{record.version} by {agent}")

    def create_record(self, record_type: str, fields: Mapping, agent: str) -> dict:
        policy = authorize_writer(self.root, agent)
        if not isinstance(fields, Mapping):
            raise WriteError("fields must be an object")
        fields = dict(fields)
        forbidden = sorted({"version", "updated_at"}.intersection(fields))
        if forbidden:
            raise WriteError(f"immutable fields: {', '.join(forbidden)}", fields=forbidden)
        if "type" in fields:
            raise WriteError("type must be supplied only as the create_record type argument")
        body = fields.pop("body", "")
        if not isinstance(body, str):
            raise WriteError("body must be a string")
        record = Record.model_validate(fields | {"type": record_type, "version": 1,
                                                "updated_at": datetime.now(timezone.utc)})
        require_grant(policy, agent, record.venture, record.type)
        identity = Identity.from_env("AGENT")
        with vault_lock(self.root):
            policy = authorize_writer(self.root, agent)
            require_grant(policy, agent, record.venture, record.type)
            items = read_vault(self.root)
            if any(item.record.id == record.id for item in items):
                raise WriteError(f"{record.id}: duplicate ID", id=record.id)
            path = self.root / "records" / f"{record.type}s" / f"{record.id}.md"
            proposed = ParsedRecord(path, record, body)
            validate_records(self.root, [*items, proposed], policy)
            ensure_repository(self.root)
            return persist_record(self.root, proposed, None, identity,
                                  f"chassis: create {record.id} v1 by {agent}")

    def create_from_template(self, template: str, venture: str, fields: Mapping,
                             agent: str) -> dict:
        """Authorize before template I/O, then use the sole record-create transaction."""
        policy = authorize_writer(self.root, agent)
        template_sections(template)
        TypeAdapter(RecordId).validate_python(venture)
        require_grant(policy, agent, venture, template)
        expanded = expand_template(self.root, template, fields)
        return self.create_record(template, expanded | {"venture": venture, "parent": venture}, agent)

    def commit_human(self, path: str | Path) -> dict:
        """Commit one validated manual edit exactly as written, as the human."""
        path = Path(path)
        if not path.is_absolute():
            path = self.root / path
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise WriteError("commit-human requires a record path within the vault") from exc
        if (len(relative.parts) != 3 or relative.parts[0] != "records"
                or relative.parts[1] not in {f"{kind}s" for kind in RECORD_TYPES}
                or path.suffix != ".md" or ".." in relative.parts):
            raise WriteError("commit-human requires a canonical record path under records/")
        identity = Identity.from_env("HUMAN")
        with vault_lock(self.root):
            ensure_repository(self.root)
            records = load_vault(self.root)
            item = next((item for item in records.values() if item.path == path), None)
            if item is None:
                raise WriteError(f"{relative}: record path not found")
            if not has_record_changes(self.root, path):
                raise WriteError(f"{relative}: no uncommitted human edit to commit")
            commit = commit_file(self.root, path, identity, f"chassis: human edit {item.record.id}")
            refresh_committed(self.root, item, commit)
            return {"path": relative.as_posix(), "commit": commit}
