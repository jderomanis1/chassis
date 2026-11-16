from contextlib import contextmanager

import pytest
from conftest import git

from chassis import store as store_module
from chassis.errors import AuthorizationError, DirtyRecordError
from chassis.index import RecordIndex
from chassis.store import RecordStore


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_dirty_edits_hidden_from_git_status_are_still_refused(git_repo, flag):
    relative = "records/tasks/task-launch-budget.md"
    path = git_repo / relative
    git(git_repo, "update-index", flag, relative)
    path.write_text(path.read_text() + "Human edit hidden by Git flag\n")
    assert git(git_repo, "status", "--porcelain", "--", relative) == ""
    original, before = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(DirtyRecordError, match="task-launch-budget.md: uncommitted human edit"):
        RecordStore(git_repo).update_record("task-launch-budget", {"status": "blocked"}, 1, "chief-of-staff")
    assert path.read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("identifier,changes,reason", [
    ("task-launch-budget", {"status": "invalid"}, "status"),
    ("task-launch-budget", {"parent": "initiative-missing"}, "parent.*does not exist"),
    ("task-launch-budget", {"depends_on": ["task-missing"]}, "dependency.*does not exist"),
    ("task-launch-budget", {"assigned_agent": "unknown-agent"}, "assigned_agent.*known agent"),
    ("task-maintenance-quotes", {"depends_on": ["task-maintenance-plan"]}, "dependency cycle"),
    ("task-launch-budget", {"type": "initiative"}, "type cannot change"),
    ("task-launch-budget", {"agents": {}}, "agents"),
    ("task-launch-budget", {"body": 17}, "body must be a string"),
])
def test_invalid_updates_preserve_sources_policy_cache_and_head(git_repo, monkeypatch,
                                                               identifier, changes, reason):
    index = RecordIndex(git_repo)
    index.rebuild()
    files = {path: path.read_bytes() for path in (git_repo / "records").rglob("*.md")}
    policy, cached = (git_repo / "agents.yaml").read_bytes(), index.path.read_bytes()
    before = git(git_repo, "rev-parse", "HEAD")
    monkeypatch.setattr("chassis.transactions.write_atomic", lambda *a: pytest.fail("Invalid write reached disk"))
    with pytest.raises(ValueError, match=reason):
        RecordStore(git_repo).update_record(identifier, changes, 1, "chief-of-staff")
    assert {path: path.read_bytes() for path in files} == files
    assert (git_repo / "agents.yaml").read_bytes() == policy
    assert index.path.read_bytes() == cached
    assert git(git_repo, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("operation", ["update", "create"])
def test_policy_is_reloaded_after_waiting_for_lock(git_repo, monkeypatch, operation):
    from test_creates import new_task

    fields = new_task(git_repo)
    lock = store_module.vault_lock
    policy = git_repo / "agents.yaml"
    original, before = (git_repo / "records/tasks/task-launch-budget.md").read_bytes(), git(git_repo, "rev-parse", "HEAD")

    @contextmanager
    def revoke_while_waiting(root):
        with lock(root):
            policy.write_text(policy.read_text().replace("task: write", "task: read"))
            yield

    monkeypatch.setattr(store_module, "vault_lock", revoke_while_waiting)
    monkeypatch.setattr("chassis.transactions.write_atomic", lambda *a: pytest.fail("Revoked write reached disk"))
    store = RecordStore(git_repo)
    with pytest.raises(AuthorizationError, match="venture-acme/task"):
        if operation == "update":
            store.update_record("task-launch-budget", {"status": "blocked"}, 1, "chief-of-staff")
        else:
            store.create_record("task", fields, "chief-of-staff")
    assert (git_repo / "records/tasks/task-launch-budget.md").read_bytes() == original
    assert not (git_repo / "records/tasks/task-fictional-new.md").exists()
    assert git(git_repo, "rev-parse", "HEAD") == before
