import hashlib
import json
import os
import subprocess
import sys
from collections import Counter

import pytest
import yaml

from conftest import ROOT, git
from chassis.errors import AuthorizationError
from chassis.identity import authenticate
from chassis.index import RecordIndex
from chassis.policy import load_policy
from chassis.store import RecordStore
from chassis.validation import load_vault

VENTURES = {"Ridgeview HOA", "Acme D2C", "Cedar Rentals", "Lumen Skincare",
            "Atlas Trades", "Northwind Reno", "Juniper Events"}


def test_demo_cli_creates_valid_fictional_vault_and_preserves_existing_fixtures(tmp_path):
    originals = {p: p.read_bytes() for p in (ROOT / "records").rglob("*.md")}
    originals[ROOT / "agents.yaml"] = (ROOT / "agents.yaml").read_bytes()
    root = tmp_path / "demo"
    result = subprocess.run([sys.executable, "-m", "chassis.cli", "demo-init", str(root)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert set(data) == {"vault", "credentials"}
    assert data["vault"] == str(root)
    assert set(data["credentials"]) == {"reviewer", "canvas-editor", "chief-of-staff"}
    records = [item.record for item in load_vault(root).values()]
    assert Counter(r.type for r in records) == {"venture": 7, "initiative": 14, "task": 42}
    assert {r.title for r in records if r.type == "venture"} == VENTURES
    assert {r.status for r in records} == {"done", "in_progress", "blocked", "planned"}
    for venture in (r for r in records if r.type == "venture"):
        initiatives = [r for r in records if r.parent == venture.id]
        assert len(initiatives) == 2
        assert all(len([r for r in records if r.parent == i.id]) == 3 for i in initiatives)
    assert [r.id for r in records if r.sensitivity == "restricted"] == ["task-launch-budget"]
    by_id = {r.id: r for r in records}
    assert [(r.id, dep) for r in records for dep in r.depends_on if r.venture != by_id[dep].venture] == [
        ("task-atlas-launch-3", "task-ridgeview-operations-3")]
    env = os.environ | {"CHASSIS_AGENT_ID": "chief-of-staff", "CHASSIS_AGENT_TOKEN": data["credentials"]["chief-of-staff"]}
    check = subprocess.run([sys.executable, "-m", "chassis.cli", "validate", str(root)], env=env,
                           capture_output=True, text=True, timeout=20)
    assert check.returncode == 0 and check.stderr == ""
    assert check.stdout == "VALID: 63 records | 7 ventures | 14 initiatives | 42 tasks | 29 dependencies\n"
    assert git(root, "rev-list", "--count", "HEAD") == "1"
    assert git(root, "status", "--porcelain") == ""
    assert git(root, "log", "-1", "--format=%an <%ae>") == "Chassis Demo <demo@chassis.local>"
    assert all(p.read_bytes() == content for p, content in originals.items())
    tracked = git(root, "ls-files").splitlines()
    history = git(root, "log", "--all", "-p", "--format=fuller")
    token_path = root / ".chassis/agent-tokens.yaml"
    hashes = yaml.safe_load(token_path.read_text())["tokens"]
    assert token_path.stat().st_mode & 0o777 == 0o600
    assert all(not p.startswith(".chassis/") for p in tracked)
    for agent, token in data["credentials"].items():
        assert authenticate(root, agent, token)
        assert hashes[agent] == hashlib.sha256(token.encode()).hexdigest()
        assert token not in history and token not in result.stderr
        assert result.stdout.count(token) == 1
        assert all(token.encode() not in p.read_bytes() for p in (root / ".chassis").rglob("*") if p.is_file())


def test_demo_agents_are_separate_normal_viewer_editor_and_privileged_chief(tmp_path, monkeypatch):
    from chassis.demo import create_demo

    root = tmp_path / "demo"
    data = create_demo(root)
    credentials = data["credentials"]
    policy = load_policy(root)
    assert policy.unknown_agent == "deny"
    assert policy.agents["reviewer"].clearance == policy.agents["canvas-editor"].clearance == "normal"
    assert policy.agents["chief-of-staff"].clearance == "restricted"
    for agent, permission in [("reviewer", "read"), ("canvas-editor", "write"), ("chief-of-staff", "write")]:
        scopes = policy.agents[agent].ventures
        assert len(scopes) == 7
        assert all(grants == {"venture": permission, "initiative": permission, "task": permission} for grants in scopes.values())
        index = RecordIndex(root, agent=agent, token=credentials[agent])
        assert len(index.list_records()) == (63 if agent == "chief-of-staff" else 62)
    monkeypatch.setenv("CHASSIS_AGENT_NAME", "canvas-editor")
    monkeypatch.setenv("CHASSIS_AGENT_EMAIL", "canvas-editor@chassis.local")
    store = RecordStore(root, token=credentials["canvas-editor"])
    result = store.update_record("task-ridgeview-launch-2", {"status": "in_progress", "blocker_reason": None}, 1, "canvas-editor")
    assert result["record"]["version"] == 2
    assert git(root, "log", "-1", "--format=%an") == "canvas-editor"
    before = git(root, "rev-parse", "HEAD")
    with pytest.raises(AuthorizationError, match="Write not permitted"):
        store.update_record("task-launch-budget", {"title": "Denied fictional edit"}, 1, "canvas-editor")
    assert git(root, "rev-parse", "HEAD") == before
    second = create_demo(tmp_path / "second")["credentials"]
    assert all(second[agent] != token for agent, token in credentials.items())


@pytest.mark.parametrize("symlink", [False, True])
def test_demo_init_never_overwrites_an_existing_destination(tmp_path, symlink):
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("Existing work")
    root = tmp_path / "link" if symlink else target
    if symlink:
        root.symlink_to(target, target_is_directory=True)
    result = subprocess.run([sys.executable, "-m", "chassis.cli", "demo-init", str(root)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 1 and result.stdout == ""
    assert "destination must not already exist" in result.stderr
    assert sentinel.read_text() == "Existing work" and sorted(p.name for p in target.iterdir()) == ["keep.txt"]
