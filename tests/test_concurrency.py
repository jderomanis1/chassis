import json
import os
import subprocess
import sys

from conftest import git

from chassis.atomic import vault_lock
from chassis.index import RecordIndex
from chassis.markdown import read_record
from chassis.store import RecordStore

TARGET = "records/tasks/task-launch-budget.md"
WRITER = """
import json, sys
from pathlib import Path
from chassis.errors import ConflictError
from chassis.store import RecordStore
store = RecordStore(Path(sys.argv[1]))
print('ready', flush=True)
sys.stdin.readline()
try:
    result = store.update_record('task-launch-budget', {'status': sys.argv[2]}, 1, 'chief-of-staff')
except ConflictError as error:
    print(json.dumps({'outcome': 'conflict', **error.as_dict()}), flush=True)
    sys.exit(3)
print(json.dumps({'outcome': 'ok', **result}), flush=True)
"""


def test_ac3_two_real_processes_same_version_have_one_winner_and_one_commit(git_repo):
    before = git(git_repo, "rev-parse", "HEAD")
    processes = []
    try:
        with vault_lock(git_repo):
            for label, status in (("A", "blocked"), ("B", "done")):
                env = os.environ | {"CHASSIS_AGENT_NAME": f"Fictional Writer {label}",
                                    "CHASSIS_AGENT_EMAIL": f"writer-{label.lower()}@chassis.local"}
                process = subprocess.Popen([sys.executable, "-c", WRITER, str(git_repo), status],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, env=env)
                processes.append((label, status, process))
            for _, _, process in processes:
                assert process.stdout.readline().strip() == "ready"
                process.stdin.write("go\n")
                process.stdin.flush()
        results = []
        for label, status, process in processes:
            out, err = process.communicate(timeout=20)
            assert err == ""
            result = json.loads(out)
            assert process.returncode == (0 if result["outcome"] == "ok" else 3)
            results.append((label, status, result))
    finally:
        for _, _, process in processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
    assert sorted(result["outcome"] for _, _, result in results) == ["conflict", "ok"]
    label, status, winner = next(row for row in results if row[2]["outcome"] == "ok")
    loser = next(row[2] for row in results if row[2]["outcome"] == "conflict")
    assert loser["expected_version"] == 1 and loser["current_version"] == 2
    assert git(git_repo, "rev-list", "--count", f"{before}..HEAD") == "1"
    assert git(git_repo, "rev-parse", "HEAD") == winner["commit"]
    assert git(git_repo, "show", "--format=", "--name-only", "HEAD") == TARGET
    assert git(git_repo, "show", "-s", "--format=%an") == f"Fictional Writer {label}"
    source = read_record(git_repo / TARGET)
    assert source.record.status == status and source.record.version == 2
    assert RecordIndex(git_repo).get_record(source.record.id) == winner["record"]
    committed = subprocess.check_output(["git", "-C", str(git_repo), "show", f"HEAD:{TARGET}"])
    assert (git_repo / TARGET).read_bytes() == committed


def test_process_crash_before_replace_preserves_source_head_cache_and_releases_lock(git_repo):
    index = RecordIndex(git_repo)
    index.rebuild()
    path = git_repo / TARGET
    original, cached = path.read_bytes(), index.path.read_bytes()
    before = git(git_repo, "rev-parse", "HEAD")
    crashed = subprocess.run([sys.executable, "-c", """
import os, sys
from pathlib import Path
from chassis import atomic
from chassis.store import RecordStore
atomic.os.replace = lambda *args: os._exit(73)
RecordStore(Path(sys.argv[1])).update_record('task-launch-budget', {'status': 'blocked'}, 1, 'chief-of-staff')
""", str(git_repo)], capture_output=True, timeout=20)
    assert crashed.returncode == 73
    assert path.read_bytes() == original and index.path.read_bytes() == cached
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert read_record(path).record.version == 1
    result = RecordStore(git_repo).update_record("task-launch-budget", {"status": "done"}, 1, "chief-of-staff")
    assert result["record"]["version"] == 2  # Kernel released the crashed process's lock.
