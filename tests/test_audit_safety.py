import json

import pytest
from conftest import git

from chassis.index import RecordIndex
from chassis.store import RecordStore
from chassis.tool_handlers import ToolHandlers


def test_audit_failure_never_returns_a_read_payload(git_repo, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("storage unavailable")
    monkeypatch.setattr("chassis.audit.append_event", fail)
    result = ToolHandlers(git_repo, "chief-of-staff").call("read_record", {"id": "task-launch-budget"})
    assert result == {"error": "audit_error", "message": "Audit unavailable"}


def test_post_commit_audit_failure_keeps_commit_recovery_facts(git_repo, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("storage unavailable")
    monkeypatch.setattr("chassis.audit.append_event", fail)
    result = ToolHandlers(git_repo, "chief-of-staff").call("update_record", {
        "id": "task-launch-offer", "expected_version": 1, "changes": {"status": "done"}})
    assert result == {"error": "audit_error", "message": "Audit unavailable", "committed": True,
                      "commit": git(git_repo, "rev-parse", "HEAD"), "current_version": 2}


def test_audit_symlink_is_refused_without_touching_target(git_repo):
    outside = git_repo / "audit-sentinel"
    outside.write_text("sentinel")
    (git_repo / ".chassis/audit.jsonl").symlink_to(outside)
    with pytest.raises(ValueError, match="Audit unavailable"):
        RecordIndex(git_repo).list_records()
    assert outside.read_text() == "sentinel"
