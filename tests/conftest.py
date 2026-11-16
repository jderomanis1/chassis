import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_IDS = [
    "initiative-d2c-launch", "initiative-maintenance", "initiative-resident-updates",
    "task-audience-interviews", "task-launch-budget", "task-launch-offer",
    "task-maintenance-inventory", "task-maintenance-plan", "task-maintenance-quotes",
    "task-resident-bulletin", "task-resident-faq", "venture-acme", "venture-ridgeview",
]


@pytest.fixture
def vault(tmp_path):
    """An isolated copy of the fictional vault, with no generated index."""
    shutil.copytree(ROOT / "records", tmp_path / "records")
    shutil.copyfile(ROOT / "agents.yaml", tmp_path / "agents.yaml")
    return tmp_path
