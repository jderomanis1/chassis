from conftest import assert_no_transaction_artifacts
from pathlib import Path

import pytest
from conftest import git

from chassis.errors import AuthorizationError
from chassis.index import RecordIndex
from chassis.store import RecordStore
from test_templates import EXPECTED_GTM, initiative_fields
from test_write_permissions import limit_to_ridgeview


def test_ac4_template_creation_populates_six_sections_and_commits_once(template_repo):
    before = git(template_repo, "rev-parse", "HEAD")
    policy = (template_repo / "agents.yaml").read_bytes()
    fields = initiative_fields()
    result = RecordStore(template_repo).create_from_template("initiative", "venture-acme", fields, "chief-of-staff")
    record = result["record"]
    assert tuple(line[3:] for line in record["body"].splitlines() if line.startswith("## ")) == EXPECTED_GTM
    assert all(value in record["body"] for value in fields["sections"].values())
    assert record["venture"] == record["parent"] == "venture-acme"
    assert record["version"] == 1 and record["status"] == "planned"
    assert git(template_repo, "rev-parse", "HEAD^") == before
    assert git(template_repo, "rev-parse", "HEAD") == result["commit"]
    assert git(template_repo, "show", "--format=", "--name-only") == "records/initiatives/initiative-sample-launch.md"
    assert git(template_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Homer <homer@chassis.local>"
    assert (template_repo / "agents.yaml").read_bytes() == policy
    assert RecordIndex(template_repo).get_record(record["id"]) == record
    assert git(template_repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("section", EXPECTED_GTM)
@pytest.mark.parametrize("value", [None, " \n", "{{unfinished}}"])
def test_bad_template_sections_leave_sources_index_and_head_unchanged(template_repo, section, value):
    index = RecordIndex(template_repo)
    index.rebuild()
    before, cached = git(template_repo, "rev-parse", "HEAD"), index.path.read_bytes()
    files = {p: p.read_bytes() for p in template_repo.rglob("*.md")}
    fields = initiative_fields()
    if value is None:
        del fields["sections"][section]
    else:
        fields["sections"][section] = value
    with pytest.raises(ValueError, match=section):
        RecordStore(template_repo).create_from_template("initiative", "venture-acme", fields, "chief-of-staff")
    assert {p: p.read_bytes() for p in template_repo.rglob("*.md")} == files
    assert index.path.read_bytes() == cached
    assert git(template_repo, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("template,venture,reason", [
    ("unknown", "venture-acme", "unknown template"),
    ("../agent", "venture-acme", "unknown template"),
    ("initiative", "venture-missing", "Write not permitted"),
])
def test_unknown_template_or_venture_is_rejected_without_write(template_repo, template, venture, reason):
    before = git(template_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match=reason):
        RecordStore(template_repo).create_from_template(template, venture, initiative_fields(), "chief-of-staff")
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert git(template_repo, "status", "--porcelain") == ""
    assert_no_transaction_artifacts(template_repo)


@pytest.mark.parametrize("template", ["initiative", "agent"])
@pytest.mark.parametrize("agent", ["unknown-agent", "reviewer", "limited-writer"])
def test_template_scope_denial_reads_policy_only(template_repo, monkeypatch, template, agent):
    token = limit_to_ridgeview(template_repo)
    store = RecordStore(template_repo, token=token if agent == "limited-writer" else None)
    opened, original_open = [], Path.open

    def policy_only(path, *args, **kwargs):
        assert path in {template_repo / "agents.yaml", template_repo / ".chassis/agent-tokens.yaml"}, f"Unauthorized I/O: {path}"
        opened.append(path)
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", policy_only)
        patch.setattr("chassis.store.vault_lock", lambda *_: pytest.fail("Unauthorized lock I/O"))
        patch.setattr("chassis.git.subprocess.run", lambda *a, **k: pytest.fail("Unauthorized Git I/O"))
        with pytest.raises(AuthorizationError, match="^Write not permitted$"):
            store.create_from_template(template, "venture-acme", {}, agent)
    assert opened == [template_repo / "agents.yaml"] + ([template_repo / ".chassis/agent-tokens.yaml"] if agent == "limited-writer" else [])
    assert_no_transaction_artifacts(template_repo)
