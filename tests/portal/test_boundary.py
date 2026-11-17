import json
import secrets

import pytest
import yaml

from conftest import EphemeralToken, issue
from chassis.errors import AuthorizationError
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig
from test_security_cli import assert_no_leaks, restricted_terms

PATHS = ["/api/version", "/api/snapshot", "/api/ventures/venture-acme",
         "/api/initiatives/initiative-d2c-launch", "/api/graph", "/api/search?q=fictional"]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def test_all_endpoints_only_allow_get(client, method):
    for path in PATHS:
        response = client.request(method, path)
        assert response.status_code == 405
        assert response.headers["allow"] == "GET"
        if method != "HEAD":
            assert response.json() == {"error": {"code": "validation", "message": "Only GET is supported"}}
        else:
            assert response.content == b""


@pytest.mark.parametrize("headers", [{"Origin": "https://untrusted.example.invalid"},
    {"Origin": "null"}, {"Origin": "http://127.0.0.1:1234"}, {"Host": "untrusted.example.invalid:8765"}])
def test_all_endpoints_refuse_other_origins_and_hosts(client, headers):
    for path in PATHS:
        response = client.get(path, headers=headers)
        assert response.status_code == 403
        assert response.json() == {"error": {"code": "validation", "message": "Origin or host not permitted"}}


def test_matching_origin_is_allowed_and_ask_does_not_exist(client):
    for path in PATHS:
        assert client.get(path, headers={"Origin": "http://127.0.0.1:8765"}).status_code == 200
    assert client.get("/api/ask").status_code == 404
    assert client.post("/api/ask", json={"question": "Fictional question"}).status_code == 405


@pytest.mark.parametrize("path", ["/api/ventures/INVALID!", "/api/initiatives/INVALID!", "/api/graph?venture=INVALID!"])
def test_invalid_ids_use_validation_envelope_without_echoing_input(client, path):
    response = client.get(path)
    assert response.status_code == 400
    assert response.json() == {"error": {"code": "validation", "message": "Invalid request"}}


def test_missing_and_hidden_scope_have_identical_envelopes(client, git_repo):
    path = git_repo / "records/ventures/venture-acme.md"
    path.write_text(path.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    for url in ["/api/graph?venture=venture-acme", "/api/graph?venture=venture-missing",
                "/api/ventures/venture-acme", "/api/ventures/venture-missing",
                "/api/initiatives/initiative-d2c-launch", "/api/initiatives/initiative-missing"]:
        response = client.get(url)
        assert response.status_code == 404
        assert response.json() == {"error": {"code": "not_found", "message": "Not found"}}


def test_revoked_viewer_cannot_read_any_endpoint(client, git_repo):
    issue(git_repo, "reviewer")
    for path in PATHS:
        response = client.get(path)
        assert response.status_code == 404
        assert response.json() == {"error": {"code": "not_found", "message": "Not found"}}
    events = [json.loads(line) for line in (git_repo / ".chassis/audit.jsonl").read_text().splitlines()]
    assert [e["outcome"] for e in events] == ["denied"] * len(PATHS)
    assert all(e["record_ids"] == [] for e in events)


@pytest.mark.parametrize("mode", ["unknown", "empty", "missing-token", "wrong-token"])
def test_portal_rejects_unproven_viewer_at_startup(git_repo, mode):
    agent, token = "reviewer", issue(git_repo, "reviewer")
    if mode in {"unknown", "empty"}:
        agent = "unknown-agent" if mode == "unknown" else ""
    else:
        token = "" if mode == "missing-token" else EphemeralToken(secrets.token_urlsafe(32))
    with pytest.raises(AuthorizationError, match="^Portal viewer authentication failed$"):
        create_app(PortalConfig(git_repo, viewer_agent=agent, viewer_token=token))


def test_viewer_grants_scope_every_projection_and_search(client, git_repo):
    path = git_repo / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    del policy["agents"]["reviewer"]["ventures"]["venture-acme"]
    path.write_text(yaml.safe_dump(policy))
    assert [v["id"] for v in client.get("/api/snapshot").json()["ventures"]] == ["venture-ridgeview"]
    assert len(client.get("/api/graph").json()["nodes"]) == 8
    assert client.get("/api/ventures/venture-acme").status_code == 404
    assert client.get("/api/initiatives/initiative-d2c-launch").status_code == 404
    assert client.get("/api/search?q=Acme").json() == {"hits": []}


def test_internal_errors_return_generic_json_without_stack_or_record_content(client, git_repo, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Traceback " + " ".join(restricted_terms(git_repo)))

    monkeypatch.setattr(client.app.state.index, "list_records", fail)
    monkeypatch.setattr(client.app.state.index, "search", fail)
    for path in PATHS[1:]:
        response = client.get(path)
        assert response.status_code == 500
        assert response.json() == {"error": {"code": "internal", "message": "Request could not be completed"}}
        assert_no_leaks([response.text], restricted_terms(git_repo))
        assert "Traceback" not in response.text
