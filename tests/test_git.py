import pytest
from conftest import git

from chassis.errors import DirtyRecordError, GitError, WriteError
from chassis.git import Identity, commit_file, ensure_clean

TARGET = "records/tasks/task-launch-budget.md"


@pytest.mark.parametrize("created", [False, True])
def test_commit_touches_only_target_with_configured_author_and_preserves_staging(git_repo, created):
    target = git_repo / ("records/tasks/task-new.md" if created else TARGET)
    target.write_text("Fictional manual content\n")
    (git_repo / "unrelated.txt").write_text("Keep this staged\n")
    git(git_repo, "add", "unrelated.txt")
    staged = git(git_repo, "diff", "--cached", "--", "unrelated.txt")
    before = git(git_repo, "rev-parse", "HEAD")
    commit = commit_file(git_repo, target, Identity.from_env("AGENT"), "Sample update")
    assert git(git_repo, "rev-parse", "HEAD^") == before
    assert git(git_repo, "rev-parse", "HEAD") == commit
    assert git(git_repo, "show", "--format=", "--name-only", commit) == target.relative_to(git_repo).as_posix()
    assert git(git_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Homer <homer@chassis.local>"
    assert git(git_repo, "diff", "--cached", "--", "unrelated.txt") == staged
    assert git(git_repo, "status", "--porcelain", "--", str(target)) == ""


@pytest.mark.parametrize("staged", [False, True])
def test_dirty_guard_names_file_and_reason(git_repo, staged):
    target = git_repo / TARGET
    target.write_text(target.read_text() + "Human edit\n")
    if staged:
        git(git_repo, "add", TARGET)
    with pytest.raises(DirtyRecordError, match="task-launch-budget.md: uncommitted human edit"):
        ensure_clean(git_repo, target)


def test_failed_create_commit_removes_only_its_intent_to_add(git_repo):
    target = git_repo / "records/tasks/task-new.md"
    target.write_text("Fictional content\n")
    hook = git_repo / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    before = git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(GitError, match="git commit failed"):
        commit_file(git_repo, target, Identity.from_env("AGENT"), "Must fail")
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert git(git_repo, "ls-files", "--", str(target)) == ""


def test_missing_identity_fails_without_falling_back_to_git_config(monkeypatch):
    monkeypatch.delenv("CHASSIS_AGENT_NAME", raising=False)
    with pytest.raises(WriteError, match="CHASSIS_AGENT_NAME"):
        Identity.from_env("AGENT")
