import shutil

import pytest
from conftest import ROOT

from chassis import templates

EXPECTED_GTM = ("Positioning", "Audience", "Channels", "Offer", "Launch checklist", "Success metrics")


def initiative_fields():
    return {"id": "initiative-sample-launch", "title": "Fictional desk-kit pilot",
            "owner": "Avery Quinn", "next_step": "Review the fictional launch plan.",
            "sections": dict(zip(EXPECTED_GTM, (
                "A compact kit for a small desk.", "Fictional remote workers with small desks.",
                "A draft product page and an opt-in sample email.", "One illustrative starter kit.",
                "- [ ] Review ten fictional interviews.\n- [ ] Check the draft offer.",
                "Sample targets: ten interviews and three expressions of interest.")))}


@pytest.fixture
def template_root(tmp_path):
    shutil.copytree(ROOT / "templates", tmp_path / "templates")
    return tmp_path


def test_initiative_template_has_exact_filled_gtm_sections_in_order(template_root):
    assert templates.GTM_SECTIONS == EXPECTED_GTM
    fields = initiative_fields()
    expanded = templates.expand_template(template_root, "initiative", fields)
    body = expanded["body"]
    assert tuple(line[3:] for line in body.splitlines() if line.startswith("## ")) == EXPECTED_GTM
    assert all(value in body for value in fields["sections"].values())
    assert "{{" not in body and expanded["status"] == "planned"
    assert "sections" not in expanded and "body" not in fields


@pytest.mark.parametrize("section", EXPECTED_GTM)
@pytest.mark.parametrize("value", [None, "", " \n\t", "{{value}}", "TBD", "TODO: fill this", "[insert text]"])
def test_missing_empty_and_placeholder_sections_are_rejected(template_root, section, value):
    fields = initiative_fields()
    if value is None:
        del fields["sections"][section]
    else:
        fields["sections"][section] = value
    with pytest.raises(ValueError, match=section):
        templates.expand_template(template_root, "initiative", fields)


@pytest.mark.parametrize("old,new", [("## Offer", "## Other"), ("{{Offer}}", "{{unknown}}")])
def test_damaged_template_is_rejected(template_root, old, new):
    path = template_root / "templates/initiative.md"
    path.write_text(path.read_text().replace(old, new))
    with pytest.raises(ValueError, match="template|placeholder"):
        templates.expand_template(template_root, "initiative", initiative_fields())
