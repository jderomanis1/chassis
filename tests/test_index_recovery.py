import json
import os
import shutil
import sqlite3
from contextlib import closing
from hashlib import sha256

import pytest

from chassis.index import RecordIndex
from chassis.markdown import RecordFileError


@pytest.mark.parametrize("operation,args", [("list_records", ()),
    ("get_record", ("task-launch-budget",)), ("search", ("maintenance",))])
@pytest.mark.parametrize("damage", ["missing", "garbage", "truncated", "schema", "version", "payload"])
def test_reads_rebuild_missing_or_corrupt_cache(vault, operation, args, damage):
    index = RecordIndex(vault)
    index.rebuild()
    expected = getattr(index, operation)(*args)
    if damage == "missing":
        shutil.rmtree(index.path.parent)
    elif damage == "garbage":
        index.path.write_bytes(b"not a SQLite database")
    elif damage == "truncated":
        index.path.write_bytes(index.path.read_bytes()[:100])
    else:
        sql = {"schema": "DROP TABLE records", "version": "PRAGMA user_version = 99",
               "payload": "UPDATE records SET record_json = '{broken json'"}[damage]
        with closing(sqlite3.connect(index.path)) as connection, connection:
            connection.execute(sql)
    assert getattr(index, operation)(*args) == expected
    assert index.path.is_file()
    with closing(sqlite3.connect(index.path)) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA user_version").fetchone() == (2,)


def test_bad_source_is_not_hidden_by_cache_recovery(vault):
    index = RecordIndex(vault)
    index.rebuild()
    index.path.write_bytes(b"broken cache")
    (vault / "records/tasks/broken.md").write_text("invalid record", encoding="utf-8")
    with pytest.raises(RecordFileError, match="broken.md:.*opening YAML frontmatter fence"):
        index.list_records()
    assert index.path.read_bytes() == b"broken cache"


@pytest.mark.parametrize("method", ["rebuild", "list_records"])
def test_generated_cache_does_not_follow_symlink_outside_vault(vault, tmp_path, method):
    outside = tmp_path / "outside-cache"
    outside.mkdir()
    (vault / ".chassis").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match=".chassis.*symlink"):
        getattr(RecordIndex(vault), method)()
    assert list(outside.iterdir()) == []


def test_locked_cache_is_reported_not_replaced(vault, monkeypatch):
    index = RecordIndex(vault)
    index.rebuild()
    connect = sqlite3.connect
    monkeypatch.setattr(sqlite3, "connect", lambda path: connect(path, timeout=0))
    monkeypatch.setattr(index, "rebuild", lambda: pytest.fail("Must not rebuild a locked cache"))
    with closing(connect(index.path)) as connection:
        connection.execute("BEGIN EXCLUSIVE")
        with pytest.raises(ValueError, match="index.sqlite.*locked"):
            index.list_records()


@pytest.mark.parametrize("damage", ["body", "filter-column", "valid-json", "missing-sensitivity"])
def test_structurally_valid_cache_with_damaged_values_recovers_from_source(vault, damage):
    index = RecordIndex(vault)
    original = index.get_record("task-launch-budget")
    column, value = "body", "Damaged cached body."
    if damage == "filter-column":
        column, value = "sensitivity", "normal"
    elif damage in {"valid-json", "missing-sensitivity"}:
        record = {key: value for key, value in original.items() if key != "body"}
        if damage == "valid-json":
            record["title"] = "Damaged cached title"
        else:
            del record["sensitivity"]
        column, value = "record_json", json.dumps(record)
    with closing(sqlite3.connect(index.path)) as connection, connection:
        connection.execute(f"UPDATE records SET {column} = ? WHERE id = ?",
                           (value, "task-launch-budget"))
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert index.get_record("task-launch-budget") == original
    assert index.list_records({"sensitivity": "restricted"}) == [original]


def test_mtime_only_change_updates_the_stored_fingerprint(vault):
    index = RecordIndex(vault)
    original = index.get_record("task-launch-budget")
    path = vault / "records/tasks/task-launch-budget.md"
    previous = path.stat()
    os.utime(path, ns=(previous.st_atime_ns, previous.st_mtime_ns + 10_000_000))
    assert index.get_record("task-launch-budget") == original
    with closing(sqlite3.connect(index.path)) as connection:
        fingerprint = connection.execute(
            "SELECT mtime_ns, content_hash FROM records WHERE id = ?", (original["id"],)).fetchone()
    assert fingerprint == (path.stat().st_mtime_ns, sha256(path.read_bytes()).hexdigest())
