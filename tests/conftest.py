import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def vault(tmp_path):
    """An isolated copy of the fictional vault, with no generated index."""
    shutil.copytree(ROOT / "records", tmp_path / "records")
    shutil.copyfile(ROOT / "agents.yaml", tmp_path / "agents.yaml")
    return tmp_path
