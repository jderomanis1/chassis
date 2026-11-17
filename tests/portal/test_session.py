import json

from starlette.testclient import TestClient

from chassis.portal.app import create_app
from chassis.store import RecordStore
from test_security_cli import assert_no_leaks, restricted_terms
from .helpers import EphemeralToken


def test_session_contract_token_is_ephemeral_and_no_credential_is_disclosed(client, portal_config):
    response = client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"csrf", "writes_enabled", "viewer"}
    csrf = EphemeralToken(data["csrf"])
    assert len(csrf) == 43 and data["writes_enabled"] is False
    assert data["viewer"] == "reviewer"
    assert portal_config.viewer_token not in response.text
    assert client.get("/api/session").json()["csrf"] == csrf
    assert response.headers["cache-control"] == "private, no-store"
    assert "access-control-allow-origin" not in response.headers
    with TestClient(create_app(portal_config), base_url="http://127.0.0.1:8765") as next_launch:
        assert next_launch.get("/api/session").json()["csrf"] != csrf
    events = [json.loads(line) for line in (portal_config.root / ".chassis/audit.jsonl").read_text().splitlines()]
    assert [(e["tool"], e["outcome"]) for e in events] == [("session", "ok")] * 3
    assert all(not e["record_ids"] for e in events)
    for path in portal_config.root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            assert csrf.encode() not in path.read_bytes(), path.name
    assert_no_leaks([response.text], restricted_terms(portal_config.root))


def test_every_record_projection_exposes_its_actual_version_and_editable_next_step(client, git_repo):
    store = RecordStore(git_repo)
    for identifier in ["venture-acme", "initiative-d2c-launch", "task-launch-offer"]:
        store.update_record(identifier, {"next_step": "Review the revised fictional plan."}, 1, "chief-of-staff")
    versions = {r["id"]: r["version"] for r in client.app.state.index.list_records()}
    snapshot = client.get("/api/snapshot").json()["ventures"]
    detail = client.get("/api/ventures/venture-acme").json()
    initiative = client.get("/api/initiatives/initiative-d2c-launch").json()
    graph = client.get("/api/graph").json()["nodes"]
    records = [*snapshot, detail["venture"], *detail["initiatives"], initiative["initiative"], *initiative["tasks"], *graph]
    assert all(r["version"] == versions[r["id"]] for r in records)
    assert {versions[key] for key in ["venture-acme", "initiative-d2c-launch", "task-launch-offer"]} == {2}
    task = next(r for r in initiative["tasks"] if r["id"] == "task-launch-offer")
    assert task["next_step"] == "Review the revised fictional plan."
    assert_no_leaks([json.dumps(records)], restricted_terms(git_repo))
