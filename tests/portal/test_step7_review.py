import os
import subprocess
import sys
from pathlib import Path

from .helpers import git
from chassis.index import RecordIndex
from chassis.portal.config import version_etag


def test_hidden_record_edits_and_commits_do_not_change_normal_viewer_etag(client, git_repo):
    before = client.get("/api/version").json()["etag"]
    path = git_repo / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text() + "\nFictional private activity.\n")
    assert client.get("/api/version").json()["etag"] == before
    git(git_repo, "add", str(path))
    git(git_repo, "commit", "-qm", "Fictional private update")
    assert client.get("/api/version").json()["etag"] == before
    assert client.get("/api/snapshot").json()["etag"] == before
    (git_repo / "README.md").write_text("Fictional documentation update.\n")
    git(git_repo, "add", "README.md")
    git(git_repo, "commit", "-qm", "Fictional docs update")
    assert client.get("/api/version").json()["etag"] == before


def test_version_is_scoped_to_configured_viewer(client, git_repo):
    privileged = RecordIndex(git_repo)
    before = version_etag(privileged)
    normal = client.get("/api/version").json()["etag"]
    assert normal != before
    path = git_repo / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text() + "\nFictional private change.\n")
    assert version_etag(privileged) != before
    assert client.get("/api/version").json()["etag"] == normal


def test_portal_conftest_import_is_independent_of_conftest_search_order():
    tests = Path(__file__).resolve().parents[1]
    code = "import sys; sys.path[:0] = sys.argv[1:]; import portal.conftest"
    result = subprocess.run([sys.executable, "-c", code, str(tests / "portal"), str(tests)],
                            env=os.environ.copy(), capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
