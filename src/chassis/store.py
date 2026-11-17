"""Local, transport-independent record mutations. Caller identity is explicit."""

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from chassis.atomic import vault_lock
from chassis.audit import audited
from chassis.identity import caller_id
from chassis.errors import AuthorizationError, ConflictError, NotFoundError, WriteError
from chassis.git import Identity, commit_file, ensure_clean, ensure_repository, has_record_changes
from chassis.markdown import ParsedRecord, RecordFileError, parse_record, read_frontmatter
from chassis.models import RECORD_TYPES, Record, RecordId, RecordType
from chassis.policy import authorize_writer, require_grant, require_clearance, visible_records, can_read_record
from chassis.templates import expand_template, template_sections
from chassis.transactions import persist_record, refresh_committed
from chassis.validation import read_vault, validate_records

IMMUTABLE = {"id", "version", "updated_at"}
MAX_RECORD_BODY = 64 * 1024


def _require_body_limit(body):
    if len(body.encode()) > MAX_RECORD_BODY:
        raise WriteError("Record body exceeds the edit limit")


class RecordStore:
    def __init__(self, root: Path, token=None, *, identity=None, normal_only=False):
        self.root = Path(root).resolve()
        self.token = token
        self.identity, self.normal_only = identity, normal_only

    def _authorize_update(self, agent):
        policy = authorize_writer(self.root, agent, self.token)
        if self.normal_only and policy.agents[agent].clearance != "normal":
            raise AuthorizationError("Write not permitted")
        return policy

    def _find_path(self, identifier: str) -> Path:
        paths = []
        for kind in RECORD_TYPES:
            path = self.root / "records" / f"{kind}s" / f"{identifier}.md"
            for part in (path.parent.parent, path.parent, path):
                if part.is_symlink():
                    raise RecordFileError(f"{part}: record paths cannot be symlinks")
            if path.is_file():
                paths.append(path)
        if not paths:
            raise NotFoundError(f"{identifier}: record not found", id=identifier)
        if len(paths) > 1:
            raise WriteError(f"{identifier}: duplicate ID", id=identifier)
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
        try:
            fields = read_frontmatter(self._find_path(identifier))
            require_clearance(policy, agent, fields.get("sensitivity", "normal"))
            require_clearance(policy, agent, changes.get("sensitivity", fields.get("sensitivity", "normal")))
            venture, kind = TypeAdapter(tuple[RecordId, RecordType]).validate_python(
                (fields.get("venture"), fields.get("type")))
            require_grant(policy, agent, venture, kind)
            venture, kind = changes.get("venture", venture), changes.get("type", kind)
            if isinstance(venture, str) and isinstance(kind, str):
                require_grant(policy, agent, venture, kind)
        except (RecordFileError, WriteError, ValidationError, OSError):
            # If target metadata cannot prove a scope, no path or parser detail escapes.
            raise AuthorizationError("Write not permitted") from None

    def _read_sources(self):
        try:
            return read_vault(self.root)
        except (RecordFileError, OSError):
            raise RecordFileError("Records unavailable; source validation failed") from None

    def _validate_sources(self, items, policy, agent):
        try:
            return validate_records(self.root, items, policy)
        except RecordFileError as exc:
            # Whole-vault validation can name records unrelated to the write target.
            visible = {item.record.id for item in items if can_read_record(item.record.model_dump(), policy, agent)}
            named = set(re.findall(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", str(exc)))
            hidden = {item.record.id for item in items} - visible
            if not named & hidden:
                raise
            raise RecordFileError("Records unavailable; source validation failed") from None

    @audited("update_record")
    def update_record(self, identifier: str, changes: Mapping, expected_version: int,
                      agent: str) -> dict:
        policy = self._authorize_update(agent)
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
        if "body" in changes:
            _require_body_limit(changes["body"])
        # Authorize both scopes from frontmatter before reading any record body.
        self._check_scopes(identifier, changes, policy, agent)
        identity = self.identity or Identity.from_env("AGENT")
        with vault_lock(self.root):
            policy = self._authorize_update(agent)
            self._check_scopes(identifier, changes, policy, agent)
            current, original = self._read_current(identifier)
            path = current.path
            require_grant(policy, agent, current.record.venture, current.record.type)
            if current.record.version != expected_version:
                raise ConflictError(identifier, expected_version, current.record.version)
            ensure_repository(self.root)
            ensure_clean(self.root, path)
            body = changes.pop("body", current.body)
            _require_body_limit(body)
            timestamp = max(datetime.now(timezone.utc), current.record.updated_at + timedelta(microseconds=1))
            fields = current.record.model_dump() | changes | {
                "version": current.record.version + 1, "updated_at": timestamp}
            record = Record.model_validate(fields)
            if record.type != current.record.type:
                raise WriteError("type cannot change the stable record path")
            require_grant(policy, agent, record.venture, record.type)
            proposed = ParsedRecord(path, record, body)
            items = self._read_sources()
            self._require_readable_dependencies(proposed, items, policy, agent)
            self._validate_sources([proposed if item.record.id == identifier else item
                                    for item in items], policy, agent)
            references = self._visible_dependencies(proposed, items, policy, agent)
            result = persist_record(self.root, proposed, original, identity,
                                    f"chassis: update {identifier} v{record.version} by {agent}")
            result["record"]["depends_on"] = references
            return result

    @audited("create_record")
    def create_record(self, record_type: str, fields: Mapping, agent: str) -> dict:
        return self._create_record(record_type, fields, agent)

    def _create_record(self, record_type: str, fields: Mapping, agent: str) -> dict:
        policy = authorize_writer(self.root, agent, self.token)
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
        _require_body_limit(body)
        record = Record.model_validate(fields | {"type": record_type, "version": 1,
                                                "updated_at": datetime.now(timezone.utc)})
        require_grant(policy, agent, record.venture, record.type)
        require_clearance(policy, agent, record.sensitivity)
        identity = Identity.from_env("AGENT")
        with vault_lock(self.root):
            policy = authorize_writer(self.root, agent, self.token)
            require_grant(policy, agent, record.venture, record.type)
            require_clearance(policy, agent, record.sensitivity)
            items = self._read_sources()
            if any(item.record.id == record.id for item in items):
                raise WriteError(f"{record.id}: duplicate ID", id=record.id)
            path = self.root / "records" / f"{record.type}s" / f"{record.id}.md"
            proposed = ParsedRecord(path, record, body)
            self._require_readable_dependencies(proposed, items + [proposed], policy, agent)
            self._validate_sources([*items, proposed], policy, agent)
            ensure_repository(self.root)
            references = self._visible_dependencies(proposed, items, policy, agent)
            result = persist_record(self.root, proposed, None, identity,
                                    f"chassis: create {record.id} v1 by {agent}")
            result["record"]["depends_on"] = references
            return result

    @audited("create_from_template")
    def create_from_template(self, template: str, venture: str, fields: Mapping,
                             agent: str) -> dict:
        """Authorize before template I/O, then use the sole record-create transaction."""
        policy = authorize_writer(self.root, agent, self.token)
        template_sections(template)
        TypeAdapter(RecordId).validate_python(venture)
        require_grant(policy, agent, venture, template)
        if not isinstance(fields, Mapping):
            raise WriteError("fields must be an object")
        fields = dict(fields)
        # Reuse the create schema, including strict strings and owner trimming.
        # The complete proposal and policy are checked again by create_record.
        for name in ("owner", "sensitivity", "assigned_agent"):
            if name not in fields:
                continue
            field = Record.model_fields[name]
            try:
                fields[name] = TypeAdapter(field.rebuild_annotation()).validate_python(
                    fields.get(name, field.default))
            except ValidationError as exc:
                reason = exc.errors(include_input=False)[0]["msg"]
                raise WriteError(f"{name}: {reason}", field=name, reason=reason) from exc
        assigned = fields.get("assigned_agent")
        if assigned is not None and assigned not in policy.agents:
            raise WriteError(f"assigned_agent {assigned!r} is not a known agent id",
                             field="assigned_agent", reason="must be a known agent id")
        expanded = expand_template(self.root, template, fields)
        return self._create_record(template, expanded | {"venture": venture, "parent": venture}, agent)

    def _require_readable_dependencies(self, proposed, items, policy, agent):
        """Missing and unreadable dependency ids are the same refusal, with no id in the error."""
        rows = [item.record.model_dump(mode="json") for item in items
                if item.record.id != proposed.record.id]
        rows.append(proposed.record.model_dump(mode="json"))
        visible = {row["id"] for row in visible_records(rows, policy, agent)}
        if any(dependency not in visible for dependency in proposed.record.depends_on):
            raise WriteError("invalid dependency")

    def _visible_dependencies(self, proposed, items, policy, agent):
        rows = [item.record.model_dump(mode="json") for item in items
                if item.record.id != proposed.record.id] + [proposed.record.model_dump(mode="json")]
        record = next((r for r in visible_records(rows, policy, agent)
                       if r["id"] == proposed.record.id), None)
        if record is None:
            raise AuthorizationError("Write not permitted")
        return record["depends_on"]

    @audited("commit_human")
    def commit_human(self, path: str | Path) -> dict:
        """Commit one validated manual edit exactly as written, as the human."""
        agent = caller_id()
        policy = authorize_writer(self.root, agent, self.token)
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
        self._check_scopes(path.stem, {}, policy, agent)
        identity = Identity.from_env("HUMAN")
        with vault_lock(self.root):
            policy = authorize_writer(self.root, agent, self.token)
            self._check_scopes(path.stem, {}, policy, agent)
            ensure_repository(self.root)
            records = self._validate_sources(self._read_sources(), policy, agent)
            item = next((item for item in records.values() if item.path == path), None)
            if item is None:
                raise WriteError(f"{relative}: record path not found")
            if not has_record_changes(self.root, path):
                raise WriteError(f"{relative}: no uncommitted human edit to commit")
            commit = commit_file(self.root, path, identity, f"chassis: human edit {item.record.id}")
            refresh_committed(self.root, item, commit)
            return {"path": relative.as_posix(), "commit": commit}
