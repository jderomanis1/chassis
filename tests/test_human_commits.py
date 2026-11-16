import pytest
from conftest import git

from chassis.errors import DirtyRecordError, WriteError
from chassis.markdown import read_record
from chassis.store import RecordStore

TARGET = "records/tasks/task-launch-budget.md"


@pytest.mark.parametrize("staged", [False, True])
def test_dirty_refusal_then_human_commit_allows_agent_update(git_repo, staged):
    store, path = RecordStore(git_repo), git_repo / TARGET
    path.write_text(path.read_text() + "\nFictional human edit.\n")
    if staged:
        git(git_repo, "add", TARGET)
    original, before = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(DirtyRecordError, match="task-launch-budget.md: uncommitted human edit"):
        store.update_record("task-launch-budget", {"status": "blocked"}, 1, "chief-of-staff")
    assert path.read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == before
    (git_repo / "unrelated.txt").write_text("Unrelated staged human work\n")
    git(git_repo, "add", "unrelated.txt")
    staged_diff = git(git_repo, "diff", "--cached", "--", "unrelated.txt")
    result = store.commit_human(TARGET)
    assert result["path"] == TARGET
    assert result["commit"] == git(git_repo, "rev-parse", "HEAD")
    assert git(git_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Human <human@chassis.local>"
    assert git(git_repo, "show", "--format=", "--name-only") == TARGET
    assert path.read_bytes() == original  # Explicit commit preserves manual bytes.
    assert git(git_repo, "diff", "--cached", "--", "unrelated.txt") == staged_diff
    version = read_record(path).record.version
    result = store.update_record("task-launch-budget", {"status": "blocked"}, version, "chief-of-staff")
    assert result["record"]["version"] == version + 1
    assert "Fictional human edit" in result["record"]["body"]


@pytest.mark.parametrize("path", ["agents.yaml", "../outside.md", "records/tasks"])
def test_commit_human_cannot_commit_policy_or_nonrecord_paths(git_repo, path):
    before = git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(WriteError, match="record path"):
        RecordStore(git_repo).commit_human(path)
    assert git(git_repo, "rev-parse", "HEAD") == before


def test_invalid_manual_source_is_not_committed(git_repo):
    path = git_repo / TARGET
    path.write_text(path.read_text().replace("status: planned", "status: invalid"))
    before, original = git(git_repo, "rev-parse", "HEAD"), path.read_bytes()
    with pytest.raises(ValueError, match="status"):
        RecordStore(git_repo).commit_human(TARGET)
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert path.read_bytes() == original
    with pytest.raises(DirtyRecordError, match="uncommitted human edit"):
        RecordStore(git_repo).update_record("task-launch-budget", {}, 1, "chief-of-staff")


def test_clean_human_path_is_not_an_empty_commit(git_repo):
    before = git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(WriteError, match="no uncommitted human edit"):
        RecordStore(git_repo).commit_human(TARGET)
    assert git(git_repo, "rev-parse", "HEAD") == before
