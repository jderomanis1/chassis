"""Undo targets come from editor commits and land as new commits."""
import pytest
from conftest import git

from chassis.errors import ConflictError
from chassis.markdown import read_record
from chassis.store import RecordStore
from chassis.undo import undo_entries
from chassis.validation import read_vault

AGENT = "chief-of-staff"
EMAIL = "homer@chassis.local"
TARGET = "task-launch-offer"
ORIGINAL = "Draft the starter-kit offer"


def listed(root):
    visible = {item.record.id for item in read_vault(root)}
    return undo_entries(root, EMAIL, visible)


def title(root):
    return read_record(root / "records/tasks" / f"{TARGET}.md").record.title


def test_reload_undo_is_a_second_commit_without_rewriting_history(git_repo):
    store = RecordStore(git_repo)
    before = git(git_repo, "rev-parse", "HEAD")
    store.update_record(TARGET, {"title": "First fictional title"}, 1, AGENT)
    store.update_record(TARGET, {"title": "Second fictional title"}, 2, AGENT)
    stacked = listed(git_repo)
    assert [item["changes"] for item in stacked] == [
        {"title": ORIGINAL}, {"title": "First fictional title"}]
    assert stacked[-1]["version"] == 3
    first = store.update_record(stacked[-1]["id"], stacked[-1]["changes"], stacked[-1]["version"], AGENT)
    assert title(git_repo) == "First fictional title"
    assert git(git_repo, "rev-parse", "HEAD^^^") == before
    again = listed(git_repo)
    assert again[-1]["changes"] == {"title": ORIGINAL}
    assert again[-1]["version"] == first["record"]["version"]
    store.update_record(again[-1]["id"], again[-1]["changes"], again[-1]["version"], AGENT)
    assert title(git_repo) == ORIGINAL
    assert listed(git_repo) == []
    assert git(git_repo, "rev-list", "--count", f"{before}..HEAD") == "4"


def test_cached_undo_version_conflicts_after_a_newer_edit(git_repo):
    store = RecordStore(git_repo)
    store.update_record(TARGET, {"title": "First fictional title"}, 1, AGENT)
    cached = listed(git_repo)[-1]
    store.update_record(TARGET, {"title": "Second fictional title"}, cached["version"], AGENT)
    with pytest.raises(ConflictError) as caught:
        store.update_record(cached["id"], cached["changes"], cached["version"], AGENT)
    assert caught.value.details["current_version"] == cached["version"] + 1
    assert title(git_repo) == "Second fictional title"
    assert listed(git_repo)[-1]["version"] == cached["version"] + 1
