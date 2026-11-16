import pytest
from conftest import git

from chassis import store as store_module
from chassis.store import RecordStore
from test_templates import initiative_fields


@pytest.mark.parametrize("field,value", [
    ("owner", None), ("owner", "  "), ("owner", 7),
    ("sensitivity", "secret"), ("sensitivity", None),
    ("assigned_agent", "Bad ID"), ("assigned_agent", "unknown-agent"),
    ("assigned_agent", False),
])
def test_template_metadata_is_validated_before_expansion(template_repo, monkeypatch, field, value):
    before = git(template_repo, "rev-parse", "HEAD")
    monkeypatch.setattr(store_module, "expand_template",
                        lambda *_: pytest.fail("Invalid metadata reached template expansion"))
    with pytest.raises(ValueError, match=field):
        RecordStore(template_repo).create_from_template(
            "initiative", "venture-acme", initiative_fields() | {field: value}, "chief-of-staff")
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert git(template_repo, "status", "--porcelain") == ""
    assert not (template_repo / ".chassis").exists()


def test_valid_template_metadata_uses_record_constraints(template_repo):
    result = RecordStore(template_repo).create_from_template(
        "initiative", "venture-acme", initiative_fields() | {
            "owner": "  Fictional Owner  ", "sensitivity": "restricted",
            "assigned_agent": "chief-of-staff"}, "chief-of-staff")
    assert result["record"]["owner"] == "Fictional Owner"
    assert result["record"]["sensitivity"] == "restricted"
    assert result["record"]["assigned_agent"] == "chief-of-staff"


@pytest.mark.parametrize("value", [
    "FIXME", "xxx", "Fixme: finish the offer", "ＦＩＸＭＥ", "ＸＸＸ", "ＴＯＤＯ",
    "𝑇𝐵𝐷", "｛｛Offer｝｝", "［ｉｎｓｅｒｔ text］", "＜replace text＞",
])
def test_nfkc_placeholder_markers_never_create_a_record(template_repo, value):
    fields = initiative_fields()
    fields["sections"]["Offer"] = value
    before = git(template_repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="Offer.*placeholder"):
        RecordStore(template_repo).create_from_template(
            "initiative", "venture-acme", fields, "chief-of-staff")
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert git(template_repo, "status", "--porcelain") == ""
    assert not (template_repo / ".chassis").exists()
