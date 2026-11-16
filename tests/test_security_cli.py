import json
import os
import subprocess
import sys

from conftest import issue
from chassis.markdown import read_record


def restricted_terms(root):
    item = read_record(root / "records/tasks/task-launch-budget.md")
    return [item.record.id, item.record.title, item.record.owner, item.body]


def assert_no_leaks(outputs, terms):
    text = "\n".join(outputs)
    for term in terms:
        assert term not in text
        assert json.dumps(term, ensure_ascii=False)[1:-1] not in text


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
