import hashlib
import json
import secrets

import pytest
import yaml

from chassis.errors import AuthorizationError
from chassis.index import RecordIndex
from chassis.store import RecordStore

RESTRICTED = "task-launch-budget"


from conftest import issue


@pytest.fixture
def secured(git_repo):
    path = git_repo / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["unknown_agent"] = "deny"
    policy["agents"]["chief-of-staff"]["clearance"] = "restricted"
    policy["agents"]["scoped-reader"] = {"ventures": {
        "venture-ridgeview": {"venture": "read", "initiative": "read", "task": "read"}}}
    path.write_text(yaml.safe_dump(policy))
    return git_repo, {agent: issue(git_repo, agent) for agent in policy["agents"]}


@pytest.mark.parametrize("agent,credential", [("", "valid"), ("unknown-agent", "valid"),
    ("reviewer", "missing"), ("reviewer", "wrong")])
def test_unknown_empty_missing_and_wrong_token_get_nothing(secured, agent, credential):
    root, tokens = secured
    token = tokens["reviewer"] if credential == "valid" else (
        "" if credential == "missing" else secrets.token_urlsafe(32))
    index = RecordIndex(root, agent=agent, token=token)
    assert index.list_records() == []
    assert index.get_record("venture-acme") is None
    assert index.search("fictional") == []
    with pytest.raises(AuthorizationError, match="Write not permitted"):
        RecordStore(root, token=token).update_record(RESTRICTED, {}, 1, agent)


def test_normal_clearance_has_no_restricted_row_count_or_search_hit(secured):
    root, tokens = secured
    index = RecordIndex(root, agent="reviewer", token=tokens["reviewer"])
    assert len(index.list_records()) == 12
    assert len(index.list_records({"venture": "venture-acme", "type": "task"})) == 2
    assert index.list_records({"sensitivity": "restricted"}) == []
    assert index.get_record(RESTRICTED) is None
    assert index.get_record("missing-id") is None
    assert index.search("Set the internal launch test budget") == []


def test_clearance_and_venture_grant_are_both_required(secured):
    root, tokens = secured
    index = RecordIndex(root, agent="chief-of-staff", token=tokens["chief-of-staff"])
    assert index.get_record(RESTRICTED)["id"] == RESTRICTED
    scoped = RecordIndex(root, agent="scoped-reader", token=tokens["scoped-reader"])
    assert {r["venture"] for r in scoped.list_records()} == {"venture-ridgeview"}
    assert scoped.get_record("venture-acme") is None
    path = root / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["scoped-reader"]["clearance"] = "restricted"
    path.write_text(yaml.safe_dump(policy))
    assert scoped.get_record(RESTRICTED) is None


def test_hidden_references_and_descendants_are_removed_in_library(secured):
    root, tokens = secured
    task = root / "records/tasks/task-launch-offer.md"
    task.write_text(task.read_text().replace("depends_on: []", f"depends_on: [{RESTRICTED}]"))
    index = RecordIndex(root, agent="reviewer", token=tokens["reviewer"])
    assert index.get_record("task-launch-offer")["depends_on"] == []
    assert RESTRICTED not in json.dumps(index.list_records())
    graph = index.graph("venture-acme")
    assert len(graph["nodes"]) == 4
    assert graph["edges"] == []
    assert RESTRICTED not in json.dumps(graph)
    parent = root / "records/initiatives/initiative-d2c-launch.md"
    parent.write_text(parent.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    assert index.list_records({"venture": "venture-acme", "type": "task"}) == []


def test_revoked_token_and_clearance_take_effect_on_next_read(secured):
    root, tokens = secured
    index = RecordIndex(root, agent="chief-of-staff", token=tokens["chief-of-staff"])
    assert index.get_record(RESTRICTED)["id"] == RESTRICTED
    path = root / "agents.yaml"
    path.write_text(path.read_text().replace("clearance: restricted", "clearance: normal"))
    assert index.get_record(RESTRICTED) is None
    issue(root, "chief-of-staff")
    assert index.list_records() == []


def test_audit_logs_one_event_per_operation_with_no_bodies_or_tokens(secured):
    root, tokens = secured
    index = RecordIndex(root, agent="reviewer", token=tokens["reviewer"])
    index.list_records()
    index.get_record(RESTRICTED)
    index.search("fictional")
    with pytest.raises(AuthorizationError):
        RecordStore(root, token=tokens["reviewer"]).update_record(RESTRICTED, {}, 1, "reviewer")
    text = (root / ".chassis/audit.jsonl").read_text()
    entries = [json.loads(line) for line in text.splitlines()]
    assert [e["tool"] for e in entries] == ["list_records", "read_record", "search", "update_record"]
    assert [e["outcome"] for e in entries] == ["ok", "not_found", "ok", "unauthorized"]
    assert entries[0]["count"] == 12
    assert entries[1]["record_ids"] == []
    assert {e["agent_id"] for e in entries} == {"reviewer"}
    assert all(e["time"].endswith("+00:00") for e in entries)
    assert all(token not in text for token in tokens.values())
    assert RESTRICTED not in text
    assert "body" not in text


def test_restricted_write_and_missing_write_share_generic_error(secured):
    root, tokens = secured
    path = root / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["scoped-reader"]["ventures"]["venture-ridgeview"]["task"] = "write"
    path.write_text(yaml.safe_dump(policy))
    store = RecordStore(root, token=tokens["scoped-reader"])
    errors = []
    for identifier in (RESTRICTED, "missing-id"):
        with pytest.raises(AuthorizationError) as exc:
            store.update_record(identifier, {}, 1, "scoped-reader")
        errors.append(exc.value.as_dict())
    assert errors == [{"error": "unauthorized", "message": "Write not permitted"}] * 2


def test_normal_writer_cannot_read_or_declassify_restricted_record(secured):
    root, tokens = secured
    path = root / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["reviewer"]["ventures"]["venture-acme"]["task"] = "write"
    path.write_text(yaml.safe_dump(policy))
    store = RecordStore(root, token=tokens["reviewer"])
    for changes in ({}, {"sensitivity": "normal"}):
        with pytest.raises(AuthorizationError, match="^Write not permitted$"):
            store.update_record(RESTRICTED, changes, 1, "reviewer")


def test_audit_records_successful_write_once(secured):
    root, tokens = secured
    result = RecordStore(root, token=tokens["chief-of-staff"]).update_record(
        "task-launch-offer", {"next_step": "Fictional audit proof"}, 1, "chief-of-staff")
    entries = [json.loads(line) for line in (root / ".chassis/audit.jsonl").read_text().splitlines()]
    assert len(entries) == 1
    assert entries[0]["record_ids"] == [result["record"]["id"]]
    assert entries[0]["outcome"] == "ok"
    assert "Fictional audit proof" not in json.dumps(entries)
