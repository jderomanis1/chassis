import json

import pytest
from conftest import git

from test_agent_templates import agent_fields, agent_repo
from test_index_cli import cli
from test_templates import initiative_fields


@pytest.mark.parametrize("template", ["initiative", "agent"])
def test_cli_new_uses_one_attributed_create_with_explicit_vault(agent_repo, tmp_path, template):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    fields = initiative_fields() if template == "initiative" else agent_fields()
    before = git(agent_repo, "rev-parse", "HEAD")
    result = cli(elsewhere, "new", template, "--venture", "venture-acme", "--fields", json.dumps(fields),
                 "--vault", str(agent_repo))
    assert result.returncode == 0 and result.stderr == b""
    payload = json.loads(result.stdout)
    assert payload["record"]["type"] == template and payload["record"]["version"] == 1
    assert payload["record"]["venture"] == payload["record"]["parent"] == "venture-acme"
    assert git(agent_repo, "rev-parse", "HEAD^") == before
    assert git(agent_repo, "rev-parse", "HEAD") == payload["commit"]
    assert git(agent_repo, "show", "--format=", "--name-only") == f"records/{template}s/{fields['id']}.md"
    assert git(agent_repo, "show", "-s", "--format=%an <%ae>") == "Fictional Homer <homer@chassis.local>"
    assert json.loads(cli(agent_repo, "get", fields["id"]).stdout) == payload["record"]
    listing = cli(agent_repo, "list", "--type", template)
    assert listing.returncode == 0 and fields["id"] in [r["id"] for r in json.loads(listing.stdout)]


@pytest.mark.parametrize("agent", [None, "reviewer", "unknown-agent"])
def test_cli_new_requires_configured_authorized_caller(template_repo, monkeypatch, agent):
    if agent is None:
        monkeypatch.delenv("CHASSIS_AGENT_ID")
    else:
        monkeypatch.setenv("CHASSIS_AGENT_ID", agent)
    before = git(template_repo, "rev-parse", "HEAD")
    result = cli(template_repo, "new", "initiative", "--venture", "venture-acme", "--fields", "{}")
    assert result.returncode == 1 and result.stdout == b""
    assert json.loads(result.stderr)["error"] == "unauthorized"
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert not (template_repo / ".chassis").exists()


@pytest.mark.parametrize("arguments,code,reason", [
    (("unknown", "--venture", "venture-acme", "--fields", "{}"), 2, b"invalid choice: 'unknown'"),
    (("initiative", "--fields", "{}"), 2, b"--venture"),
    (("initiative", "--venture", "venture-acme", "--fields", "{"), 1, b"INVALID"),
    (("initiative", "--venture", "venture-acme", "--fields", "{}"), 1, b"Positioning"),
])
def test_cli_new_refusals_are_actionable_and_do_not_write(template_repo, arguments, code, reason):
    before = git(template_repo, "rev-parse", "HEAD")
    result = cli(template_repo, "new", *arguments)
    assert result.returncode == code and result.stdout == b""
    assert reason in result.stderr and b"Traceback" not in result.stderr
    assert git(template_repo, "rev-parse", "HEAD") == before
    assert git(template_repo, "status", "--porcelain") == ""
    assert not (template_repo / ".chassis").exists()
