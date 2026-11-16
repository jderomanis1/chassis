import json
import os
import sqlite3
from datetime import datetime, timezone

import pytest
from conftest import git

from chassis.index import RecordIndex
from chassis.markdown import read_record, serialize_record
from chassis.models import Record
from chassis.store import RecordStore
from test_index_cli import cli

TARGET = "records/tasks/task-launch-budget.md"


def commit_time(root):
    return datetime.fromisoformat(git(root, "show", "-s", "--format=%cI")).astimezone(timezone.utc).isoformat()


@pytest.mark.parametrize("initialized", [False, True])
def test_records_without_commit_history_have_null_activity(vault, initialized):
    if initialized:
        git(vault, "init", "-q")
    index = RecordIndex(vault)
    records = index.list_records()
    assert all(record["last_activity_at"] is None for record in records)
    assert index.list_records({"last_activity_at": None}) == records


def test_activity_tracks_agent_and_human_commits_and_ignores_uncommitted_edits(git_repo):
    index, store = RecordIndex(git_repo), RecordStore(git_repo)
    initial = index.get_record("task-launch-budget")
    assert initial["last_activity_at"] == commit_time(git_repo)
    result = store.update_record("task-launch-budget", {"due_at": "2026-12-01"}, 1, "chief-of-staff")
    assert result["record"] == index.get_record("task-launch-budget")
    assert result["record"]["last_activity_at"] == commit_time(git_repo)
    path = git_repo / TARGET
    path.write_text(path.read_text() + "\nFictional manual activity.\n")
    before = index.get_record("task-launch-budget")
    assert before["last_activity_at"] == result["record"]["last_activity_at"]
    store.commit_human(TARGET)
    after = index.get_record("task-launch-budget")
    assert after["last_activity_at"] == commit_time(git_repo)
    assert after["updated_at"] == before["updated_at"]
    assert b"last_activity_at" not in path.read_bytes()


def test_history_refreshes_even_when_source_bytes_and_mtime_are_identical(git_repo, monkeypatch):
    index = RecordIndex(git_repo)
    original = index.get_record("task-launch-budget")
    path = git_repo / TARGET
    raw, stat = path.read_bytes(), path.stat()
    path.write_bytes(raw + b"\nFictional manual note.\n")
    git(git_repo, "commit", "--only", "-qm", "Fictional human edit", "--", TARGET)
    path.write_bytes(raw)
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2030-01-02T12:00:00Z")
    git(git_repo, "commit", "--only", "-qm", "Fictional human restore", "--", TARGET)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    expected = original | {"last_activity_at": "2030-01-02T12:00:00+00:00"}
    assert index.get_record("task-launch-budget") == expected
    (git_repo / "unrelated.txt").write_text("Fictional unrelated activity.\n")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2030-01-03T12:00:00Z")
    git(git_repo, "add", "unrelated.txt")
    git(git_repo, "commit", "-qm", "Fictional unrelated commit")
    assert index.get_record("task-launch-budget") == expected
    index.path.unlink()
    assert index.get_record("task-launch-budget") == expected


@pytest.mark.parametrize("identifier,kind,changes", [
    ("venture-acme", "venture", {"next_milestone": "Fictional review", "milestone_due_at": "2026-12-01"}),
    ("task-launch-budget", "task", {"due_at": "2026-11-30"}),
    ("task-launch-budget", "task", {"status": "blocked", "blocker_reason": "Fictional review pending"}),
])
def test_new_fields_roundtrip_and_filter_in_library_and_cli(vault, identifier, kind, changes):
    path = vault / "records" / f"{kind}s" / f"{identifier}.md"
    item = read_record(path)
    path.write_bytes(serialize_record(Record.model_validate(item.record.model_dump() | changes), item.body))
    index = RecordIndex(vault)
    record = index.get_record(identifier)
    for key, value in changes.items():
        assert record[key] == value
        assert [r["id"] for r in index.list_records({key: value, "type": kind, "venture": "venture-acme"})] == [identifier]
        result = cli(vault, "list", "--" + key.replace("_", "-"), value, "--type", kind, "--venture", "venture-acme")
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == [record]
    expected = ["venture-acme", "venture-ridgeview"]
    assert [r["id"] for r in index.list_records({"due_at": None, "type": "venture"})] == expected
    assert [r["id"] for r in json.loads(cli(vault, "list", "--due-at", "null", "--type", "venture").stdout)] == expected


def test_old_cache_schema_and_corrupted_activity_are_rebuilt(git_repo):
    index = RecordIndex(git_repo)
    expected = index.list_records()
    for damage in ("PRAGMA user_version = 2", "UPDATE records SET last_activity_at = 'corrupt'"):
        with sqlite3.connect(index.path) as connection:
            connection.execute(damage)
        assert index.list_records() == expected
