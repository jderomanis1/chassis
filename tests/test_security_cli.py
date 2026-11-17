import json
import os
import subprocess
import sys

import pytest

from conftest import issue
from chassis.markdown import read_record


def restricted_terms(root):
    item = read_record(root / "records/tasks/task-launch-budget.md")
    return [item.record.id, item.record.title, item.record.owner, item.body]


def leak_patterns(terms):
    expanded = list(terms)
    for line in terms[-1].splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ">", "Parent:")):
            fragment = " ".join(line.split()[:8])
            if len(fragment) >= 20:
                expanded.append(fragment)
                break
    return list(dict.fromkeys(value for term in expanded for value in
                             (term, json.dumps(term, ensure_ascii=False)[1:-1])))


def assert_no_leaks(outputs, terms):
    text = "\n".join(outputs)
    for pattern in leak_patterns(terms):
        assert pattern not in text


def test_all_cli_record_outputs_hide_restricted_values_and_counts(git_repo):
    token = issue(git_repo, "reviewer")
    env = os.environ | {"CHASSIS_AGENT_ID": "reviewer", "CHASSIS_AGENT_TOKEN": token}
    commands = [("list",), ("list", "--sensitivity", "restricted"),
        ("get", "task-launch-budget"), ("get", "missing-id"), ("get", "venture-acme"),
        ("index", "rebuild"), ("validate", str(git_repo)),
        ("update", "task-launch-budget", "--expected-version", "1", "--changes", "{}"),
        ("create", "task", "--fields", "{}"),
        ("new", "initiative", "--venture", "venture-acme", "--fields", "{}"),
        ("commit-human", "records/tasks/task-launch-budget.md")]
    commands += [("search", term) for term in restricted_terms(git_repo)]
    results = [subprocess.run([sys.executable, "-m", "chassis.cli", *args], cwd=git_repo,
                             env=env, capture_output=True, text=True) for args in commands]
    assert len(json.loads(results[0].stdout)) == 12
    assert results[1].stdout.strip() == "[]"
    assert results[2].stderr == results[3].stderr
    assert "INDEXED: 12 records" in results[5].stdout
    assert "VALID: 12 records" in results[6].stdout
    assert_no_leaks([part for result in results for part in (result.stdout, result.stderr)],
                    restricted_terms(git_repo))


@pytest.mark.parametrize("source_damage", ["schema", "graph"])
def test_cli_hidden_source_errors_do_not_reveal_record_content(template_repo, source_damage):
    from test_read_error_safety import normal_writer, damage_hidden_record, create_arguments, template_arguments

    root = template_repo
    terms = restricted_terms(root)
    token = normal_writer(root)
    if source_damage == "schema":
        damage_hidden_record(root, terms[0])
    else:
        path = root / "records/tasks/task-launch-budget.md"
        path.write_text(path.read_text().replace("parent: initiative-d2c-launch", "parent: task-launch-offer"))
    env = os.environ | {"CHASSIS_AGENT_ID": "normal-writer", "CHASSIS_AGENT_TOKEN": token}
    commands = [("list",), ("get", "venture-acme"), ("search", "fictional"),
        ("validate", str(root)), ("index", "rebuild"),
        ("update", "task-launch-offer", "--expected-version", "1", "--changes", "{}"),
        ("create", "task", "--fields", json.dumps(create_arguments(root)["fields"])),
        ("new", "initiative", "--venture", "venture-acme", "--fields", json.dumps(template_arguments()["fields"])),
        ("commit-human", "records/tasks/task-launch-offer.md")]
    results = [subprocess.run([sys.executable, "-m", "chassis.cli", *args], cwd=root,
                             env=env, capture_output=True, text=True) for args in commands]
    assert [result.returncode for result in results] == [1] * len(commands)
    assert all("Records unavailable; source validation failed" in result.stderr for result in results)
    assert_no_leaks([part for result in results for part in (result.stdout, result.stderr)], terms)
