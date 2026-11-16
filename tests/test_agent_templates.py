import shutil

import pytest
import yaml
from conftest import ROOT, git

from chassis.errors import AuthorizationError
from chassis.index import RecordIndex
from chassis.policy import authorize_writer, load_policy
from chassis.store import RecordStore
from chassis.templates import expand_template


def agent_fields():
    return {"id": "agent-sample-reader", "title": "Fictional launch reviewer",
            "owner": "Morgan Vale", "next_step": "Review the fictional playbook.",
            "sections": {"Playbooks": "Summarize open tasks and surface blockers.",
                         "Channels": "Local Markdown reports only.",
                         "Data scope": "Fictional Acme records for review."}}


@pytest.fixture
def agent_repo(git_repo):
    shutil.copytree(ROOT / "templates", git_repo / "templates")
    path = git_repo / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    # Human provisioning permits the existing writer to author agent documents.
    policy["agents"]["chief-of-staff"]["ventures"]["venture-acme"]["agent"] = "write"
    path.write_text(yaml.safe_dump(policy))
    git(git_repo, "add", "templates", "agents.yaml")
    git(git_repo, "commit", "-qm", "Fictional human permits agent documents")
    return git_repo


def test_agent_document_created_from_template_grants_no_access(agent_repo):
    policy_bytes = (agent_repo / "agents.yaml").read_bytes()
    fields = expand_template(agent_repo, "agent", agent_fields()) | {
        "venture": "venture-acme", "parent": "venture-acme"}
    result = RecordStore(agent_repo).create_record("agent", fields, "chief-of-staff")
    assert "## Permissions\nRead-only by default." in result["record"]["body"]
    assert result["record"]["type"] == "agent" and result["record"]["assigned_agent"] is None
    assert git(agent_repo, "show", "--format=", "--name-only") == "records/agents/agent-sample-reader.md"
    policy = load_policy(agent_repo)
    assert policy.unknown_agent == "read" and "agent-sample-reader" not in policy.agents
    with pytest.raises(AuthorizationError, match="agent-sample-reader.*no write grant"):
        authorize_writer(agent_repo, "agent-sample-reader")
    assert (agent_repo / "agents.yaml").read_bytes() == policy_bytes
    assert RecordIndex(agent_repo).get_record("agent-sample-reader") == result["record"]


@pytest.mark.parametrize("override", ["section", "template"])
def test_agent_template_permissions_cannot_be_overridden(agent_repo, override):
    fields = agent_fields()
    if override == "section":
        fields["sections"]["Permissions"] = "write"
    else:
        path = agent_repo / "templates/agent.md"
        path.write_text(path.read_text().replace("Read-only by default.", "Write access by default."))
    with pytest.raises(ValueError, match="section|permissions"):
        expand_template(agent_repo, "agent", fields)


def test_agent_documents_use_the_existing_update_and_human_commit_paths(agent_repo):
    store = RecordStore(agent_repo)
    fields = expand_template(agent_repo, "agent", agent_fields()) | {
        "venture": "venture-acme", "parent": "venture-acme"}
    store.create_record("agent", fields, "chief-of-staff")
    assert store.update_record(fields["id"], {"status": "in_progress"}, 1, "chief-of-staff")["record"]["version"] == 2
    relative = "records/agents/agent-sample-reader.md"
    path = agent_repo / relative
    path.write_text(path.read_text() + "\nHuman-reviewed fictional playbook.\n")
    assert store.commit_human(relative)["path"] == relative
    assert [r["id"] for r in RecordIndex(agent_repo).list_records({"type": "agent"})] == [fields["id"]]
