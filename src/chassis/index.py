"""Disposable SQLite projection of authoritative working-tree records."""

import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError

from chassis.atomic import vault_lock, write_atomic
from chassis.audit import audited, mark_denied
from chassis.identity import caller_id
from chassis.policy import authorize_reader, load_policy, visible_records
from chassis.git import record_activity
from chassis.markdown import ParsedRecord, RecordFileError, parse_record
from chassis.models import Record, iso_date
from chassis.validation import load_vault, read_vault, validate_records

SCHEMA = """
CREATE TABLE records (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    venture TEXT NOT NULL,
    status TEXT NOT NULL,
    parent TEXT,
    assigned_agent TEXT,
    sensitivity TEXT NOT NULL,
    title TEXT NOT NULL,
    next_step TEXT NOT NULL,
    next_milestone TEXT,
    milestone_due_at TEXT,
    due_at TEXT,
    blocker_reason TEXT,
    last_activity_at TEXT,
    body TEXT NOT NULL,
    record_json TEXT NOT NULL,
    source_path TEXT NOT NULL UNIQUE,
    mtime_ns INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    row_hash TEXT NOT NULL
);
PRAGMA user_version = 3;
"""
FIELDS = ("id", "type", "venture", "status", "parent", "assigned_agent",
          "sensitivity", "title", "next_step", "next_milestone", "milestone_due_at",
          "due_at", "blocker_reason", "last_activity_at")
FILTER_FIELDS = ("type", "venture", "status", "parent", "assigned_agent", "sensitivity",
                 "next_milestone", "milestone_due_at", "due_at", "blocker_reason", "last_activity_at")
NULL_FILTER_FIELDS = {"parent", "assigned_agent", "next_milestone", "milestone_due_at",
                      "due_at", "blocker_reason", "last_activity_at"}
COLUMNS = FIELDS + ("body", "record_json", "source_path", "mtime_ns", "content_hash", "row_hash")
INSERT = "INSERT OR REPLACE INTO records VALUES (" + ", ".join("?" for _ in COLUMNS) + ")"


class IndexFileError(ValueError):
    """An index storage failure with its filename, distinct from source errors."""


class _InvalidIndex(Exception):
    """Disposable cache schema or integrity is invalid."""


