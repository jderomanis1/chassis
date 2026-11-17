import shutil
from pathlib import Path

import pytest
from portal.helpers import EphemeralToken, git, issue

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_IDS = [
    "initiative-d2c-launch", "initiative-maintenance", "initiative-resident-updates",
    "task-audience-interviews", "task-launch-budget", "task-launch-offer",
    "task-maintenance-inventory", "task-maintenance-plan", "task-maintenance-quotes",
    "task-resident-bulletin", "task-resident-faq", "venture-acme", "venture-ridgeview",
]


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """An isolated copy of the fictional vault, with no generated index."""
    shutil.copytree(ROOT / "records", tmp_path / "records")
    shutil.copyfile(ROOT / "agents.yaml", tmp_path / "agents.yaml")
    monkeypatch.setenv("CHASSIS_AGENT_ID", "chief-of-staff")
    monkeypatch.setenv("CHASSIS_AGENT_TOKEN", issue(tmp_path, "chief-of-staff"))
    return tmp_path


def assert_no_transaction_artifacts(root):
    assert not (root / ".chassis/index.sqlite").exists()
    assert not (root / ".chassis/write.lock").exists()


@pytest.fixture
def git_repo(vault, monkeypatch):
    for role, name, email in [("AGENT", "Fictional Homer", "homer@chassis.local"),
                              ("HUMAN", "Fictional Human", "human@chassis.local")]:
        monkeypatch.setenv(f"CHASSIS_{role}_NAME", name)
        monkeypatch.setenv(f"CHASSIS_{role}_EMAIL", email)
    monkeypatch.setenv("CHASSIS_AGENT_ID", "chief-of-staff")
    (vault / ".gitignore").write_text(".chassis/\n")
    git(vault, "init", "-q", "--initial-branch=main")
    git(vault, "config", "user.name", "Fictional Fixture")
    git(vault, "config", "user.email", "fixture@chassis.local")
    git(vault, "config", "commit.gpgsign", "false")
    git(vault, "add", ".")
    git(vault, "commit", "-qm", "Fictional baseline")
    return vault


@pytest.fixture
def template_repo(git_repo):
    shutil.copytree(ROOT / "templates", git_repo / "templates")
    git(git_repo, "add", "templates")
    git(git_repo, "commit", "-qm", "Fictional template baseline")
    return git_repo
