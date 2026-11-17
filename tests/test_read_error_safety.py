import json

import pytest
import yaml

from conftest import git, issue
from chassis.errors import AuthorizationError
from chassis.markdown import RecordFileError, read_record
from chassis.store import RecordStore
from chassis.templates import GTM_SECTIONS
from chassis.tool_handlers import ToolHandlers
from test_security_cli import assert_no_leaks, restricted_terms


def damage_hidden_record(root, private_key):
    path = root / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("version: 1\n", "version: 1\n" + json.dumps(private_key) + ": true\n"))


def normal_writer(root):
    path = root / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["normal-writer"] = {"ventures": {venture: {kind: "write" for kind in grants}
        for venture, grants in policy["agents"]["reviewer"]["ventures"].items()}}
    path.write_text(yaml.safe_dump(policy))
    return issue(root, "normal-writer")


def create_arguments(root):
    record = read_record(root / "records/tasks/task-launch-offer.md").record
    fields = record.model_dump(mode="json", exclude={"version", "updated_at", "type"})
    return {"type": "task", "fields": fields | {"id": "task-public-probe"}}


def template_arguments():
    return {"template": "initiative", "venture": "venture-acme", "fields": {
        "id": "initiative-public-probe", "title": "Fictional public plan", "owner": "Fictional Reviewer",
        "next_step": "Review the sample plan.", "sections": {key: "Fictional plan for this section." for key in GTM_SECTIONS}}}


def test_hidden_source_validation_cause_is_not_exposed_by_tool_mapping(git_repo):
    terms = restricted_terms(git_repo)
    damage_hidden_record(git_repo, terms[0])
    handlers = ToolHandlers(git_repo, "reviewer", token=issue(git_repo, "reviewer"))
    results = [handlers.call(name, args) for name, args in [
        ("list_records", {}), ("read_record", {"id": "venture-acme"}), ("search", {"query": "fictional"})]]
    assert_no_leaks([json.dumps(result) for result in results], terms)
    assert results == [{"error": "validation", "field": field,
                        "reason": "Records unavailable; source validation failed"}
                       for field in ["filters", "record", "record"]]


@pytest.mark.parametrize("operation", ["update", "create", "template", "commit-human"])
@pytest.mark.parametrize("source_damage", ["schema", "graph"])
def test_write_validation_of_other_hidden_sources_is_generic(template_repo, monkeypatch, operation, source_damage):
    root = template_repo
    terms = restricted_terms(root)
    token = normal_writer(root)
    monkeypatch.setenv("CHASSIS_AGENT_ID", "normal-writer")
    monkeypatch.setenv("CHASSIS_AGENT_TOKEN", token)
    if source_damage == "schema":
        damage_hidden_record(root, terms[0])
    else:
        path = root / "records/tasks/task-launch-budget.md"
        path.write_text(path.read_text().replace("parent: initiative-d2c-launch", "parent: task-launch-offer"))
    store = RecordStore(root, token=token)
    before = git(root, "rev-parse", "HEAD")
    with pytest.raises(RecordFileError, match="^Records unavailable; source validation failed$") as error:
        if operation == "update":
            store.update_record("task-launch-offer", {"title": "Fictional updated offer"}, 1, "normal-writer")
        elif operation == "create":
            args = create_arguments(root)
            store.create_record(args["type"], args["fields"], "normal-writer")
        elif operation == "template":
            args = template_arguments()
            store.create_from_template(args["template"], args["venture"], args["fields"], "normal-writer")
        else:
            store.commit_human("records/tasks/task-launch-offer.md")
    assert error.value.__cause__ is None
    assert_no_leaks([str(error.value)], terms)
    assert git(root, "rev-parse", "HEAD") == before


def test_unreadable_target_frontmatter_does_not_reveal_unauthorized_path(git_repo):
    token = normal_writer(git_repo)
    path = git_repo / "records/tasks/task-launch-budget.md"
    path.write_text("---\nsensitivity: [\n---\nFictional private body.\n")
    with pytest.raises(AuthorizationError, match="^Write not permitted$"):
        RecordStore(git_repo, token=token).update_record("task-launch-budget", {}, 1, "normal-writer")
