import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from conftest import git
from mcp_client import StdioClient
from test_creates import new_task
from test_mcp_stdio import TOOLS
from test_templates import initiative_fields


def assert_commit(root, before, result, relative):
    assert "error" not in result, result
    commit = result["commit"]
    assert git(root, "rev-parse", "HEAD") == commit
    assert git(root, "rev-list", "--parents", "-n", "1", commit).split() == [commit, before]
    assert git(root, "show", "--format=", "--name-only", commit) == relative
    assert git(root, "show", "-s", "--format=%an <%ae>", commit) == "Fictional Homer <homer@chassis.local>"


def snapshot(root):
    cache = root / ".chassis/index.sqlite"
    return ({p.relative_to(root).as_posix(): p.read_bytes() for p in (root / "records").rglob("*.md")},
            git(root, "rev-parse", "HEAD"), cache.read_bytes() if cache.exists() else None)


def assert_lock_released(root):
    # The stable inode intentionally remains. Removing it races other waiters.
    with (root / ".chassis/write.lock").open("rb") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (root / ".git/index.lock").exists()
    assert list((root / "records").rglob("*.tmp")) == []


def test_real_stdio_session_all_six_tools(template_repo):
    root = template_repo
    start = git(root, "rev-parse", "HEAD")
    with StdioClient(root) as client:
        assert client.initialize()["serverInfo"]["name"] == "Chassis"
        assert sorted(t["name"] for t in client.request("tools/list")["tools"]) == TOOLS
        listed = client.call("list_records", {"filters": {"status": "blocked", "venture": "venture-ridgeview"}})
        assert [r["id"] for r in listed["records"]] == ["task-maintenance-plan"]
        assert listed["records"][0]["blocker_reason"] == (
            "Waiting for the fictional estimate comparison before drafting the sequence.")
        original = client.call("read_record", {"id": "task-launch-budget"})["record"]
        assert original["version"] == 1
        assert original["last_activity_at"] == datetime.fromisoformat(
            git(root, "log", "-1", "--format=%cI", "--", "records/tasks/task-launch-budget.md")
        ).astimezone(timezone.utc).isoformat()
        found = client.call("search", {"query": "three most repeated"})
        assert [r["id"] for r in found["records"]] == ["task-audience-interviews"]

        created = client.call("create_record", {"type": "task", "fields": new_task(root, assigned_agent="reviewer")})
        assert_commit(root, start, created, "records/tasks/task-fictional-new.md")
        assert created["record"]["version"] == 1
        templated = client.call("create_from_template", {"template": "initiative", "venture": "venture-acme",
                                                         "fields": initiative_fields()})
        assert_commit(root, created["commit"], templated, "records/initiatives/initiative-sample-launch.md")
        assert tuple(line[3:] for line in templated["record"]["body"].splitlines() if line.startswith("## ")) == (
            "Positioning", "Audience", "Channels", "Offer", "Launch checklist", "Success metrics")
        updated = client.call("update_record", {"id": original["id"], "expected_version": 1, "changes": {
            "status": "blocked", "blocker_reason": "Waiting for fictional review", "due_at": "2026-12-01"}})
        assert_commit(root, templated["commit"], updated, "records/tasks/task-launch-budget.md")
        assert updated["record"]["version"] == 2
        assert client.call("read_record", {"id": original["id"]})["record"] == updated["record"]

        before = snapshot(root)
        stale = client.call("update_record", {"id": original["id"], "expected_version": 1,
                                               "changes": {"next_step": "Stale fictional attempt"}})
        assert stale["error"] == "conflict" and stale["current_version"] == 2
        assert stale["expected_version"] == 1 and snapshot(root) == before
        invalid = client.call("update_record", {"id": original["id"], "expected_version": 2,
                                                 "changes": {"due_at": "2026-02-30"}})
        assert invalid["error"] == "validation" and invalid["field"] == "due_at"
        assert invalid["reason"] == "Value error, day is out of range for month"
        assert snapshot(root) == before
        missing = client.call("read_record", {"id": "missing-id"})
        assert missing["error"] == "not_found"
    assert git(root, "rev-list", "--count", f"{start}..HEAD") == "3"
    assert git(root, "status", "--porcelain") == ""
    assert_lock_released(root)
    logs = "".join(client.stderr_lines)
    assert all("Calling " + name in logs for name in TOOLS)
    assert "Chassis stdio server stopped" in logs
    if destination := os.environ.get("CHASSIS_MCP_TRANSCRIPT"):
        Path(destination).write_text("".join(json.dumps(line, ensure_ascii=False) + "\n"
                                            for line in client.transcript), encoding="utf-8")