def _row_hash(row: tuple) -> str:
    try:
        encoded = json.dumps(row, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise _InvalidIndex("invalid cached value type") from exc
    return sha256(encoded.encode("utf-8")).hexdigest()


class RecordIndex:
    def __init__(self, root: Path, agent=None, token=None, *, drop_dangling=False):
        self.root = Path(root).resolve()
        self.agent, self.token = caller_id(agent), token
        self.drop_dangling = drop_dangling
        self.path = self.root / ".chassis" / "index.sqlite"

    def _check_path(self):
        for path in (self.path.parent, self.path):
            if path.is_symlink():
                raise IndexFileError(f"{path}: index paths cannot be symlinks")

    def _remember(self, rows, activity, item, relative, fingerprint):
        values = item.record.model_dump(mode="json") | {"last_activity_at": activity.get(relative)}
        row = tuple(values[field] for field in FIELDS) + (
            item.body, item.record.model_dump_json(), relative, *fingerprint)
        rows[relative] = row + (_row_hash(row),)

    def _source_rows(self, cached=None) -> dict[str, tuple]:
        cached, rows, pending = cached or {}, {}, []
        activity = record_activity(self.root)

        def read(path):
            try:
                before = path.stat()
                raw = path.read_bytes()
                after = path.stat()
                stats = ("st_mtime_ns", "st_ctime_ns", "st_size", "st_ino", "st_dev")
                if any(getattr(before, key) != getattr(after, key) for key in stats):
                    raise RecordFileError(f"{path}: source changed while reading; retry")
                relative = path.relative_to(self.root).as_posix()
                fingerprint = (after.st_mtime_ns, sha256(raw).hexdigest())
                old = cached.get(relative)
                if old is not None and fingerprint == (old["mtime_ns"], old["content_hash"]):
                    if _row_hash(tuple(old)[:-1]) != old["row_hash"]:
                        raise _InvalidIndex(f"damaged cached row: {relative}")
                    item = ParsedRecord(path, Record.model_validate_json(old["record_json"]), old["body"])
                else:
                    item = parse_record(raw.decode("utf-8"), path)
                pending.append((item, relative, fingerprint))
                return item
            except (OSError, UnicodeError) as exc:
                raise RecordFileError(f"{path}: {exc}") from exc

        if self.drop_dangling:
            # A deleted hidden target and a missing id are the same absent record.
            # Skip both before validation so a read does not fail or echo the id.
            items = read_vault(self.root, reader=read)
            known = {item.record.id for item in items}
            cleaned = []
            for item, relative, fingerprint in pending:
                kept = [dependency for dependency in item.record.depends_on if dependency in known]
                if kept != list(item.record.depends_on):
                    item = ParsedRecord(item.path, item.record.model_copy(update={"depends_on": kept}), item.body)
                cleaned.append((item, relative, fingerprint))
            validate_records(self.root, [item for item, _, _ in cleaned], load_policy(self.root))
            for item, relative, fingerprint in cleaned:
                self._remember(rows, activity, item, relative, fingerprint)
            return rows
        load_vault(self.root, reader=read)
        for item, relative, fingerprint in pending:
            self._remember(rows, activity, item, relative, fingerprint)
        return rows

    @audited("rebuild", many=True)
    def rebuild(self) -> int:
        """Replace the entire cache only after all source records validate."""
        policy = authorize_reader(self.root, self.agent, self.token)
        if policy is None:
            mark_denied()
            return 0
        with vault_lock(self.root):
            policy = authorize_reader(self.root, self.agent, self.token)
            if policy is None:
                mark_denied()
                return 0
            try:
                self._rebuild_locked()
                return len(visible_records(self._query_locked("", ()), policy, self.agent))
            except RecordFileError:
                raise RecordFileError("Records unavailable; source validation failed") from None

    def _rebuild_locked(self) -> int:
        """Caller holds vault_lock, including callers in the mutation layer."""
        self._check_path()
        rows = self._source_rows()
        with closing(sqlite3.connect(":memory:")) as connection:
            with connection:
                connection.executescript(SCHEMA)
                connection.executemany(INSERT, rows.values())
            write_atomic(self.path, connection.serialize())
        return len(rows)

    def _refresh(self, connection):
        cached = {row["source_path"]: row for row in connection.execute("SELECT * FROM records")}
        rows = self._source_rows(cached)
        changed = [row for path, row in rows.items() if path not in cached or row != tuple(cached[path])]
        with connection:
            connection.executemany("DELETE FROM records WHERE source_path = ?",
                                   [(path,) for path in cached.keys() - rows.keys()])
            connection.executemany(INSERT, changed)

    def _query(self, where: str = "", parameters: tuple = ()) -> list[dict]:
        with vault_lock(self.root):
            return self._query_locked(where, parameters)

    def _query_locked(self, where: str, parameters: tuple) -> list[dict]:
        self._check_path()
        if not self.path.exists():
            self._rebuild_locked()
        for attempt in range(2):
            try:
                return self._read(where, parameters)
            except (sqlite3.DatabaseError, _InvalidIndex, ValidationError, json.JSONDecodeError) as exc:
                if isinstance(exc, sqlite3.DatabaseError) and (exc.sqlite_errorcode & 0xFF) not in {
                        sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB}:
                    raise IndexFileError(f"{self.path}: {exc}") from exc
                if attempt:
                    raise IndexFileError(f"{self.path}: cache remains invalid after rebuild: {exc}") from exc
                self._rebuild_locked()

    def _read(self, where, parameters):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            connection.create_function("casefold", 1, str.casefold, deterministic=True)
            columns = tuple(row["name"] for row in connection.execute("PRAGMA table_info(records)"))
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            checks = [row[0] for row in connection.execute("PRAGMA quick_check")]
            if version != 3 or columns != COLUMNS or checks != ["ok"]:
                raise _InvalidIndex("unexpected cache schema, version, or integrity check")
            self._refresh(connection)
            rows = connection.execute(
                "SELECT record_json, body, last_activity_at FROM records " + where + " ORDER BY id",
                parameters).fetchall()
        return [json.loads(row["record_json"]) | {"body": row["body"],
                "last_activity_at": row["last_activity_at"]} for row in rows]

    def _visible(self):
        policy = authorize_reader(self.root, self.agent, self.token)
        if policy is None:
            mark_denied()
            return []
        with vault_lock(self.root):
            return self._visible_locked()

    def _visible_locked(self):
        """Same authorization projection when a caller already holds the vault lock."""
        policy = authorize_reader(self.root, self.agent, self.token)
        if policy is None:
            mark_denied()
            return []
        try:
            records = self._query_locked("", ())
        except RecordFileError:
            raise RecordFileError("Records unavailable; source validation failed") from None
        return visible_records(records, policy, self.agent)

    @audited("list_records", many=True)
    def list_records(self, filters: Mapping[str, str | None] | None = None) -> list[dict]:
        """AND exact filters; omitted fields are unrestricted, None matches null."""
        clauses, parameters = [], []
        for field, value in (filters or {}).items():
            if field not in FILTER_FIELDS:
                raise ValueError(f"Unknown filter field: {field}")
            if not isinstance(value, str) and not (
                    value is None and field in NULL_FILTER_FIELDS):
                raise ValueError(f"Invalid filter value for {field}: {value!r}")
            if value is not None and field in {"milestone_due_at", "due_at"}:
                try:
                    value = iso_date(value).isoformat()
                except ValueError as exc:
                    raise ValueError(f"Invalid filter value for {field}: {exc}") from exc
            clauses.append(f"{field} IS ?")
            parameters.append(value)
        return [r for r in self._visible()
                if all(r[field] == value for field, value in zip((filters or {}), parameters))]

    @audited("read_record")
    def get_record(self, identifier: str) -> dict | None:
        return next((r for r in self._visible() if r["id"] == identifier), None)

    @audited("search", many=True)
    def search(self, query: str) -> list[dict]:
        """Literal Unicode-casefolded substring in title, next_step, or body."""
        needle = query.strip().casefold()
        return [r for r in self._visible() if needle and any(
            needle in r[field].casefold() for field in ("title", "next_step", "body"))]

    read_record = get_record

    @audited("graph")
    def graph(self, venture=None):
        from chassis.read_model import neutral_graph
        return neutral_graph(self._visible(), venture)
