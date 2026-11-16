import shutil
from pathlib import Path

import pytest

from chassis.cli import main
from chassis.policy import load_policy
from chassis.validation import load_vault

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("old", "new", "reason"), [
    ("task: write", "task: admin", "task"),
    ("unknown_agent: deny", "unknown_agent: write", "unknown_agent"),
    ("version: 1", "version: true", "version"),
    ("version: 1", "version: 2", "version"),
    ("venture-acme:", "venture-missing:", "venture-missing"),
    ("venture-acme:", "task-launch-budget:", "task-launch-budget"),
    ("task: write", "task: read\n        task: write", "duplicate YAML key"),
    ("task: write", "task: !!python/object:builtins.object {}",
     "could not determine a constructor"),
])
def test_validate_rejects_invalid_policy(vault, capsys, old, new, reason):
    path = vault / "agents.yaml"
    path.write_text(path.read_text().replace(old, new), encoding="utf-8")
    with pytest.raises(ValueError, match=reason):
        load_vault(vault)
    assert main(["validate", str(vault)]) == 1
    error = capsys.readouterr().err
    assert "Read not permitted" in error or "source validation failed" in error


def test_validate_rejects_unknown_assigned_agent(vault, capsys):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("chief-of-staff", "unknown-agent"),
                    encoding="utf-8")
    assert main(["validate", str(vault)]) == 1
    error = capsys.readouterr().err
    assert "Records unavailable; source validation failed" in error
    with pytest.raises(ValueError, match="assigned_agent.*unknown-agent"):
        load_vault(vault)


def test_validate_rejects_missing_policy(vault, capsys):
    (vault / "agents.yaml").unlink()
    assert main(["validate", str(vault)]) == 1
    assert "Read not permitted" in capsys.readouterr().err
    with pytest.raises(ValueError, match="agents.yaml"):
        load_policy(vault)


def test_known_assignment_and_unassigned_records_validate(vault, capsys):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("assigned_agent: chief-of-staff",
                                            "assigned_agent: null"), encoding="utf-8")
    assert main(["validate", str(vault)]) == 0
    assert "VALID: 13 records" in capsys.readouterr().out
