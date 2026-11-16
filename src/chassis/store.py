"""Local, transport-independent record mutations. Caller identity is explicit."""

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import TypeAdapter

from chassis.atomic import vault_lock
from chassis.errors import ConflictError, WriteError
from chassis.git import Identity, ensure_clean, ensure_repository
from chassis.markdown import ParsedRecord, RecordFileError, parse_record
from chassis.models import Record, RecordId
from chassis.policy import authorize_writer, require_grant
from chassis.transactions import persist_record
from chassis.validation import read_vault, validate_records

IMMUTABLE = {"id", "version", "updated_at"}


class RecordStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def _find_path(self, identifier: str) -> Path:
        paths = []
        for kind in ("venture", "initiative", "task"):
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

    def update_record(self, identifier: str, changes: Mapping, expected_version: int,
                      agent: str) -> dict:
        authorize_writer(self.root, agent)
        if not isinstance(changes, Mapping):
            raise WriteError("changes must be an object")
        changes = dict(changes)
        forbidden = sorted(IMMUTABLE.intersection(changes))
        if forbidden:
            raise WriteError(f"immutable fields: {', '.join(forbidden)}", fields=forbidden)
        TypeAdapter(RecordId).validate_python(identifier)
        if type(expected_version) is not int or expected_version < 1:
            raise WriteError("expected_version must be a positive integer")
        identity = Identity.from_env("AGENT")
        with vault_lock(self.root):
            policy = authorize_writer(self.root, agent)
            path = self._find_path(identifier)
            original = path.read_bytes()
            try:
                current = parse_record(original.decode("utf-8"), path)
            except (RecordFileError, UnicodeError):
                ensure_clean(self.root, path)
                raise
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
