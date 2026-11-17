import json
import os
import secrets
import subprocess
import sys

import pytest
import yaml
from conftest import EphemeralToken, issue
from mcp_client import StdioClient
from chassis.read_model import neutral_graph
from test_security_cli import assert_no_leaks, restricted_terms
from test_read_error_safety import damage_hidden_record, normal_writer, create_arguments, template_arguments


@pytest.mark.parametrize("mode", ["unknown", "empty", "missing-token", "wrong-token"])
def test_real_stdio_denies_unproven_identity_before_handshake(git_repo, mode):
    env = os.environ.copy()
    if mode in {"unknown", "empty"}:
        env["CHASSIS_AGENT_ID"] = "unknown-agent" if mode == "unknown" else ""
    else:
        env["CHASSIS_AGENT_TOKEN"] = "" if mode == "missing-token" else EphemeralToken(secrets.token_urlsafe(32))
    result = subprocess.run([sys.executable, "-m", "chassis.mcp_server", "--vault", str(git_repo)],
                            env=env, input="", capture_output=True, text=True, timeout=5)
    assert result.returncode == 1 and result.stdout == ""
    assert "Authentication failed" in result.stderr
    assert "Traceback" not in result.stderr
    assert_no_leaks([result.stderr], restricted_terms(git_repo))


def test_real_stdio_normal_clearance_leak_scan_and_audit(git_repo):
    token = issue(git_repo, "reviewer")
    with StdioClient(git_repo, CHASSIS_AGENT_ID="reviewer", CHASSIS_AGENT_TOKEN=token) as client:
        client.initialize()
        records = client.call("list_records", {})["records"]
        assert len(records) == 12
        graph = neutral_graph(records, "venture-acme")
        assert len(graph["nodes"]) == 4 and graph["edges"] == []
        assert client.call("list_records", {"filters": {"sensitivity": "restricted"}}) == {"records": []}
        hidden = client.call("read_record", {"id": "task-launch-budget"})
        assert hidden == client.call("read_record", {"id": "missing-id"}) == {
            "error": "not_found", "message": "Record not found"}
        for term in restricted_terms(git_repo):
            assert client.call("search", {"query": term}) == {"records": []}
        assert client.call("update_record", {"id": "task-launch-budget", "expected_version": 1,
                                             "changes": {}}) == {"error": "unauthorized", "message": "Write not permitted"}
        assert client.call("create_record", {"type": "task", "fields": {}}) == {
            "error": "unauthorized", "message": "Write not permitted"}
        assert client.call("create_from_template", {"template": "initiative", "venture": "venture-acme", "fields": {}}) == {
            "error": "unauthorized", "message": "Write not permitted"}
    assert_no_leaks(client.stdout_lines + client.stderr_lines, restricted_terms(git_repo))
    audit = (git_repo / ".chassis/audit.jsonl").read_text()
    assert [json.loads(line)["tool"] for line in audit.splitlines()] == [
        "list_records", "list_records", "read_record", "read_record",
        "search", "search", "search", "search", "update_record", "create_record", "create_from_template"]
    assert token not in audit
    assert_no_leaks([audit], restricted_terms(git_repo))


def test_real_stdio_scope_clearance_and_live_revocation(git_repo):
    path = git_repo / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["scoped-reader"] = {"ventures": {
        "venture-ridgeview": {"venture": "read", "initiative": "read", "task": "read"}}}
    path.write_text(yaml.safe_dump(policy))
    token = issue(git_repo, "scoped-reader")
    with StdioClient(git_repo, CHASSIS_AGENT_ID="scoped-reader", CHASSIS_AGENT_TOKEN=token) as client:
        client.initialize()
        records = client.call("list_records", {})["records"]
        assert {r["venture"] for r in records} == {"venture-ridgeview"}
        assert client.call("search", {"query": "Acme"}) == {"records": []}
    with StdioClient(git_repo) as client:
        client.initialize()
        assert client.call("read_record", {"id": "task-launch-budget"})["record"]["id"] == "task-launch-budget"
        issue(git_repo, "chief-of-staff")
        assert client.call("list_records", {}) == {"records": []}
        assert client.call("search", {"query": "fictional"}) == {"records": []}
        assert client.call("read_record", {"id": "venture-acme"}) == {
            "error": "not_found", "message": "Record not found"}


@pytest.mark.parametrize("private_field", [0, 1, 2, 3], ids=["id", "title", "owner", "body"])
def test_real_stdio_hidden_validation_error_cannot_reveal_private_fields(template_repo, private_field):
    git_repo = template_repo
    terms = restricted_terms(git_repo)
    damage_hidden_record(git_repo, terms[private_field])
    token = normal_writer(git_repo)
    with StdioClient(git_repo, CHASSIS_AGENT_ID="normal-writer", CHASSIS_AGENT_TOKEN=token) as client:
        client.initialize()
        results = [client.call(name, args) for name, args in [
            ("list_records", {}), ("read_record", {"id": "venture-acme"}), ("search", {"query": "fictional"}),
            ("update_record", {"id": "task-launch-offer", "expected_version": 1, "changes": {"title": "Fictional updated offer"}}),
            ("create_record", create_arguments(git_repo)), ("create_from_template", template_arguments())]]
    assert_no_leaks(client.stdout_lines + client.stderr_lines, terms)
    assert results == [{"error": "validation", "field": field,
                        "reason": "Records unavailable; source validation failed"}
                       for field in ["filters", "record", "record", "record", "record", "record"]]
