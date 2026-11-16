import json
import subprocess
import sys
from conftest import SAMPLE_IDS


def cli(vault, *args):
    return subprocess.run([sys.executable, "-m", "chassis.cli", *args],
                          cwd=vault, capture_output=True)


def test_cli_queries_are_byte_identical_after_delete_and_rebuild(vault):
    sources = {path: path.read_bytes() for path in vault.rglob("*.md")}
    policy = (vault / "agents.yaml").read_bytes()
    rebuilt = cli(vault, "index", "rebuild")
    assert rebuilt.returncode == 0 and b"INDEXED: 13 records" in rebuilt.stdout
    commands = [("list",), ("list", "--type", "task", "--venture", "venture-acme",
        "--status", "planned", "--parent", "initiative-d2c-launch",
        "--assigned-agent", "chief-of-staff", "--sensitivity", "restricted"),
        ("list", "--parent", "null"), ("get", "task-launch-budget"),
        ("search", "three most repeated"), ("search", "zz-no-match-zz")]
    before = [cli(vault, *command) for command in commands]
    assert all(result.returncode == 0 and result.stderr == b"" for result in before)
    assert [item["id"] for item in json.loads(before[0].stdout)] == SAMPLE_IDS
    assert [item["id"] for item in json.loads(before[1].stdout)] == ["task-launch-budget"]
    assert [item["id"] for item in json.loads(before[2].stdout)] == ["venture-acme", "venture-ridgeview"]
    assert json.loads(before[3].stdout)["sensitivity"] == "restricted"
    assert json.loads(before[4].stdout)[0]["id"] == "task-audience-interviews"
    assert json.loads(before[5].stdout) == []
    (vault / ".chassis/index.sqlite").unlink()
    assert cli(vault, "index", "rebuild").returncode == 0
    after = [cli(vault, *command) for command in commands]
    assert all(result.returncode == 0 and result.stderr == b"" for result in after)
    assert [result.stdout for result in after] == [result.stdout for result in before]
    assert {path: path.read_bytes() for path in sources} == sources
    assert (vault / "agents.yaml").read_bytes() == policy


def test_cli_automatic_index_and_actionable_invalid_record(vault):
    assert cli(vault, "get", "venture-acme").returncode == 0
    assert (vault / ".chassis/index.sqlite").is_file()
    before = (vault / ".chassis/index.sqlite").read_bytes()
    (vault / "records/tasks/broken.md").write_text("invalid record", encoding="utf-8")
    result = cli(vault, "list")
    assert result.returncode == 1 and result.stdout == b""
    assert result.stderr == b"INVALID: Records unavailable; source validation failed\n"
    assert b"Traceback" not in result.stderr
    assert (vault / ".chassis/index.sqlite").read_bytes() == before


def test_cli_missing_id_has_nonzero_exit_and_no_json(vault):
    result = cli(vault, "get", "missing-id")
    assert result.returncode == 1 and result.stdout == b""
    assert json.loads(result.stderr) == {"error": "not_found", "message": "Record not found"}


def test_cli_null_assignment_and_explicit_vault(vault):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("assigned_agent: chief-of-staff",
                                            "assigned_agent: null"), encoding="utf-8")
    elsewhere = vault / "elsewhere"
    elsewhere.mkdir()
    result = cli(elsewhere, "list", "--vault", str(vault), "--assigned-agent", "null")
    assert result.returncode == 0
    assert [item["id"] for item in json.loads(result.stdout)] == ["task-launch-budget"]


def test_cli_rejects_invalid_status(vault):
    result = cli(vault, "list", "--status", "invalid")
    assert result.returncode == 2
    assert b"--status" in result.stderr and b"invalid choice" in result.stderr
