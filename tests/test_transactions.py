import pytest
from conftest import git

from chassis.atomic import vault_lock
from chassis.errors import CommittedIndexError, GitError
from chassis.git import Identity
from chassis.index import RecordIndex
from chassis.markdown import ParsedRecord, read_record
from chassis.models import Record
from chassis.transactions import persist_record


def candidate(root, created=False):
    original = read_record(root / "records/tasks/task-launch-budget.md")
    fields = original.record.model_dump() | {"version": 2, "status": "blocked", "blocker_reason": "Fictional review pending"}
    if created:
        fields.update(id="task-new", version=1)
    path = original.path.with_name(f"{fields['id']}.md")
    return ParsedRecord(path, Record.model_validate(fields), original.body)


@pytest.mark.parametrize("created", [False, True])
def test_failed_commit_restores_record_and_leaves_head_index_and_staging_unchanged(git_repo, created):
    item = candidate(git_repo, created)
    original = None if created else item.path.read_bytes()
    index = RecordIndex(git_repo)
    index.rebuild()
    cache = index.path.read_bytes()
    before = git(git_repo, "rev-parse", "HEAD")
    (git_repo / "unrelated.txt").write_text("Human work\n")
    git(git_repo, "add", "unrelated.txt")
    staged = git(git_repo, "diff", "--cached")
    hook = git_repo / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    with vault_lock(git_repo), pytest.raises(GitError, match="git commit failed"):
        persist_record(git_repo, item, original, Identity.from_env("AGENT"), "Must fail")
    assert (item.path.read_bytes() if item.path.exists() else None) == original
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert git(git_repo, "diff", "--cached") == staged
    assert index.path.read_bytes() == cache


def test_cache_failure_after_commit_reports_commit_instead_of_false_rollback(git_repo, monkeypatch):
    item = candidate(git_repo)
    original = item.path.read_bytes()

    def fail_rebuild(self):
        raise OSError("simulated full disk")

    monkeypatch.setattr(RecordIndex, "_rebuild_locked", fail_rebuild)
    with vault_lock(git_repo), pytest.raises(CommittedIndexError, match="committed.*index refresh failed") as error:
        persist_record(git_repo, item, original, Identity.from_env("AGENT"), "Commit then cache failure")
    details = error.value.as_dict()
    assert details["committed"] is True
    assert details["commit"] == git(git_repo, "rev-parse", "HEAD")
    assert details["current_version"] == 2
    assert read_record(item.path).record.version == 2
    assert git(git_repo, "status", "--porcelain", "--", str(item.path)) == ""
