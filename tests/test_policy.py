import shutil
from pathlib import Path

import pytest

from chassis.cli import main

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def vault(tmp_path):
    shutil.copytree(ROOT / "records", tmp_path / "records")
    shutil.copyfile(ROOT / "agents.yaml", tmp_path / "agents.yaml")
    return tmp_path


@pytest.mark.parametrize(("old", "new", "reason"), [
    ("task: write", "task: admin", "task"),
    ("unknown_agent: read", "unknown_agent: write", "unknown_agent"),
    ("version: 1", "version: true", "version"),
    ("version: 1", "version: 2", "version"),
    ("task: write", "task: read\n        task: write", "duplicate YAML key"),
    ("task: write", "task: !!python/object:builtins.object {}",
     "could not determine a constructor"),
])
def test_validate_rejects_invalid_policy(vault, capsys, old, new, reason):
    path = vault / "agents.yaml"
    path.write_text(path.read_text().replace(old, new), encoding="utf-8")
    assert main(["validate", str(vault)]) == 1
    error = capsys.readouterr().err
    assert "agents.yaml" in error and reason in error


def test_validate_rejects_unknown_assigned_agent(vault, capsys):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("chief-of-staff", "unknown-agent"),
                    encoding="utf-8")
    assert main(["validate", str(vault)]) == 1
    error = capsys.readouterr().err
    assert path.name in error and "assigned_agent" in error and "unknown-agent" in error


def test_validate_rejects_missing_policy(vault, capsys):
    (vault / "agents.yaml").unlink()
    assert main(["validate", str(vault)]) == 1
    assert "agents.yaml" in capsys.readouterr().err


def test_known_assignment_and_unassigned_records_validate(vault, capsys):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("assigned_agent: chief-of-staff",
                                            "assigned_agent: null"), encoding="utf-8")
    assert main(["validate", str(vault)]) == 0
    assert "VALID: 13 records" in capsys.readouterr().out
