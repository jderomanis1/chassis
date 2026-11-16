import json
import os
import signal
import time

import pytest

from mcp_client import StdioClient
from test_mcp_session import assert_lock_released


def raw(client, text):
    client.process.stdin.write(text)
    client.process.stdin.flush()
    return client.responses.get(timeout=5)


def test_malformed_json_is_parse_error_and_session_recovers(git_repo):
    with StdioClient(git_repo) as client:
        client.initialize()
        assert raw(client, '{bad json}\n') == {
            "jsonrpc": "2.0", "id": None,
            "error": {"code": -32700, "message": "Parse error"}}
        assert client.call("search", {"query": "unmatched text"}) == {"records": []}


@pytest.mark.parametrize("limit", [1024, 1024 * 1024])
def test_payload_limit_is_bounded_structured_and_recovers(git_repo, limit):
    with StdioClient(git_repo, CHASSIS_MCP_MAX_REQUEST_BYTES=str(limit)) as client:
        client.initialize()
        assert raw(client, 'x' * (limit + 1) + '\n') == {
            "jsonrpc": "2.0", "id": None,
            "error": {"code": -32000, "message": "Request exceeds payload limit",
                      "data": {"code": "payload_too_large", "max_bytes": limit}}}
        assert client.call("search", {"query": "unmatched text"}) == {"records": []}


def test_sigterm_finishes_active_transaction_and_releases_lock(git_repo):
    hook = git_repo / ".git/hooks/pre-commit"
    hook.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nimport time\n"
                    "Path('.chassis/hook-started').touch()\n"
                    "while not Path('.chassis/hook-continue').exists(): time.sleep(0.01)\n")
    hook.chmod(0o755)
    with StdioClient(git_repo) as client:
        client.initialize()
        client.send("tools/call", {"name": "update_record", "arguments": {
            "id": "task-launch-offer", "expected_version": 1, "changes": {"status": "done"}}})
        deadline = time.monotonic() + 5
        while not (git_repo / ".chassis/hook-started").exists():
            if time.monotonic() > deadline:
                pytest.fail("Git hook did not start")
            time.sleep(0.01)
        os.kill(client.process.pid, signal.SIGTERM)
        (git_repo / ".chassis/hook-continue").touch()
        assert client.process.wait(timeout=5) == 0
    assert_lock_released(git_repo)

