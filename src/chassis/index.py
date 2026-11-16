"""Disposable SQLite projection of authoritative working-tree records."""

import json
import sqlite3
from hashlib import sha256
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from tempfile import NamedTemporaryFile

from chassis.markdown import ParsedRecord, RecordFileError, parse_record
from chassis.models import Record
from chassis.validation import load_vault

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
    body TEXT NOT NULL,
    record_json TEXT NOT NULL,
    source_path TEXT NOT NULL UNIQUE,
    mtime_ns INTEGER NOT NULL,
    content_hash TEXT NOT NULL
);
PRAGMA user_version = 1;
"""
FIELDS = ("id", "type", "venture", "status", "parent", "assigned_agent",
          "sensitivity", "title", "next_step")
FILTER_FIELDS = ("type", "venture", "status", "parent", "assigned_agent", "sensitivity")
COLUMNS = FIELDS + ("body", "record_json", "source_path", "mtime_ns", "content_hash")
INSERT = "INSERT OR REPLACE INTO records VALUES (" + ", ".join("?" for _ in COLUMNS) + ")"


class RecordIndex:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.path = self.root / ".chassis" / "index.sqlite"

    def _source_rows(self, cached=None) -> dict[str, tuple]:
        cached, rows = cached or {}, {}

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
                    item = ParsedRecord(path, Record.model_validate_json(old["record_json"]), old["body"])
                    rows[relative] = tuple(old)
                else:
                    item = parse_record(raw.decode("utf-8"), path)
                    rows[relative] = tuple(getattr(item.record, field) for field in FIELDS) + (
                        item.body, item.record.model_dump_json(), relative, *fingerprint)
                return item
            except (OSError, UnicodeError) as exc:
                raise RecordFileError(f"{path}: {exc}") from exc

        load_vault(self.root, reader=read)
        return rows

    def rebuild(self) -> int:
        """Replace the entire cache only after all source records validate."""
        rows = self._source_rows()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=self.path.parent, prefix="index-", suffix=".sqlite",
                                delete=False) as handle:
            temporary = Path(handle.name)
        try:
            with closing(sqlite3.connect(temporary)) as connection, connection:
                connection.executescript(SCHEMA)
                connection.executemany(INSERT, rows.values())
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
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
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            connection.create_function("casefold", 1, str.casefold, deterministic=True)
            self._refresh(connection)
            rows = connection.execute(
                "SELECT record_json, body FROM records " + where + " ORDER BY id",
                parameters).fetchall()
        return [json.loads(row["record_json"]) | {"body": row["body"]} for row in rows]

    def list_records(self, filters: Mapping[str, str | None] | None = None) -> list[dict]:
        """AND exact filters; omitted fields are unrestricted, None matches null."""
        clauses, parameters = [], []
        for field, value in (filters or {}).items():
            if field not in FILTER_FIELDS:
                raise ValueError(f"Unknown filter field: {field}")
            if not isinstance(value, str) and not (
                    value is None and field in {"parent", "assigned_agent"}):
                raise ValueError(f"Invalid filter value for {field}: {value!r}")
            clauses.append(f"{field} IS ?")
            parameters.append(value)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return self._query(where, tuple(parameters))

    def get_record(self, identifier: str) -> dict | None:
        results = self._query("WHERE id = ?", (identifier,))
        return results[0] if results else None

    def search(self, query: str) -> list[dict]:
        """Literal Unicode-casefolded substring in title, next_step, or body."""
        needle = query.strip().casefold()
        if not needle:
            return self._query("WHERE 0")
        return self._query("WHERE instr(casefold(title), ?) > 0 "
                           "OR instr(casefold(next_step), ?) > 0 "
                           "OR instr(casefold(body), ?) > 0", (needle,) * 3)
