from conftest import assert_no_transaction_artifacts
import pytest

from chassis.errors import AuthorizationError, ConflictError
from chassis.policy import authorize_writer, require_grant


@pytest.mark.parametrize("agent", ["unknown-agent", "reviewer"])
def test_unknown_and_read_only_callers_are_denied_after_policy_read(vault, monkeypatch, agent):
    from pathlib import Path

    original = Path.open
    opened = []

    def policy_only(path, *args, **kwargs):
        opened.append(path)
        assert path == vault / "agents.yaml"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", policy_only)
    with pytest.raises(AuthorizationError, match="^Write not permitted$") as error:
        authorize_writer(vault, agent)
    assert error.value.as_dict()["error"] == "unauthorized"
    assert opened == [vault / "agents.yaml"]
    assert_no_transaction_artifacts(vault)


@pytest.mark.parametrize("damage", ["missing", "invalid"])
def test_missing_or_invalid_policy_denies_writes(vault, damage):
    path = vault / "agents.yaml"
    if damage == "missing":
        path.unlink()
    else:
        path.write_text("version: 1\nunknown_agent: write\nagents: {}\n")
    with pytest.raises(AuthorizationError, match="^Write not permitted$"):
        authorize_writer(vault, "chief-of-staff")


def test_scope_is_exact_and_policy_is_reloaded(vault):
    policy = authorize_writer(vault, "chief-of-staff")
    require_grant(policy, "chief-of-staff", "venture-acme", "task")
    with pytest.raises(AuthorizationError, match="^Write not permitted$"):
        require_grant(policy, "chief-of-staff", "venture-missing", "task")
    path = vault / "agents.yaml"
    path.write_text(path.read_text().replace("task: write", "task: read"))
    fresh = authorize_writer(vault, "chief-of-staff")
    with pytest.raises(AuthorizationError, match="^Write not permitted$"):
        require_grant(fresh, "chief-of-staff", "venture-acme", "task")
    require_grant(fresh, "chief-of-staff", "venture-acme", "initiative")


def test_conflict_is_structured_and_includes_current_version():
    error = ConflictError("task-launch-budget", 1, 2)
    assert error.as_dict() == {
        "error": "conflict", "message": "task-launch-budget: expected version 1; current version 2",
        "id": "task-launch-budget", "expected_version": 1, "current_version": 2,
    }
