from datetime import date, datetime, timezone

import pytest
from conftest import git
from pydantic import ValidationError

from chassis.markdown import read_record, serialize_record
from chassis.models import Record
from chassis.store import RecordStore

PORTAL_FIELDS = {"next_milestone", "milestone_due_at", "due_at", "blocker_reason"}


def fields(root, kind="task"):
    name = {"task": "task-launch-budget", "initiative": "initiative-d2c-launch",
            "venture": "venture-acme"}[kind]
    return read_record(root / "records" / f"{kind}s" / f"{name}.md").record.model_dump()


@pytest.mark.parametrize("kind", ["venture", "initiative", "task", "agent"])
def test_legacy_records_without_portal_fields_still_validate(vault, kind):
    values = fields(vault, "initiative" if kind == "agent" else kind)
    values["type"] = kind
    for key in PORTAL_FIELDS:
        values.pop(key, None)
    record = Record.model_validate(values)
    assert all(getattr(record, key) is None for key in PORTAL_FIELDS)


@pytest.mark.parametrize("kind", ["venture", "initiative"])
def test_milestone_fields_accept_iso_dates_and_roundtrip(vault, kind):
    record = Record.model_validate(fields(vault, kind) | {
        "next_milestone": "Fictional pilot review", "milestone_due_at": "2026-12-01"})
    assert record.milestone_due_at == date(2026, 12, 1)
    assert record.model_dump(mode="json")["milestone_due_at"] == "2026-12-01"
    assert b"last_activity_at" not in serialize_record(record, "Fictional body.\n")


@pytest.mark.parametrize("key,kind", [("milestone_due_at", "venture"), ("due_at", "task")])
@pytest.mark.parametrize("value", ["20261201", "2026-02-30", "12/01/2026", 1796083200,
                                  True, "2026-12-01T00:00:00Z",
                                  datetime(2026, 12, 1, tzinfo=timezone.utc)])
def test_dates_reject_coercion_and_non_date_values(vault, key, kind, value):
    with pytest.raises(ValidationError, match=key):
        Record.model_validate(fields(vault, kind) | {key: value})


@pytest.mark.parametrize("kind,extra,key", [
    ("task", {"next_milestone": "Fictional review"}, "next_milestone"),
    ("task", {"milestone_due_at": "2026-12-01"}, "milestone_due_at"),
    ("venture", {"due_at": "2026-12-01"}, "due_at"),
    ("initiative", {"blocker_reason": "Waiting for sample input"}, "blocker_reason"),
    ("task", {"last_activity_at": "2026-12-01T00:00:00Z"}, "last_activity_at"),
])
def test_portal_fields_have_type_scope_and_activity_cannot_be_stored(vault, kind, extra, key):
    with pytest.raises(ValidationError, match=key):
        Record.model_validate(fields(vault, kind) | extra)


@pytest.mark.parametrize("value", [None, "", " \t", 123])
def test_blocked_task_requires_nonempty_reason(vault, value):
    with pytest.raises(ValidationError, match="blocker_reason"):
        Record.model_validate(fields(vault) | {"status": "blocked", "blocker_reason": value})


@pytest.mark.parametrize("status", ["planned", "in_progress", "done"])
def test_unblocked_task_rejects_stale_blocker_reason(vault, status):
    with pytest.raises(ValidationError, match="blocker_reason"):
        Record.model_validate(fields(vault) | {"status": status, "blocker_reason": "Old blocker"})
    for empty in (None, "", "  "):
        Record.model_validate(fields(vault) | {"status": status, "blocker_reason": empty})


def test_blocking_and_unblocking_validate_the_combined_proposal(git_repo):
    store = RecordStore(git_repo)
    before = git(git_repo, "rev-parse", "HEAD")
    path = git_repo / "records/tasks/task-launch-budget.md"
    original = path.read_bytes()
    with pytest.raises(ValidationError, match="blocker_reason"):
        store.update_record("task-launch-budget", {"status": "blocked"}, 1, "chief-of-staff")
    assert path.read_bytes() == original and git(git_repo, "rev-parse", "HEAD") == before
    result = store.update_record("task-launch-budget", {
        "status": "blocked", "blocker_reason": "Waiting for fictional approval",
        "due_at": "2026-12-01"}, 1, "chief-of-staff")
    assert result["record"]["due_at"] == "2026-12-01"
    with pytest.raises(ValidationError, match="blocker_reason"):
        store.update_record("task-launch-budget", {"status": "done"}, 2, "chief-of-staff")
    assert git(git_repo, "rev-parse", "HEAD") == result["commit"]
    done = store.update_record("task-launch-budget", {"status": "done", "blocker_reason": None},
                               2, "chief-of-staff")
    assert done["record"]["blocker_reason"] is None
