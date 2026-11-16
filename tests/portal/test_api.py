import json
from datetime import datetime

from conftest import git
from test_security_cli import assert_no_leaks, restricted_terms

VENTURE_KEYS = {"id", "title", "health", "next_milestone", "milestone_due_at", "counts", "last_activity_at"}
TASK_KEYS = {"id", "title", "owner", "status", "due_at", "blocker_reason", "depends_on", "health", "last_activity_at"}


def test_snapshot_contract_and_exact_visible_counts(client):
    response = client.get("/api/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"etag", "generated_at", "ventures"}
    assert datetime.fromisoformat(data["generated_at"]).utcoffset().total_seconds() == 0
    assert [r["id"] for r in data["ventures"]] == ["venture-acme", "venture-ridgeview"]
    assert [r["counts"] for r in data["ventures"]] == [
        {"initiatives": 1, "tasks": 2, "blocked": 0, "done": 0},
        {"initiatives": 2, "tasks": 5, "blocked": 1, "done": 1}]
    for card in data["ventures"]:
        assert set(card) == VENTURE_KEYS
        assert set(card["health"]) == {"color", "reasons"}
    assert data["etag"] == client.get("/api/version").json()["etag"]


def test_venture_and_initiative_contracts_include_gtm_progress_and_tasks(client):
    response = client.get("/api/ventures/venture-acme")
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"venture", "initiatives"}
    assert data["venture"]["id"] == "venture-acme"
    assert [r["id"] for r in data["initiatives"]] == ["initiative-d2c-launch"]
    initiative = data["initiatives"][0]
    assert initiative["progress"] == {"done": 0, "total": 2}
    assert list(initiative["gtm"]) == ["Positioning", "Audience", "Channels", "Offer", "Launch checklist", "Success metrics"]
    assert initiative["gtm"]["Positioning"] == "A compact desk accessory that keeps everyday work essentials within reach."
    detail = client.get("/api/initiatives/initiative-d2c-launch").json()
    assert set(detail) == {"initiative", "tasks"}
    assert detail["initiative"] == initiative
    assert [r["id"] for r in detail["tasks"]] == ["task-audience-interviews", "task-launch-offer"]
    assert all(set(task) == TASK_KEYS for task in detail["tasks"])


def test_hidden_task_changes_no_visible_count_or_health(client, git_repo):
    before = client.get("/api/snapshot").json()["ventures"]
    path = git_repo / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("status: planned", "status: blocked\nblocker_reason: Private fictional delay\ndue_at: 2020-01-01"))
    assert client.get("/api/snapshot").json()["ventures"] == before


def test_p2_endpoints_and_errors_have_zero_restricted_content(client, git_repo):
    paths = ["/api/version", "/api/snapshot", "/api/ventures/venture-acme", "/api/ventures/venture-ridgeview",
             "/api/initiatives/initiative-d2c-launch", "/api/initiatives/initiative-maintenance",
             "/api/initiatives/initiative-resident-updates", "/api/ventures/task-launch-budget",
             "/api/initiatives/task-launch-budget"]
    responses = [client.get(path) for path in paths]
    assert [r.status_code for r in responses] == [200] * 7 + [404, 404]
    assert_no_leaks([r.text for r in responses], restricted_terms(git_repo))
    assert all(r.headers["cache-control"] == "private, no-store" for r in responses)


def test_hidden_venture_has_same_response_as_missing_venture(client, git_repo):
    path = git_repo / "records/ventures/venture-acme.md"
    path.write_text(path.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    hidden = client.get("/api/ventures/venture-acme")
    missing = client.get("/api/ventures/venture-missing")
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json() == missing.json() == {"error": {"code": "not_found", "message": "Not found"}}
    assert [v["id"] for v in client.get("/api/snapshot").json()["ventures"]] == ["venture-ridgeview"]


def test_snapshot_retries_when_commit_changes_during_read(client, git_repo, monkeypatch):
    from chassis.portal import api
    from chassis.store import RecordStore
    original, calls = api.version_etag, []

    def change(root):
        calls.append(1)
        if len(calls) == 2:
            RecordStore(root).update_record("venture-acme", {"title": "Fictional updated Acme"}, 1, "chief-of-staff")
        return original(root)

    monkeypatch.setattr(api, "version_etag", change)
    data = client.get("/api/snapshot").json()
    assert data["ventures"][0]["title"] == "Fictional updated Acme"
    assert data["etag"].startswith(git(git_repo, "rev-parse", "HEAD") + ":")
    assert len(calls) == 4
