import json
from dataclasses import replace

import pytest
import yaml

from chassis.errors import AuditError, CommittedIndexError
from chassis.git import Identity
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig
from chassis.markdown import read_record
from chassis.portal.writes import CONFLICT_MESSAGE
from chassis.store import RecordStore
from starlette.testclient import TestClient
from test_security_cli import assert_no_leaks, restricted_terms
from .helpers import git, issue
from .test_write_guard import editor_config, writer

TARGET = "/api/records/task-launch-offer"


def patch(writer, changes=None, version=1, path=TARGET):
    return writer.patch(path, json={"changes": changes or {"title": "Fictional canvas edit"},
                                    "expected_version": version})


def test_restricted_editor_history_is_invisible_to_a_normal_viewer(writer, editor_config, monkeypatch):
    root = editor_config.root
    saved = patch(writer, {"title": "Visible fictional title"})
    assert saved.status_code == 200
    before = writer.get("/api/undo")
    version = writer.get("/api/version").json()["etag"]
    assert before.status_code == 200
    assert before.json()["count"] == len(before.json()["entries"]) == 1
    chief = issue(root, "chief-of-staff")
    monkeypatch.setenv("CHASSIS_AGENT_ID", "chief-of-staff")
    monkeypatch.setenv("CHASSIS_AGENT_TOKEN", chief)
    RecordStore(root, token=chief, identity=Identity("canvas-editor", "canvas-editor@chassis.local")).update_record(
        "task-launch-budget", {"title": "Hidden undo title"}, 1, "chief-of-staff")
    after = writer.get("/api/undo")
    assert after.content == before.content
    assert after.json()["count"] == before.json()["count"]
    assert after.json()["etag"] == before.json()["etag"]
    assert writer.get("/api/version").json()["etag"] == version
    for term in (b"task-launch-budget", b"Hidden undo title", b"Set the internal launch test budget"):
        assert term not in after.content
    cleared = PortalConfig(root=root, viewer_agent="chief-of-staff", viewer_token=chief,
                           editor_agent="canvas-editor", editor_token=editor_config.editor_token)
    with TestClient(create_app(cleared), base_url="http://127.0.0.1:8765") as client:
        seen = client.get("/api/undo")
        assert seen.status_code == 200
        body = seen.json()
        assert body["count"] == before.json()["count"] + 1
        assert any(entry["id"] == "task-launch-budget" for entry in body["entries"])
        assert "Set the internal launch test budget" in seen.text
        assert body["etag"] != before.json()["etag"]


def test_undo_after_a_reload_is_a_second_editor_commit(writer, editor_config):
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    saved = patch(writer, {"title": "Fictional title to undo"})
    assert saved.status_code == 200
    stacked = writer.get("/api/undo").json()["entries"]
    assert stacked[-1]["id"] == "task-launch-offer"
    assert stacked[-1]["changes"] == {"title": "Draft the starter-kit offer"}
    assert stacked[-1]["version"] == 2
    undone = patch(writer, stacked[-1]["changes"], stacked[-1]["version"])
    assert undone.status_code == 200
    assert "Draft the starter-kit offer" in (root / "records/tasks/task-launch-offer.md").read_text()
    assert git(root, "rev-parse", "HEAD^") == saved.json()["commit"]
    assert git(root, "rev-list", "--count", f"{before}..HEAD") == "2"
    assert writer.get("/api/undo").json()["entries"] == []


def test_canvas_uses_library_one_record_commit_editor_author_and_etag(writer, editor_config, monkeypatch):
    root = editor_config.root
    before, etag = git(root, "rev-parse", "HEAD"), writer.get("/api/version").json()["etag"]
    calls, original = [], RecordStore.update_record
    def observe(store, *args, **kwargs):
        calls.append((args, kwargs))
        return original(store, *args, **kwargs)
    monkeypatch.setattr(RecordStore, "update_record", observe)
    response = patch(writer)
    assert response.status_code == 200
    data = response.json()
    assert data["record"] == {"id": "task-launch-offer", "version": 2}
    assert data["commit"] == git(root, "rev-parse", "HEAD")
    assert git(root, "rev-list", "--count", f"{before}..HEAD") == "1"
    assert git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD") == "records/tasks/task-launch-offer.md"
    assert git(root, "log", "-1", "--format=%an <%ae>") == "canvas-editor <canvas-editor@chassis.local>"
    assert len(calls) == 1 and calls[0][0] == ("task-launch-offer", {"title": "Fictional canvas edit"}, 1, "canvas-editor")
    assert writer.get("/api/version").json()["etag"] != etag
    events = [json.loads(line) for line in (root / ".chassis/audit.jsonl").read_text().splitlines()]
    assert any(e["tool"] == "update_record" and e["outcome"] == "ok" and e["agent_id"] == "canvas-editor" for e in events)


