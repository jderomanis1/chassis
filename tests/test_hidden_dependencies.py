"""Stored hidden dependencies survive edits the caller is allowed to make."""
import json

from conftest import git
from chassis.errors import WriteError
from chassis.index import RecordIndex
from chassis.markdown import read_record
from chassis.store import RecordStore
from chassis.tool_handlers import ToolHandlers
from test_read_error_safety import normal_writer
from test_templates import initiative_fields

HIDDEN = "task-launch-budget"
TARGET = "task-launch-offer"
VISIBLE = "task-audience-interviews"
AGENT = "normal-writer"


def plant(root, dependencies, task=TARGET):
    path = root / "records/tasks" / f"{task}.md"
    text = path.read_text().replace("depends_on: []", "depends_on: [" + ", ".join(dependencies) + "]")
    assert text != path.read_text()
    path.write_text(text)
    git(root, "add", f"records/tasks/{task}.md")
    git(root, "commit", "-qm", "Plant fictional dependency")
    return path


def open_writer(root, monkeypatch):
    token = normal_writer(root)
    monkeypatch.setenv("CHASSIS_AGENT_ID", AGENT)
    monkeypatch.setenv("CHASSIS_AGENT_TOKEN", token)
    return RecordStore(root, token=token), ToolHandlers(root, AGENT, token=token)


def test_title_update_leaves_a_stored_hidden_dependency(git_repo, monkeypatch):
    path = plant(git_repo, [HIDDEN])
    store, handlers = open_writer(git_repo, monkeypatch)
    result = store.update_record(TARGET, {"title": "Fictional title only"}, 1, AGENT)
    assert result["record"]["title"] == "Fictional title only"
    assert result["record"]["depends_on"] == []
    assert HIDDEN not in json.dumps(result)
    assert read_record(path).record.depends_on == [HIDDEN]
    assert RecordIndex(git_repo, agent=AGENT, token=store.token).get_record(TARGET)["depends_on"] == []
    follow = handlers.call("update_record", {"id": TARGET, "expected_version": 2, "changes": {
        "next_step": "Keep the fictional hidden link."}})
    assert follow["record"]["depends_on"] == []
    assert HIDDEN not in json.dumps(follow)
    assert read_record(path).record.depends_on == [HIDDEN]
    read = handlers.call("read_record", {"id": TARGET})
    assert read["record"]["depends_on"] == []
    assert HIDDEN not in json.dumps(read)


def test_visible_dependency_list_keeps_hidden_ids_through_link_and_undo(git_repo, monkeypatch):
    path = plant(git_repo, [VISIBLE, HIDDEN])
    store, handlers = open_writer(git_repo, monkeypatch)
    linked = handlers.call("update_record", {"id": TARGET, "expected_version": 1, "changes": {
        "depends_on": [VISIBLE, "task-resident-faq"]}})
    assert linked["record"]["depends_on"] == [VISIBLE, "task-resident-faq"]
    assert HIDDEN not in json.dumps(linked)
    assert read_record(path).record.depends_on == [VISIBLE, "task-resident-faq", HIDDEN]
    undone = store.update_record(TARGET, {"depends_on": [VISIBLE]}, 2, AGENT)
    assert undone["record"]["depends_on"] == [VISIBLE]
    assert HIDDEN not in json.dumps(undone)
    assert read_record(path).record.depends_on == [VISIBLE, HIDDEN]
    cleared = store.update_record(TARGET, {"depends_on": []}, 3, AGENT)
    assert cleared["record"]["depends_on"] == []
    assert read_record(path).record.depends_on == [HIDDEN]


def test_new_hidden_and_missing_dependencies_stay_indistinguishable(git_repo, monkeypatch):
    path = plant(git_repo, [HIDDEN])
    other = git_repo / "records/tasks/task-resident-faq.md"
    other.write_text(other.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    store, handlers = open_writer(git_repo, monkeypatch)
    original, head = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")

    def refuse(dependency):
        changes = {"depends_on": [dependency]}
        try:
            store.update_record(TARGET, changes, 1, AGENT)
        except WriteError as exc:
            library = exc
        else:
            raise AssertionError("library update wrote a new hidden dependency")
        mcp = handlers.call("update_record", {"id": TARGET, "expected_version": 1, "changes": changes})
        return library, mcp

    hidden_error, hidden_mcp = refuse("task-resident-faq")
    missing_error, missing_mcp = refuse("task-missing")
    assert str(hidden_error) == str(missing_error) == "invalid dependency"
    assert hidden_error.as_dict() == missing_error.as_dict() == {
        "error": "write_refused", "message": "invalid dependency"}
    assert hidden_mcp == missing_mcp
    assert hidden_mcp["error"] == "validation" and hidden_mcp["reason"] == "invalid dependency"
    blob = json.dumps([hidden_error.as_dict(), hidden_mcp, missing_mcp])
    for term in (HIDDEN, "task-resident-faq", "task-missing"):
        assert term not in blob
    assert path.read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == head
    assert read_record(path).record.depends_on == [HIDDEN]


def test_template_create_rejects_new_hidden_and_missing_dependencies_alike(template_repo, monkeypatch):
    token = normal_writer(template_repo)
    monkeypatch.setenv("CHASSIS_AGENT_ID", AGENT)
    monkeypatch.setenv("CHASSIS_AGENT_TOKEN", token)
    store = RecordStore(template_repo, token=token)
    head = git(template_repo, "rev-parse", "HEAD")

    def refuse(depends, identifier):
        fields = initiative_fields() | {"id": identifier, "depends_on": depends}
        try:
            store.create_from_template("initiative", "venture-acme", fields, AGENT)
        except WriteError as exc:
            return exc
        raise AssertionError("template create wrote a hidden dependency")

    hidden, missing = refuse([HIDDEN], "initiative-hidden-probe"), refuse(["task-missing"], "initiative-missing-probe")
    assert str(hidden) == str(missing) == "invalid dependency"
    assert hidden.as_dict() == missing.as_dict()
    assert HIDDEN not in json.dumps(hidden.as_dict())
    assert "task-missing" not in json.dumps(missing.as_dict())
    assert git(template_repo, "rev-parse", "HEAD") == head
    assert not (template_repo / "records/initiatives/initiative-hidden-probe.md").exists()
    assert not (template_repo / "records/initiatives/initiative-missing-probe.md").exists()
