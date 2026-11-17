import pytest
from conftest import git

from chassis.index import RecordIndex
from chassis.markdown import read_record
from chassis.store import RecordStore

AGENT = "chief-of-staff"


def new_task(root, **changes):
    fields = read_record(root / "records/tasks/task-launch-budget.md").record.model_dump(mode="json")
    for key in ("type", "version", "updated_at"):
        del fields[key]
    return fields | {"id": "task-fictional-new", "body": "\r\nFictional task body.\r\n"} | changes


def test_create_validates_commits_once_and_populates_index(git_repo):
    fields = new_task(git_repo)
    before = git(git_repo, "rev-parse", "HEAD")
    result = RecordStore(git_repo).create_record("task", fields, AGENT)
    assert result["record"]["version"] == 1
    assert result["record"]["body"] == fields["body"]
    assert result["record"]["sensitivity"] == "restricted"
    assert git(git_repo, "rev-parse", "HEAD^") == before
    assert git(git_repo, "show", "--format=", "--name-only") == "records/tasks/task-fictional-new.md"
    assert git(git_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Homer <homer@chassis.local>"
    assert RecordIndex(git_repo).get_record(fields["id"]) == result["record"]
    assert git(git_repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("changes,reason", [
    ({"id": "task-launch-budget"}, "duplicate ID"),
    ({"parent": "initiative-missing"}, "parent.*does not exist"),
    ({"depends_on": ["task-missing"]}, "invalid dependency"),
    ({"depends_on": ["task-fictional-new"]}, "cannot depend on itself"),
    ({"status": "invalid"}, "status"),
    ({"assigned_agent": "unknown-agent"}, "assigned_agent.*known agent"),
    ({"version": 5}, "immutable.*version"),
    ({"updated_at": "2030-01-01T00:00:00Z"}, "immutable.*updated_at"),
    ({"body": 17}, "body must be a string"),
])
def test_invalid_create_writes_nothing(git_repo, changes, reason):
    store = RecordStore(git_repo)
    index = RecordIndex(git_repo)
    index.rebuild()
    files = {path: path.read_bytes() for path in (git_repo / "records").rglob("*.md")}
    cache, before = index.path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match=reason):
        store.create_record("task", new_task(git_repo, **changes), AGENT)
    assert {path: path.read_bytes() for path in (git_repo / "records").rglob("*.md")} == files
    assert index.path.read_bytes() == cache
    assert git(git_repo, "rev-parse", "HEAD") == before


def test_create_rejects_a_multi_record_cycle_in_the_proposed_graph(git_repo):
    path = git_repo / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("depends_on: []", "depends_on: [task-fictional-new]"))
    original, before = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="dependency cycle"):
        RecordStore(git_repo).create_record("task", new_task(git_repo, depends_on=["task-launch-budget"]), AGENT)
    assert path.read_bytes() == original
    assert not (git_repo / "records/tasks/task-fictional-new.md").exists()
    assert git(git_repo, "rev-parse", "HEAD") == before
