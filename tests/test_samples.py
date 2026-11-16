from pathlib import Path

import yaml

from chassis.validation import load_vault

ROOT = Path(__file__).resolve().parents[1]


def test_seed_ventures_and_hoa_initiatives():
    records = load_vault(ROOT)
    expected = {"venture-ridgeview", "venture-acme", "initiative-maintenance",
                "initiative-resident-updates"}
    assert expected <= records.keys()
    assert records["venture-ridgeview"].record.title == "Ridgeview HOA"
    assert records["venture-acme"].record.title == "Acme D2C"
    assert all("Fictional sample" in records[key].body for key in expected)


def test_agents_file_has_explicit_venture_and_type_scopes():
    policy = yaml.safe_load((ROOT / "agents.yaml").read_text(encoding="utf-8"))
    chief = policy["agents"]["chief-of-staff"]["ventures"]
    assert set(chief) == {"venture-ridgeview", "venture-acme"}
    assert all(scopes == {"venture": "write", "initiative": "write", "task": "write"}
               for scopes in chief.values())
    assert policy["unknown_agent"] == "read"


def test_ridgeview_has_five_tasks_and_two_dependencies():
    records = load_vault(ROOT)
    tasks = [item.record for item in records.values()
             if item.record.venture == "venture-ridgeview" and item.record.type == "task"]
    assert len(tasks) == 5
    edges = {(task.id, dependency) for task in tasks for dependency in task.depends_on}
    assert edges == {("task-maintenance-quotes", "task-maintenance-inventory"),
                     ("task-maintenance-plan", "task-maintenance-quotes")}
    assert all(task.sensitivity == "normal" for task in tasks)
