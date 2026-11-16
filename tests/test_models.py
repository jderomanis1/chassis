from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from chassis.models import Record


@pytest.fixture
def fields():
    return dict(id="venture-ridgeview", type="venture", title="Ridgeview HOA",
                status="planned", owner="Morgan Vale", venture="venture-ridgeview",
                parent=None, next_step="Confirm the fictional maintenance scope.",
                updated_at="2026-11-16T12:00:00Z", version=1)


def test_valid_record_has_safe_defaults(fields):
    record = Record.model_validate(fields)
    assert record.sensitivity == "normal"
    assert record.assigned_agent is None
    assert record.depends_on == []
    assert record.updated_at == datetime(2026, 11, 16, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize("key", ["id", "type", "title", "status", "owner", "venture",
                                "parent", "next_step", "updated_at", "version"])
def test_every_required_field_is_required(fields, key):
    del fields[key]
    with pytest.raises(ValidationError):
        Record.model_validate(fields)


@pytest.mark.parametrize(("key", "value"), [
    ("id", "../escape"), ("id", "Title With Spaces"), ("type", "agent"),
    ("title", "  "), ("owner", ""), ("next_step", ""), ("status", "unknown"),
    ("version", 0), ("version", True), ("version", 1.0), ("version", "1"),
    ("updated_at", "2026-11-16T12:00:00"), ("updated_at", 1794830400),
    ("updated_at", "1794830400"), ("updated_at", "20261116"),
    ("updated_at", "1794830400.5"), ("updated_at", "+1794830400"),
    ("sensitivity", "secret"), ("assigned_agent", "../agent"),
    ("depends_on", "task-one"), ("depends_on", ["task-one", "task-one"]),
    ("unexpected", "not allowed"),
])
def test_malformed_values_are_rejected(fields, key, value):
    with pytest.raises(ValidationError):
        Record.model_validate(fields | {key: value})


def test_restricted_and_assigned_agent_are_supported(fields):
    record = Record.model_validate(fields | {"sensitivity": "restricted",
                                             "assigned_agent": "chief-of-staff"})
    assert record.sensitivity == "restricted"
    assert record.assigned_agent == "chief-of-staff"
