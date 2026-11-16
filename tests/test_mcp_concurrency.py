import json
import queue

import pytest
from conftest import git
from mcp_client import StdioClient
from test_mcp_refusals import TARGET
from test_mcp_session import assert_lock_released, snapshot

from chassis.atomic import vault_lock
from chassis.markdown import read_record


def test_two_real_mcp_clients_share_lock_and_have_one_winner(git_repo):
    before = snapshot(git_repo)
    with StdioClient(git_repo, CHASSIS_AGENT_NAME="Fictional Writer A", CHASSIS_AGENT_EMAIL="a@chassis.local") as a, \
            StdioClient(git_repo, CHASSIS_AGENT_NAME="Fictional Writer B", CHASSIS_AGENT_EMAIL="b@chassis.local") as b:
        a.initialize()
        b.initialize()
        with vault_lock(git_repo):
            requests = [client.send("tools/call", {"name": "update_record", "arguments": {
                "id": "task-launch-budget", "expected_version": 1,
                "changes": {"next_step": f"Fictional proposal {label}"}}})
                for client, label in ((a, "A"), (b, "B"))]
            for client, identifier in zip((a, b), requests):
                client.wait_for_log("Calling update_record")
                with pytest.raises(queue.Empty):
                    client.receive(identifier, timeout=0.1)
            assert snapshot(git_repo) == before
        responses = [client.receive(identifier) for client, identifier in zip((a, b), requests)]
        payloads = [response["structuredContent"] for response in responses]
        assert sorted(response["isError"] for response in responses) == [False, True]
        for response, payload in zip(responses, payloads):
            assert json.loads(response["content"][0]["text"]) == payload
        winner = next(i for i, result in enumerate(payloads) if "commit" in result)
        loser = payloads[1 - winner]
        assert loser["error"] == "conflict" and loser["current_version"] == 2
        assert loser["expected_version"] == 1
        result = payloads[winner]
        assert git(git_repo, "rev-list", "--count", f"{before[1]}..HEAD") == "1"
        assert git(git_repo, "rev-parse", "HEAD") == result["commit"]
        assert git(git_repo, "show", "--format=", "--name-only") == TARGET
        label = ("A", "B")[winner]
        assert git(git_repo, "show", "-s", "--format=%an <%ae>") == f"Fictional Writer {label} <{label.lower()}@chassis.local>"
        source = read_record(git_repo / TARGET)
        assert source.record.version == 2 and source.record.next_step == f"Fictional proposal {label}"
        assert a.call("read_record", {"id": source.record.id})["record"] == result["record"]
        assert git(git_repo, "status", "--porcelain") == ""
    assert_lock_released(git_repo)
