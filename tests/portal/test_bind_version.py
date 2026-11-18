import json
import os
import socket
import signal
import subprocess
import sys
import time
import urllib.request

import pytest
from .helpers import git
from chassis.portal.config import PortalConfig, validate_bind


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.2", "::", "127.0.0.2", "example.invalid"])
def test_non_ipv4_loopback_bind_is_refused_even_with_legacy_override(monkeypatch, git_repo, host):
    monkeypatch.delenv("CHASSIS_PORTAL_ALLOW_REMOTE", raising=False)
    with pytest.raises(ValueError, match="loopback"):
        validate_bind(host)
    monkeypatch.setenv("CHASSIS_PORTAL_ALLOW_REMOTE", "1")
    with pytest.raises(ValueError, match="loopback"):
        validate_bind(host)


def test_ipv6_loopback_is_accepted_and_remote_hosts_stay_closed(git_repo):
    assert validate_bind("::1") == "::1"
    assert validate_bind("localhost") == "127.0.0.1"
    assert PortalConfig.from_env(git_repo, "::1", 8765).host == "::1"


def test_config_defaults_to_loopback_and_normal_viewer(git_repo):
    config = PortalConfig(root=git_repo)
    assert (config.host, config.port, config.viewer_agent) == ("127.0.0.1", 8765, "reviewer")


def test_cli_refuses_remote_bind_before_server_start(git_repo, monkeypatch):
    monkeypatch.delenv("CHASSIS_PORTAL_ALLOW_REMOTE", raising=False)
    result = subprocess.run([sys.executable, "-m", "chassis.cli", "portal", "--host", "0.0.0.0",
                             "--vault", str(git_repo)], capture_output=True, text=True, timeout=5)
    assert result.returncode == 1 and result.stdout == ""
    assert "Portal requires a loopback host" in result.stderr


def test_matching_etag_returns_not_modified_without_a_body(client):
    first = client.get("/api/version")
    etag = first.json()["etag"]
    assert first.headers["etag"] == f'"{etag}"'
    matched = client.get("/api/version", headers={"If-None-Match": f'"{etag}"'})
    assert matched.status_code == 304
    assert matched.content == b""
    assert client.get("/api/version", headers={"If-None-Match": '"missing"'}).json()["etag"] == etag


def test_version_etag_tracks_visible_commit_and_uncommitted_bytes(client, git_repo, monkeypatch):
    first = client.get("/api/version")
    assert first.status_code == 200
    assert set(first.json()) == {"etag"}
    assert len(first.json()["etag"]) == 64
    assert git(git_repo, "rev-parse", "HEAD") not in first.json()["etag"]
    assert first.headers["cache-control"] == "private, no-store"
    path = git_repo / "records/tasks/task-launch-offer.md"
    path.write_text(path.read_text() + "\nFictional activity.\n")
    second = client.get("/api/version").json()["etag"]
    assert second != first.json()["etag"]
    git(git_repo, "add", str(path))
    with monkeypatch.context() as clock:
        clock.setenv("GIT_COMMITTER_DATE", "2031-01-01T12:00:00Z")
        git(git_repo, "commit", "-qm", "Fictional version proof")
    third = client.get("/api/version").json()["etag"]
    assert third != second
    assert len(third) == 64
    assert client.get("/api/version").json()["etag"] == third


def test_portal_cli_serves_real_loopback_http(portal_config):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = os.environ | {"CHASSIS_PORTAL_VIEWER_AGENT": "reviewer",
                        "CHASSIS_AGENT_TOKEN": portal_config.viewer_token}
    process = subprocess.Popen([sys.executable, "-m", "chassis.cli", "portal", "--port", str(port),
                                "--vault", str(portal_config.root)], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/version", timeout=0.3) as response:
                    assert response.status == 200
                    assert set(json.load(response)) == {"etag"}
                break
            except OSError:
                if process.poll() is not None or time.monotonic() > deadline:
                    pytest.fail("Portal did not start on loopback")
                time.sleep(0.02)
    finally:
        process.terminate()
        _, errors = process.communicate(timeout=5)
    assert process.returncode == -signal.SIGTERM
    assert "Application shutdown complete" in errors
    assert "Traceback" not in errors