def test_conflict_keeps_bytes_and_history_and_exposes_only_current_version(writer, editor_config):
    assert patch(writer).status_code == 200
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    path = root / "records/tasks/task-launch-offer.md"
    old = path.read_bytes()
    response = patch(writer, {"title": "Must not overwrite"})
    assert response.status_code == 409
    assert response.json() == {"error": {"code": "conflict", "message": CONFLICT_MESSAGE, "current_version": 2}}
    assert path.read_bytes() == old and git(root, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("changes", [{"agent": "chief-of-staff"}, {"body": "No canvas body writes"},
    {"owner": "Another author"}, {"sensitivity": "normal"}, {"depends_on": "task-launch-offer"},
    {"version": 2}, {"title": "x" * 241}, {"next_step": "x" * 4097},
    {"blocker_reason": "x" * 4097}, {"title": None}, {"status": "invalid"},
    {"due_at": "2026-02-30"}, {"status": "blocked"}, {}])
def test_schema_and_library_validation_refuse_without_commit(writer, editor_config, changes):
    before = git(editor_config.root, "rev-parse", "HEAD")
    response = writer.patch(TARGET, json={"changes": changes, "expected_version": 1})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation"
    assert git(editor_config.root, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("payload", [b"{", b"[]", b"null", b'{"changes":{},"expected_version":true}',
    b'{"changes":{"title":"ok"},"expected_version":1,"agent":"chief-of-staff"}'])
def test_invalid_payload_is_generic_validation(writer, payload):
    response = writer.patch(TARGET, content=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation"


@pytest.mark.parametrize("identifier", ["INVALID!", "a" * 81, "%2E%2E%2Fagents", "records%2Ftasks%2Ftask-launch-offer"])
def test_path_traversal_and_invalid_id_never_reach_library(writer, identifier, monkeypatch):
    monkeypatch.setattr(RecordStore, "update_record", lambda *a, **k: pytest.fail("unsafe id reached library"))
    assert patch(writer, path=f"/api/records/{identifier}").status_code == 400


def test_hidden_missing_ungranted_and_hidden_parent_have_same_error(writer, editor_config):
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    for identifier in ["task-launch-budget", "task-missing"]:
        response = patch(writer, path=f"/api/records/{identifier}")
        assert response.status_code == 404
        assert response.json() == {"error": {"code": "not_found", "message": "Not found"}}
        assert_no_leaks([response.text], restricted_terms(root))
    policy_path = root / "agents.yaml"
    policy = yaml.safe_load(policy_path.read_text())
    policy["agents"]["canvas-editor"]["ventures"]["venture-acme"]["task"] = "read"
    policy_path.write_text(yaml.safe_dump(policy))
    assert patch(writer).json() == {"error": {"code": "not_found", "message": "Not found"}}
    parent = root / "records/initiatives/initiative-d2c-launch.md"
    parent.write_text(parent.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    assert patch(writer).status_code == 404
    assert git(root, "rev-parse", "HEAD") == before


def test_dirty_refusal_and_existing_record_body_cap(writer, editor_config):
    root = editor_config.root
    target = root / "records/tasks/task-launch-offer.md"
    before = git(root, "rev-parse", "HEAD")
    target.write_text(target.read_text() + "Human note.\n")
    response = patch(writer)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "dirty_record"
    assert "uncommitted human edit" in response.json()["error"]["message"]
    target.write_text(target.read_text() + "x" * 65537)
    assert patch(writer).status_code == 400
    assert git(root, "rev-parse", "HEAD") == before


def test_middleware_audit_failure_after_commit_keeps_recovery(writer, editor_config, monkeypatch):
    from chassis.portal import app as portal_app
    real = portal_app.record_event

    def fail_after_commit(root, agent, tool, outcome, **kwargs):
        if tool == "portal_write" and outcome == "ok":
            raise AuditError("Audit unavailable")
        return real(root, agent, tool, outcome, **kwargs)

    monkeypatch.setattr(portal_app, "record_event", fail_after_commit)
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    response = patch(writer, {"title": "Committed before the audit append failed"})
    commit = git(root, "rev-parse", "HEAD")
    assert commit != before
    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "audit_error", "message": "Audit unavailable", "committed": True,
        "commit": commit, "current_version": 2}
    assert "Committed before the audit append failed" in (root / "records/tasks/task-launch-offer.md").read_text()


def plant_hidden(root, dependencies):
    path = root / "records/tasks/task-launch-offer.md"
    text = path.read_text().replace("depends_on: []", "depends_on: [" + ", ".join(dependencies) + "]")
    path.write_text(text)
    git(root, "add", "records/tasks/task-launch-offer.md")
    git(root, "commit", "-qm", "Plant fictional dependency")
    return path


def offer_dependencies(writer):
    tasks = writer.get("/api/initiatives/initiative-d2c-launch").json()["tasks"]
    return next(task for task in tasks if task["id"] == "task-launch-offer")["depends_on"]


def test_portal_title_edit_drops_a_deleted_hidden_dependency(writer, editor_config):
    root = editor_config.root
    path = plant_hidden(root, ["task-launch-budget"])
    (root / "records/tasks/task-launch-budget.md").unlink()
    response = patch(writer, {"title": "Fictional title after a removed link"})
    assert response.status_code == 200, response.text
    assert "Records unavailable" not in response.text
    assert response.json()["record"]["version"] == 2
    assert read_record(path).record.title == "Fictional title after a removed link"
    assert read_record(path).record.depends_on == []
    assert "task-launch-budget" not in response.text


def test_title_patch_leaves_a_stored_hidden_dependency(writer, editor_config):
    root = editor_config.root
    path = plant_hidden(root, ["task-launch-budget"])
    response = patch(writer, {"title": "Fictional title only"})
    assert response.status_code == 200
    assert "task-launch-budget" not in response.text
    assert read_depends(path) == ["task-launch-budget"]
    assert offer_dependencies(writer) == []
    assert "task-launch-budget" not in writer.get("/api/initiatives/initiative-d2c-launch").text
    assert "task-launch-budget" not in writer.get("/api/graph?venture=venture-acme").text
    undo = patch(writer, {"title": "Draft the starter-kit offer"}, 2)
    assert undo.status_code == 200
    assert read_depends(path) == ["task-launch-budget"]


def test_link_gesture_and_undo_keep_hidden_dependencies(writer, editor_config):
    root = editor_config.root
    path = plant_hidden(root, ["task-audience-interviews", "task-launch-budget"])
    linked = patch(writer, {"depends_on": ["task-audience-interviews", "task-resident-faq"]})
    assert linked.status_code == 200
    assert "task-launch-budget" not in linked.text
    assert read_depends(path) == ["task-audience-interviews", "task-resident-faq", "task-launch-budget"]
    assert offer_dependencies(writer) == ["task-audience-interviews", "task-resident-faq"]
    undone = patch(writer, {"depends_on": ["task-audience-interviews"]}, 2)
    assert undone.status_code == 200
    assert read_depends(path) == ["task-audience-interviews", "task-launch-budget"]
    assert offer_dependencies(writer) == ["task-audience-interviews"]
    cleared = patch(writer, {"depends_on": []}, 3)
    assert cleared.status_code == 200
    assert read_depends(path) == ["task-launch-budget"]
    assert offer_dependencies(writer) == []
    assert "task-launch-budget" not in writer.get("/api/graph?venture=venture-acme").text


def test_resending_a_stored_hidden_dependency_matches_a_missing_one(writer, editor_config):
    root = editor_config.root
    path = plant_hidden(root, ["task-audience-interviews", "task-launch-budget"])
    original, head = path.read_bytes(), git(root, "rev-parse", "HEAD")
    alone_hidden = patch(writer, {"depends_on": ["task-launch-budget"]})
    alone_missing = patch(writer, {"depends_on": ["task-missing"]})
    mixed_hidden = patch(writer, {"depends_on": ["task-audience-interviews", "task-launch-budget"]})
    mixed_missing = patch(writer, {"depends_on": ["task-audience-interviews", "task-missing"]})
    assert [response.status_code for response in (alone_hidden, alone_missing, mixed_hidden, mixed_missing)] == [400, 400, 400, 400]
    assert alone_hidden.content == alone_missing.content == mixed_hidden.content == mixed_missing.content
    assert alone_hidden.json()["error"] == {"code": "validation", "message": "invalid dependency"}
    for term in (b"task-launch-budget", b"task-missing", b"task-audience-interviews"):
        assert term not in alone_hidden.content
    assert path.read_bytes() == original
    assert git(root, "rev-parse", "HEAD") == head


def test_duplicate_dependency_list_uses_the_error_envelope(writer, editor_config):
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    response = patch(writer, {"depends_on": ["task-audience-interviews", "task-audience-interviews"]})
    assert response.status_code == 400
    assert response.json() == {"error": {"code": "validation", "message": "Record update could not be completed"}}
    assert b"task-audience-interviews" not in response.content
    assert git(root, "rev-parse", "HEAD") == before


def test_new_hidden_and_missing_patches_match_when_a_hidden_link_is_stored(writer, editor_config):
    root = editor_config.root
    path = plant_hidden(root, ["task-launch-budget"])
    other = root / "records/tasks/task-resident-faq.md"
    other.write_text(other.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    original, head = path.read_bytes(), git(root, "rev-parse", "HEAD")
    hidden = patch(writer, {"depends_on": ["task-resident-faq"]})
    missing = patch(writer, {"depends_on": ["task-missing"]})
    assert hidden.status_code == missing.status_code == 400
    assert hidden.content == missing.content
    assert hidden.json()["error"] == {"code": "validation", "message": "invalid dependency"}
    for term in (b"task-launch-budget", b"task-resident-faq", b"task-missing"):
        assert term not in hidden.content and term not in missing.content
    assert path.read_bytes() == original
    assert git(root, "rev-parse", "HEAD") == head
    assert read_depends(path) == ["task-launch-budget"]


def read_depends(path):
    return read_record(path).record.depends_on


def test_hidden_and_missing_dependencies_match_and_do_not_write(writer, editor_config):
    root = editor_config.root
    path = root / "records/tasks/task-launch-offer.md"
    before, original = git(root, "rev-parse", "HEAD"), path.read_bytes()
    hidden = patch(writer, {"depends_on": ["task-launch-budget"]})
    missing = patch(writer, {"depends_on": ["task-missing"]})
    assert hidden.status_code == missing.status_code == 400
    assert hidden.content == missing.content
    assert hidden.json()["error"] == {"code": "validation", "message": "invalid dependency"}
    assert b"task-launch-budget" not in hidden.content
    assert b"task-missing" not in missing.content
    assert path.read_bytes() == original
    assert git(root, "rev-parse", "HEAD") == before


def test_task_link_commits_and_cycle_or_cross_type_does_not(writer, editor_config):
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    linked = patch(writer, {"depends_on": ["task-audience-interviews"]})
    assert linked.status_code == 200
    assert git(root, "rev-list", "--count", f"{before}..HEAD") == "1"
    cycle = patch(writer, {"depends_on": ["task-launch-offer"]}, 2)
    assert cycle.status_code == 400
    assert "depend on itself" in cycle.json()["error"]["message"]
    assert root.as_posix() not in cycle.text
    cross = writer.patch("/api/records/task-resident-faq",
                         json={"changes": {"depends_on": ["initiative-d2c-launch"]}, "expected_version": 1})
    assert cross.status_code == 400
    assert "must be a task" in cross.json()["error"]["message"]
    assert root.as_posix() not in cross.text
    assert git(root, "rev-list", "--count", f"{before}..HEAD") == "1"


def test_commit_recovery_is_not_reported_as_rollback(writer, monkeypatch):
    def committed(*args, **kwargs):
        raise CommittedIndexError("private path", committed=True, commit="a" * 40, current_version=2)
    monkeypatch.setattr(RecordStore, "update_record", committed)
    response = patch(writer)
    assert response.status_code == 500
    assert response.json()["error"] == {"code": "committed_index_error", "message": "Save needs recovery. Reload before trying again.",
                                         "committed": True, "commit": "a" * 40, "current_version": 2}
    assert "private path" not in response.text
