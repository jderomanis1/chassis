import pytest
from mcp_client import StdioClient
from test_mcp_refusals import UPDATE
from test_mcp_session import snapshot

from chassis.errors import CommittedIndexError, WriteError
from chassis.store import RecordStore
from chassis.tool_handlers import ToolHandlers


def test_git_hook_diagnostics_do_not_leak_stack_traces_over_mcp(git_repo):
    hook = git_repo / ".git/hooks/pre-commit"
    hook.write_text('#!/bin/sh\nprintf "Traceback (most recent call last):\\nprivate hook diagnostic\\n" >&2\nexit 1\n')
    hook.chmod(0o755)
    before = snapshot(git_repo)
    with StdioClient(git_repo) as client:
        client.initialize()
        result = client.call("update_record", UPDATE)
        assert result["error"] == "git_error"
        assert "Traceback" not in str(result) and "private hook diagnostic" not in str(result)
        assert snapshot(git_repo) == before
    assert "private hook diagnostic" in "".join(client.stderr_lines)


@pytest.mark.parametrize("error", [
    WriteError("Inspect before retrying", committed="unknown"),
    CommittedIndexError("private cache diagnostic", committed=True, commit="a" * 40, current_version=2),
])
def test_failure_mapping_preserves_commit_outcome_without_raw_diagnostics(git_repo, monkeypatch, error):
    def fail(*_):
        raise error
    monkeypatch.setattr(RecordStore, "update_record", fail)
    result = ToolHandlers(git_repo, "chief-of-staff").call("update_record", UPDATE)
    assert result["committed"] == error.details["committed"]
    if result["committed"] is True:
        assert result["commit"] == "a" * 40 and result["current_version"] == 2
        assert "private cache diagnostic" not in str(result)
