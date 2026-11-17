import json
from dataclasses import replace

import pytest
import yaml

from chassis.errors import AuditError, CommittedIndexError
from chassis.store import RecordStore
from test_security_cli import assert_no_leaks, restricted_terms
from .helpers import git
from .test_write_guard import editor_config, writer

TARGET = "/api/records/task-launch-offer"


def patch(writer, changes=None, version=1, path=TARGET):
    return writer.patch(path, json={"changes": changes or {"title": "Fictional canvas edit"},
                                    "expected_version": version})


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
    assert response.json() == {"error": {"code": "conflict", "message": "Changed elsewhere. Reload the latest.", "current_version": 2}}
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
