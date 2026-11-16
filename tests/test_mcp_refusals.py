import pytest
from conftest import git
from mcp_client import StdioClient
from test_mcp_session import assert_lock_released, snapshot

TARGET = "records/tasks/task-launch-budget.md"
UPDATE = {"id": "task-launch-budget", "expected_version": 1,
          "changes": {"next_step": "Review the fictional MCP proposal."}}


@pytest.mark.parametrize("mode", ["dirty", "staged", "skip-worktree", "assume-unchanged",
                                 "skip-worktree-edited", "assume-unchanged-edited"])
def test_mcp_refuses_dirty_and_flagged_records_without_write(git_repo, mode):
    path = git_repo / TARGET
    if mode in {"dirty", "staged"} or mode.endswith("-edited"):
        path.write_text(path.read_text() + "\nUncommitted fictional human note.\n")
    if mode == "staged":
        git(git_repo, "add", TARGET)
    if mode.startswith(("skip-worktree", "assume-unchanged")):
        git(git_repo, "update-index", "--" + mode.removesuffix("-edited"), TARGET)
    before, staged = snapshot(git_repo), git(git_repo, "diff", "--cached")
    with StdioClient(git_repo) as client:
        client.initialize()
        result = client.call("update_record", UPDATE)
        assert result["error"] == "dirty_record"
        assert result["path"] == TARGET and "uncommitted human edit" in result["message"]
        if "worktree" in mode or "unchanged" in mode:
            assert "flag" in result["message"]
        assert snapshot(git_repo) == before
        assert git(git_repo, "diff", "--cached") == staged
    assert_lock_released(git_repo)


@pytest.mark.parametrize("mode", ["unknown", "reviewer", "missing-policy", "invalid-policy", "wrong-scope"])
def test_mcp_authorization_refuses_before_lock_or_index(git_repo, mode):
    policy = git_repo / "agents.yaml"
    agent = mode if mode in {"unknown", "reviewer"} else "chief-of-staff"
    if mode == "missing-policy":
        policy.unlink()
    elif mode == "invalid-policy":
        policy.write_text("version: invalid\n")
    elif mode == "wrong-scope":
        policy.write_text(policy.read_text().replace("task: write", "task: read"))
    before = snapshot(git_repo)
    with StdioClient(git_repo, CHASSIS_AGENT_ID=agent) as client:
        client.initialize()
        result = client.call("update_record", UPDATE)
        assert result["error"] == "unauthorized"
        assert snapshot(git_repo) == before
    assert not (git_repo / ".chassis").exists()


def test_mcp_reloads_policy_between_calls_and_rejects_identity_arguments(git_repo):
    with StdioClient(git_repo) as client:
        client.initialize()
        before = snapshot(git_repo)
        impersonated = client.call("update_record", UPDATE | {"agent": "reviewer"})
        assert impersonated["error"] == "validation" and impersonated["field"] == "agent"
        assert snapshot(git_repo) == before
        first = client.call("update_record", UPDATE)
        assert first["record"]["version"] == 2
        policy = git_repo / "agents.yaml"
        policy.write_text(policy.read_text().replace("task: write", "task: read"))
        before = snapshot(git_repo)
        denied = client.call("update_record", UPDATE | {"expected_version": 2})
        assert denied["error"] == "unauthorized" and snapshot(git_repo) == before


def test_mcp_refuses_symlink_lock_without_write(git_repo, tmp_path):
    outside = tmp_path / "outside-lock"
    outside.write_text("Fictional sentinel")
    (git_repo / ".chassis").mkdir()
    (git_repo / ".chassis/write.lock").symlink_to(outside)
    before = snapshot(git_repo)
    with StdioClient(git_repo) as client:
        client.initialize()
        result = client.call("update_record", UPDATE)
        assert result["error"] == "validation"
        assert result["field"] == "record"
        assert result["reason"] == f"{git_repo / '.chassis/write.lock'}: lock paths cannot be symlinks"
        assert snapshot(git_repo) == before
    assert outside.read_text() == "Fictional sentinel"
