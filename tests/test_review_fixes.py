from conftest import assert_no_transaction_artifacts
import pytest
from conftest import git

from chassis import git as git_module
from chassis.errors import AuthorizationError, DirtyRecordError
from chassis.git import ensure_clean
from chassis.store import RecordStore
from test_write_permissions import limit_to_ridgeview

TARGET = "records/tasks/task-launch-budget.md"


@pytest.mark.parametrize("flag,tag", [("--skip-worktree", "S"), ("--assume-unchanged", "h")])
@pytest.mark.parametrize("operation,edited", [("update", False), ("human", False), ("human", True)])
def test_flagged_targets_are_refused_before_write_or_commit(git_repo, monkeypatch,
                                                          flag, tag, operation, edited):
    path = git_repo / TARGET
    git(git_repo, "update-index", flag, TARGET)
    if edited:
        path.write_text(path.read_text() + "Hidden fictional human note.\n")
    assert git(git_repo, "ls-files", "-v", "--", TARGET).startswith(tag + " ")
    assert git(git_repo, "status", "--porcelain", "--", TARGET) == ""
    original, before = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    monkeypatch.setattr("chassis.transactions.write_atomic", lambda *a: pytest.fail("Flagged write"))
    with pytest.raises(DirtyRecordError, match="task-launch-budget.md: uncommitted human edit.*flag"):
        store = RecordStore(git_repo)
        if operation == "human":
            store.commit_human(TARGET)
        else:
            store.update_record("task-launch-budget", {"status": "blocked"}, 1, "chief-of-staff")
    assert path.read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert not (git_repo / ".chassis/index.sqlite").exists()


def test_normal_uppercase_h_is_clean(git_repo):
    assert git(git_repo, "ls-files", "-v", "--", TARGET).startswith("H ")
    ensure_clean(git_repo, git_repo / TARGET)


def test_human_commit_uses_content_hash_when_status_reports_clean(git_repo, monkeypatch):
    path = git_repo / TARGET
    path.write_text(path.read_text() + "Fictional manual note.\n")
    original, before = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    run = git_module.run_git

    def stale_status(root, *args, **kwargs):
        return "" if args[0] == "status" else run(root, *args, **kwargs)

    monkeypatch.setattr(git_module, "run_git", stale_status)
    result = RecordStore(git_repo).commit_human(TARGET)
    assert git(git_repo, "rev-parse", "HEAD^") == before
    assert result["commit"] == git(git_repo, "rev-parse", "HEAD")
    assert git(git_repo, "show", "--format=", "--name-only") == TARGET
    assert path.read_bytes() == original


@pytest.mark.parametrize("move", [False, True])
def test_wrong_venture_is_refused_before_reading_a_record_body(git_repo, monkeypatch, move):
    token = limit_to_ridgeview(git_repo)
    store = RecordStore(git_repo, token=token)
    monkeypatch.setattr(store, "_read_current", lambda *a: pytest.fail("Body read before scope authorization"))
    identifier = "task-resident-faq" if move else "task-launch-budget"
    changes = {"venture": "venture-acme", "parent": "initiative-d2c-launch"} if move else {}
    with pytest.raises(AuthorizationError, match="^Write not permitted$"):
        store.update_record(identifier, changes, 1, "limited-writer")
    assert_no_transaction_artifacts(git_repo)
