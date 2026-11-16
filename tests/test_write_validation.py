import pytest

from chassis.markdown import ParsedRecord, RecordFileError, parse_record, serialize_record
from chassis.models import Record
from chassis.policy import load_policy
from chassis.validation import read_vault, validate_records


@pytest.mark.parametrize("body", ["\r\n# Fictional café\r\n\r\nNotes  \r\n", "No final newline", ""])
def test_serialization_preserves_body_and_round_trips_record(vault, body):
    original = next(item for item in read_vault(vault) if item.record.id == "task-launch-budget")
    encoded = serialize_record(original.record, body)
    parsed = parse_record(encoded.decode("utf-8"), original.path)
    assert parsed.record == original.record
    assert parsed.body.encode("utf-8") == body.encode("utf-8")


def test_validate_proposed_graph_detects_cycle_through_new_record(vault):
    items = read_vault(vault)
    original = next(item for item in items if item.record.id == "task-launch-budget")
    fields = original.record.model_dump()
    fields["depends_on"] = ["task-new"]
    changed = ParsedRecord(original.path, Record.model_validate(fields), original.body)
    fields.update(id="task-new", depends_on=[original.record.id])
    created = ParsedRecord(vault / "records/tasks/task-new.md", Record.model_validate(fields), "")
    proposed = [changed if item == original else item for item in items] + [created]
    with pytest.raises(RecordFileError, match="dependency cycle"):
        validate_records(vault, proposed, load_policy(vault))


def test_proposed_assignment_requires_a_known_agent(vault):
    items = read_vault(vault)
    original = items[0]
    fields = original.record.model_dump() | {"assigned_agent": "unknown-agent"}
    items[0] = ParsedRecord(original.path, Record.model_validate(fields), original.body)
    with pytest.raises(RecordFileError, match="assigned_agent.*unknown-agent.*known agent"):
        validate_records(vault, items, load_policy(vault))
