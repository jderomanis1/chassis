import pytest
from conftest import git

from chassis.index import RecordIndex
from chassis.tool_handlers import TOOL_INPUTS, ToolHandlers
from test_creates import new_task


def test_handler_contract_has_exact_tools_and_no_caller_identity(git_repo):
    assert sorted(TOOL_INPUTS) == ["create_from_template", "create_record", "list_records",
                                    "read_record", "search", "update_record"]
    for model in TOOL_INPUTS.values():
        schema = model.model_json_schema()
        assert schema["additionalProperties"] is False
        assert not {"agent", "agent_id", "agent_name", "agent_email"}.intersection(schema["properties"])
    handler = ToolHandlers(git_repo, "chief-of-staff")
    assert handler.call("list_records", {"filters": {"type": "venture"}}) == {
        "records": RecordIndex(git_repo).list_records({"type": "venture"})}
    assert handler.call("read_record", {"id": "venture-acme"}) == {
        "record": RecordIndex(git_repo).get_record("venture-acme")}


@pytest.mark.parametrize("name,args,field", [
    ("update_record", {"id": "task-launch-budget", "changes": {}, "expected_version": True}, "expected_version"),
    ("update_record", {"id": "task-launch-budget", "changes": {"status": "unknown"}, "expected_version": 1}, "status"),
    ("read_record", {"id": "../outside"}, "id"),
    ("list_records", {"filters": {"due_at": 12}}, "filters.due_at"),
    ("search", {"query": "sample", "agent": "chief-of-staff"}, "agent"),
])
def test_validation_errors_have_field_and_reason_without_writes(git_repo, name, args, field):
    before = git(git_repo, "rev-parse", "HEAD")
    result = ToolHandlers(git_repo, "chief-of-staff").call(name, args)
    assert result["error"] == "validation" and result["field"] == field
    assert result["reason"] and "Traceback" not in str(result)
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert git(git_repo, "status", "--porcelain") == ""


def test_not_found_and_unauthorized_are_structured(git_repo):
    handler = ToolHandlers(git_repo, "unknown-agent")
    assert handler.call("read_record", {"id": "missing-id"})["error"] == "not_found"
    result = handler.call("create_record", {"type": "task", "fields": new_task(git_repo)})
    assert result["error"] == "unauthorized"
    assert result["agent"] == "unknown-agent"


def test_unexpected_exception_is_logged_but_never_returned(git_repo, monkeypatch, caplog):
    def fail(*_):
        raise RuntimeError("private diagnostic detail")
    monkeypatch.setattr(RecordIndex, "search", fail)
    result = ToolHandlers(git_repo, "chief-of-staff").call("search", {"query": "sample"})
    assert result["error"] == "internal_error"
    assert "private diagnostic detail" not in str(result)
    assert "Traceback" not in str(result)
    assert "private diagnostic detail" in caplog.text
