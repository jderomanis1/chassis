import pytest
import yaml
from conftest import git

from chassis import store as store_module
from chassis.errors import AuthorizationError
from chassis.store import RecordStore
from test_templates import initiative_fields


@pytest.mark.parametrize("tail", ["", "Static text under the wrong field."])
def test_template_tokens_must_fill_their_own_sections(template_repo, tail):
    path = template_repo / "templates/initiative.md"
    path.write_text(path.read_text().replace("## Success metrics\n{{Success metrics}}",
                                            "{{Success metrics}}\n\n## Success metrics\n" + tail))
    before = git(template_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="Success metrics|section"):
        RecordStore(template_repo).create_from_template("initiative", "venture-acme", initiative_fields(), "chief-of-staff")
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert not (template_repo / ".chassis").exists()


@pytest.mark.parametrize("value", ["1. \n2. ", "- [ ]\n- [x]", "<!-- draft note -->"])
def test_markup_only_sections_are_empty(template_repo, value):
    fields = initiative_fields()
    fields["sections"]["Launch checklist"] = value
    with pytest.raises(ValueError, match="Launch checklist.*empty"):
        RecordStore(template_repo).create_from_template("initiative", "venture-acme", fields, "chief-of-staff")
    assert git(template_repo, "status", "--porcelain") == ""
    assert not (template_repo / ".chassis").exists()


@pytest.mark.parametrize("extra", [{"body": "Bypassed content"}, {"parent": "venture-ridgeview"},
                                   {"permissions": "write"}, {"grants": {"task": "write"}}])
def test_template_fields_cannot_bypass_content_scope_or_grants(template_repo, extra):
    policy = (template_repo / "agents.yaml").read_bytes()
    before = git(template_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match=next(iter(extra))):
        RecordStore(template_repo).create_from_template(
            "initiative", "venture-acme", initiative_fields() | extra, "chief-of-staff")
    assert (template_repo / "agents.yaml").read_bytes() == policy
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert git(template_repo, "status", "--porcelain") == ""
    assert not (template_repo / ".chassis").exists()


def test_template_creation_rechecks_policy_after_expansion(template_repo, monkeypatch):
    expand = store_module.expand_template
    before = git(template_repo, "rev-parse", "HEAD")

    def revoke_after_expansion(*args):
        expanded = expand(*args)
        path = template_repo / "agents.yaml"
        path.write_text(path.read_text().replace("initiative: write", "initiative: read"))
        return expanded

    monkeypatch.setattr(store_module, "expand_template", revoke_after_expansion)
    monkeypatch.setattr(store_module, "vault_lock", lambda *_: pytest.fail("Revoked grant reached lock"))
    with pytest.raises(AuthorizationError, match="venture-acme/initiative"):
        RecordStore(template_repo).create_from_template("initiative", "venture-acme", initiative_fields(), "chief-of-staff")
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert not (template_repo / "records/initiatives/initiative-sample-launch.md").exists()


def test_missing_venture_cannot_be_created_even_with_an_invalid_policy_grant(template_repo):
    path = template_repo / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["chief-of-staff"]["ventures"]["venture-missing"] = {"initiative": "write"}
    path.write_text(yaml.safe_dump(policy))
    before = git(template_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="venture-missing.*existing venture"):
        RecordStore(template_repo).create_from_template("initiative", "venture-missing", initiative_fields(), "chief-of-staff")
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert not (template_repo / "records/initiatives/initiative-sample-launch.md").exists()
    assert not (template_repo / ".chassis/index.sqlite").exists()
