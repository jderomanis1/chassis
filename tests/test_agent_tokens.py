import hashlib
import json
import os
import stat
import subprocess
import sys

import pytest
import yaml
from conftest import EphemeralToken, git, issue

from chassis.identity import authenticate, create_agent_token
from chassis.index import RecordIndex


def test_cli_prints_secret_once_stores_only_hash_and_rotates(git_repo):
    old = EphemeralToken(os.environ["CHASSIS_AGENT_TOKEN"])
    result = subprocess.run([sys.executable, "-m", "chassis.cli", "agent-token", "create",
                             "chief-of-staff", "--vault", str(git_repo)], capture_output=True, text=True)
    assert result.returncode == 0 and result.stderr == ""
    assert len(result.stdout.splitlines()) == 1
    token = EphemeralToken(result.stdout.strip())
    assert len(token) == 43
    assert authenticate(git_repo, "chief-of-staff", token) is True
    assert authenticate(git_repo, "chief-of-staff", old) is False
    path = git_repo / ".chassis/agent-tokens.yaml"
    data = yaml.safe_load(path.read_text())
    assert data["tokens"]["chief-of-staff"] == hashlib.sha256(token.encode()).hexdigest()
    assert token not in path.read_text()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert git(git_repo, "check-ignore", ".chassis/agent-tokens.yaml") == ".chassis/agent-tokens.yaml"
    assert git(git_repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("damage", ["missing", "invalid", "symlink", "unknown-agent"])
def test_bad_token_storage_fails_closed(git_repo, damage):
    token = EphemeralToken(os.environ["CHASSIS_AGENT_TOKEN"])
    path = git_repo / ".chassis/agent-tokens.yaml"
    if damage == "missing":
        path.unlink()
    elif damage == "invalid":
        path.write_text("version: 1\ntokens: {chief-of-staff: invalid}\n")
    elif damage == "symlink":
        copy = git_repo / "temporary-hashes.yaml"
        path.rename(copy)
        path.symlink_to(copy)
    agent = "unknown-agent" if damage == "unknown-agent" else "chief-of-staff"
    assert authenticate(git_repo, agent, token) is False
    assert RecordIndex(git_repo, agent=agent, token=token).list_records() == []


def test_unknown_agent_cannot_be_provisioned(git_repo):
    before = (git_repo / ".chassis/agent-tokens.yaml").read_bytes()
    with pytest.raises(ValueError, match="Agent must exist"):
        create_agent_token(git_repo, "unknown-agent")
    assert (git_repo / ".chassis/agent-tokens.yaml").read_bytes() == before


def test_read_rechecks_identity_after_waiting_for_lock(git_repo, monkeypatch):
    from contextlib import contextmanager
    from chassis import index as module
    original = module.vault_lock

    @contextmanager
    def revoke(root):
        with original(root):
            issue(root, "chief-of-staff")
            yield

    monkeypatch.setattr(module, "vault_lock", revoke)
    assert RecordIndex(git_repo).list_records() == []
    assert not (git_repo / ".chassis/index.sqlite").exists()
