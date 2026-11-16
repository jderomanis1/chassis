import json

import pytest
from conftest import git

from chassis.markdown import read_record
from test_creates import new_task
from test_index_cli import cli

TARGET = "records/tasks/task-launch-budget.md"


def test_cli_update_and_structured_stale_conflict_share_the_library_path(git_repo):
    result = cli(git_repo, "update", "task-launch-budget", "--expected-version", "1",
                 "--changes", '{"status":"blocked","blocker_reason":"Fictional review pending"}')
    assert result.returncode == 0 and result.stderr == b""
    payload = json.loads(result.stdout)
    assert payload["record"]["version"] == 2
    assert payload["record"]["status"] == "blocked"
    assert payload["commit"] == git(git_repo, "rev-parse", "HEAD")
    original = (git_repo / TARGET).read_bytes()
    stale = cli(git_repo, "update", "task-launch-budget", "--expected-version", "1",
                "--changes", '{"status":"done"}')
    assert stale.returncode == 3 and stale.stdout == b""
    error = json.loads(stale.stderr)
    assert error["error"] == "conflict" and error["current_version"] == 2
    assert (git_repo / TARGET).read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == payload["commit"]


def test_cli_create_works_with_explicit_vault(git_repo, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    result = cli(elsewhere, "create", "task", "--fields", json.dumps(new_task(git_repo)),
                 "--vault", str(git_repo))
    assert result.returncode == 0 and result.stderr == b""
    record = json.loads(result.stdout)["record"]
    assert record["id"] == "task-fictional-new" and record["version"] == 1
    assert read_record(git_repo / "records/tasks/task-fictional-new.md").body == record["body"]


def test_cli_human_commit_attributes_manual_edit(git_repo):
    path = git_repo / TARGET
    path.write_text(path.read_text() + "\nManual fictional note.\n")
    original = path.read_bytes()
    result = cli(git_repo, "commit-human", TARGET)
    assert result.returncode == 0 and result.stderr == b""
    assert json.loads(result.stdout)["path"] == TARGET
    assert git(git_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Human <human@chassis.local>"
    assert path.read_bytes() == original


@pytest.mark.parametrize("agent", [None, "reviewer", "unknown-agent"])
def test_cli_denied_caller_makes_no_record_or_git_changes(git_repo, monkeypatch, agent):
    if agent is None:
        monkeypatch.delenv("CHASSIS_AGENT_ID")
    else:
        monkeypatch.setenv("CHASSIS_AGENT_ID", agent)
    original, before = (git_repo / TARGET).read_bytes(), git(git_repo, "rev-parse", "HEAD")
    result = cli(git_repo, "update", "task-launch-budget", "--expected-version", "1", "--changes", "{}")
    assert result.returncode == 1 and result.stdout == b""
    assert json.loads(result.stderr)["error"] == "unauthorized"
    assert (git_repo / TARGET).read_bytes() == original
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert not (git_repo / ".chassis").exists()


def test_cli_bad_json_is_actionable_and_does_not_commit(git_repo):
    before = git(git_repo, "rev-parse", "HEAD")
    result = cli(git_repo, "update", "task-launch-budget", "--expected-version", "1", "--changes", "{")
    assert result.returncode == 1 and result.stdout == b""
    assert b"INVALID" in result.stderr and b"Traceback" not in result.stderr
    assert git(git_repo, "rev-parse", "HEAD") == before
