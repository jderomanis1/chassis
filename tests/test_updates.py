import pytest
from conftest import git

from chassis.errors import ConflictError, WriteError
from chassis.index import RecordIndex
from chassis.markdown import read_record
from chassis.store import RecordStore

IDENTIFIER = "task-launch-budget"
TARGET = f"records/tasks/{IDENTIFIER}.md"
AGENT = "chief-of-staff"


def test_good_update_bumps_once_commits_only_target_as_agent_and_refreshes_index(git_repo):
    store, index = RecordStore(git_repo), RecordIndex(git_repo)
    original = index.get_record(IDENTIFIER)
    timestamp = read_record(git_repo / TARGET).record.updated_at
    before = git(git_repo, "rev-parse", "HEAD")
    (git_repo / "unrelated.txt").write_text("Keep staged\n")
    git(git_repo, "add", "unrelated.txt")
    staged = git(git_repo, "diff", "--cached")
    result = store.update_record(IDENTIFIER, {"status": "blocked"}, original["version"], AGENT)
    assert result["record"]["version"] == original["version"] + 1
    assert result["record"]["status"] == "blocked"
    assert result["record"]["body"] == original["body"]
    assert read_record(git_repo / TARGET).record.updated_at > timestamp
    assert git(git_repo, "rev-list", "--count", f"{before}..HEAD") == "1"
    assert git(git_repo, "show", "--format=", "--name-only", "HEAD") == TARGET
    assert git(git_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Homer <homer@chassis.local>"
    assert git(git_repo, "rev-parse", "HEAD") == result["commit"]
    assert git(git_repo, "diff", "--cached") == staged
    assert index.get_record(IDENTIFIER) == result["record"]


def test_stale_version_returns_current_version_without_file_cache_or_commit_change(git_repo):
    store = RecordStore(git_repo)
    store.update_record(IDENTIFIER, {"status": "blocked"}, 1, AGENT)
    path = git_repo / TARGET
    cache = git_repo / ".chassis/index.sqlite"
    original, cached = path.read_bytes(), cache.read_bytes()
    before = git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(ConflictError, match="expected version 1; current version 2") as error:
        store.update_record(IDENTIFIER, {"status": "done"}, 1, AGENT)
    assert error.value.as_dict()["current_version"] == 2
    assert path.read_bytes() == original and cache.read_bytes() == cached
    assert git(git_repo, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("field,value", [("id", "task-new"), ("version", 5),
                                        ("updated_at", "2030-01-01T00:00:00Z")])
def test_immutable_update_preserves_file_and_git_history(git_repo, field, value):
    path = git_repo / TARGET
    original, before = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(WriteError, match=f"immutable.*{field}"):
        RecordStore(git_repo).update_record(IDENTIFIER, {field: value}, 1, AGENT)
    assert path.read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert not (git_repo / ".chassis").exists()
