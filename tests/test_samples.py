from collections import Counter
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
    assert policy["unknown_agent"] == "deny"


def test_ridgeview_has_five_tasks_and_two_dependencies():
    records = load_vault(ROOT)
    tasks = [item.record for item in records.values()
             if item.record.venture == "venture-ridgeview" and item.record.type == "task"]
    assert len(tasks) == 5
    edges = {(task.id, dependency) for task in tasks for dependency in task.depends_on}
    assert edges == {("task-maintenance-quotes", "task-maintenance-inventory"),
                     ("task-maintenance-plan", "task-maintenance-quotes")}
    assert all(task.sensitivity == "normal" for task in tasks)


def test_complete_sample_counts_and_assignment():
    records = load_vault(ROOT)
    assert Counter(item.record.type for item in records.values()) == {
        "venture": 2, "initiative": 3, "task": 8}
    assert sum(len(item.record.depends_on) for item in records.values()) == 2
    acme = [item.record for item in records.values() if item.record.venture == "venture-acme"]
    assert Counter(item.type for item in acme) == {"venture": 1, "initiative": 1, "task": 3}
    assert all(item.record.assigned_agent == "chief-of-staff" for item in records.values())


def test_restricted_sample_is_explicitly_fictional():
    records = load_vault(ROOT)
    restricted = [item for item in records.values() if item.record.sensitivity == "restricted"]
    assert len(restricted) == 1
    assert restricted[0].record.id == "task-launch-budget"
    assert "Fictional sample" in restricted[0].body
