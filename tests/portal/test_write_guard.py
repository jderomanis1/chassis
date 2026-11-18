import json
import secrets
from dataclasses import replace

import pytest
import yaml
from starlette.testclient import TestClient

from chassis.errors import AuthorizationError
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig
from .helpers import EphemeralToken, git, issue


@pytest.fixture
def editor_config(portal_config):
    root = portal_config.root
    path = root / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["canvas-editor"] = {
        "clearance": "normal", "ventures": policy["agents"]["chief-of-staff"]["ventures"]}
    path.write_text(yaml.safe_dump(policy))
    git(root, "add", "agents.yaml")
    git(root, "commit", "-qm", "Provision fictional normal editor")
    return replace(portal_config, allow_writes=True, editor_agent="canvas-editor",
                   editor_token=issue(root, "canvas-editor"))


@pytest.fixture
def writer(editor_config):
    with TestClient(create_app(editor_config), base_url="http://127.0.0.1:8765") as client:
        client.headers.update({"Origin": "http://127.0.0.1:8765", "Sec-Fetch-Site": "same-origin",
                               "X-Chassis-CSRF": client.get("/api/session").json()["csrf"],
                               "Content-Type": "application/json"})
        yield client


def test_write_enable_is_explicit_and_credentials_stay_server_side(editor_config, monkeypatch):
    monkeypatch.setenv("CHASSIS_PORTAL_EDITOR_AGENT", editor_config.editor_agent)
    monkeypatch.setenv("CHASSIS_PORTAL_EDITOR_TOKEN", editor_config.editor_token)
    config = PortalConfig.from_env(editor_config.root)
    assert config.allow_writes is False
    assert PortalConfig.from_env(editor_config.root, allow_writes=True).allow_writes is True
    with TestClient(create_app(editor_config), base_url="http://127.0.0.1:8765") as client:
        session = client.get("/api/session").json()
        assert session["writes_enabled"] is True
        assert session["viewer"] == "reviewer"
        assert editor_config.editor_token not in json.dumps(session)
        assert editor_config.editor_token not in repr(editor_config)


@pytest.mark.parametrize("mode", ["missing", "wrong", "viewer", "chief", "restricted", "read-only"])
def test_launch_refuses_an_unproven_or_privileged_editor(editor_config, mode):
    config = editor_config
    if mode in {"missing", "wrong"}:
        config = replace(config, editor_token="" if mode == "missing" else EphemeralToken(secrets.token_urlsafe(32)))
    elif mode in {"viewer", "chief"}:
        agent = "reviewer" if mode == "viewer" else "chief-of-staff"
        token = config.viewer_token if mode == "viewer" else issue(config.root, agent)
        config = replace(config, editor_agent=agent, editor_token=token)
    else:
        path = config.root / "agents.yaml"
        policy = yaml.safe_load(path.read_text())
        if mode == "restricted":
            policy["agents"]["canvas-editor"]["clearance"] = "restricted"
        else:
            policy["agents"]["canvas-editor"]["ventures"] = policy["agents"]["reviewer"]["ventures"]
        path.write_text(yaml.safe_dump(policy))
    with pytest.raises(AuthorizationError, match="editor|Write not permitted"):
        create_app(config)


@pytest.mark.parametrize("header,value", [
    ("Host", "evil.example:8765"), ("Origin", None), ("Origin", "null"),
    ("Origin", "http://localhost:8765"), ("Origin", "https://foreign.example"),
    ("Content-Type", "application/x-www-form-urlencoded"), ("Content-Type", "multipart/form-data"),
    ("Content-Type", "application/json; charset=utf-8"), ("X-Chassis-CSRF", None),
    ("X-Chassis-CSRF", ""), ("X-Chassis-CSRF", "invalid"),
    ("Sec-Fetch-Site", None), ("Sec-Fetch-Site", "same-site"), ("Sec-Fetch-Site", "cross-site")])
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
def test_shared_guard_refuses_every_unsafe_write(writer, editor_config, header, value, method, monkeypatch):
    from chassis.store import RecordStore
    monkeypatch.setattr(RecordStore, "update_record", lambda *a, **k: pytest.fail("library write reached"))
    before = git(editor_config.root, "rev-parse", "HEAD")
    if value is None:
        del writer.headers[header]
    else:
        writer.headers[header] = value
    response = writer.request(method, "/api/records/task-launch-offer", content=b"{}")
    assert response.status_code == 403
    assert set(response.json()) == {"error"}
    assert not any(key.startswith("access-control-") for key in response.headers)
    assert git(editor_config.root, "rev-parse", "HEAD") == before
    events = [json.loads(line) for line in (editor_config.root / ".chassis/audit.jsonl").read_text().splitlines()]
    assert events[-1]["tool"] == "portal_write"
    assert events[-1]["outcome"] == "denied"
    assert events[-1]["record_ids"] == []
    assert editor_config.editor_token not in json.dumps(events)


def test_payload_cap_checks_actual_bytes_and_launch_csrf(writer, editor_config):
    response = writer.patch("/api/records/task-launch-offer", content=b"x" * (65536 + 1))
    assert response.status_code == 403
    with TestClient(create_app(editor_config), base_url="http://127.0.0.1:8765") as other:
        writer.headers["X-Chassis-CSRF"] = other.get("/api/session").json()["csrf"]
    assert writer.patch("/api/records/task-launch-offer", content=b"{}").status_code == 403


def test_editor_revocation_and_rate_limit_stop_writes(writer, editor_config):
    issue(editor_config.root, "canvas-editor")
    assert writer.patch("/api/records/task-launch-offer", content=b"{}").status_code == 404
    # Rejected requests consume the same conservative per-launch write budget.
    for _ in range(59):
        assert writer.patch("/api/records/task-launch-offer", content=b"{}").status_code == 404
    assert writer.patch("/api/records/task-launch-offer", content=b"{}").status_code == 429


def test_csp_is_strict_and_local(client):
    csp = client.get("/api/session").headers["content-security-policy"]
    assert "media-src 'self'" in [directive.strip() for directive in csp.split(";")]
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
    assert "connect-src 'self'" in csp and "frame-ancestors 'none'" in csp
