import shutil
import sqlite3
from contextlib import closing

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
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)


def test_bad_source_is_not_hidden_by_cache_recovery(vault):
    index = RecordIndex(vault)
    index.rebuild()
    index.path.write_bytes(b"broken cache")
    (vault / "records/tasks/broken.md").write_text("invalid record", encoding="utf-8")
    with pytest.raises(RecordFileError, match="broken.md:.*opening YAML frontmatter fence"):
        index.list_records()


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
