"""Disposable SQLite projection of authoritative working-tree records."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import NamedTemporaryFile

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
    record_json TEXT NOT NULL
);
PRAGMA user_version = 1;
"""
FIELDS = ("id", "type", "venture", "status", "parent", "assigned_agent",
          "sensitivity", "title", "next_step")


class RecordIndex:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.path = self.root / ".chassis" / "index.sqlite"

    def rebuild(self) -> int:
        """Replace the entire cache only after all source records validate."""
        records = load_vault(self.root)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=self.path.parent, prefix="index-", suffix=".sqlite",
                                delete=False) as handle:
            temporary = Path(handle.name)
        try:
            with closing(sqlite3.connect(temporary)) as connection, connection:
                connection.executescript(SCHEMA)
                connection.executemany(
                    "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [tuple(getattr(item.record, field) for field in FIELDS)
                     + (item.body, item.record.model_dump_json())
                     for item in records.values()])
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return len(records)

    def _query(self, where: str = "", parameters: tuple = ()) -> list[dict]:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT record_json, body FROM records " + where + " ORDER BY id",
                parameters).fetchall()
        return [json.loads(row["record_json"]) | {"body": row["body"]} for row in rows]

    def list_records(self) -> list[dict]:
        """Return complete JSON-compatible records in ascending ID order."""
        return self._query()

    def get_record(self, identifier: str) -> dict | None:
        results = self._query("WHERE id = ?", (identifier,))
        return results[0] if results else None
