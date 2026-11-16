from pathlib import Path

import pytest
import yaml
from conftest import git

from chassis import store as store_module
from chassis.errors import AuthorizationError
from chassis.store import RecordStore
from test_creates import new_task


@pytest.mark.parametrize("agent", ["unknown-agent", "reviewer"])
@pytest.mark.parametrize("operation", ["update-normal", "update-restricted", "create"])
def test_denied_callers_perform_only_policy_read_no_record_index_git_or_lock_io(git_repo, monkeypatch,
                                                                              agent, operation):
    store = RecordStore(git_repo)
    fields = new_task(git_repo)
    files = {path: path.read_bytes() for path in (git_repo / "records").rglob("*.md")}
    before = git(git_repo, "rev-parse", "HEAD")
    opened, original_open = [], Path.open

    def policy_only(path, *args, **kwargs):
        assert path == git_repo / "agents.yaml", f"Unexpected record/index I/O: {path}"
        opened.append(path)
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", policy_only)
        patch.setattr(store_module, "vault_lock", lambda *_: pytest.fail("Unexpected lock I/O"))
        patch.setattr("chassis.git.subprocess.run", lambda *a, **k: pytest.fail("Unexpected Git I/O"))
        with pytest.raises(AuthorizationError, match=f"{agent}.*write grant"):
            if operation == "create":
                store.create_record("task", fields, agent)
            else:
                identifier = "task-launch-budget" if operation.endswith("restricted") else "task-launch-offer"
                store.update_record(identifier, {"assigned_agent": "chief-of-staff"}, 1, agent)
    assert opened == [git_repo / "agents.yaml"]
    assert not (git_repo / ".chassis").exists()
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert {path: path.read_bytes() for path in files} == files


def limit_to_ridgeview(root):
    path = root / "agents.yaml"
    policy = yaml.safe_load(path.read_text())
    policy["agents"]["limited-writer"] = {"ventures": {
        "venture-ridgeview": {"task": "write"}, "venture-acme": {"task": "read"}}}
    path.write_text(yaml.safe_dump(policy))


@pytest.mark.parametrize("operation", ["update-normal", "update-restricted", "create", "move"])
def test_scoped_denials_never_open_a_lock_index_or_git(git_repo, monkeypatch, operation):
    limit_to_ridgeview(git_repo)
    store, fields = RecordStore(git_repo), new_task(git_repo)
    before = git(git_repo, "rev-parse", "HEAD")
    files = {path: path.read_bytes() for path in (git_repo / "records").rglob("*.md")}
    with monkeypatch.context() as patch:
        patch.setattr(store_module, "vault_lock", lambda *_: pytest.fail("Denied scope must precede lock I/O"))
        patch.setattr("chassis.git.subprocess.run", lambda *a, **k: pytest.fail("Unexpected Git I/O"))
        with pytest.raises(AuthorizationError, match="venture-acme/task"):
            if operation == "create":
                store.create_record("task", fields, "limited-writer")
            elif operation == "move":
                store.update_record("task-resident-faq", {"venture": "venture-acme",
                    "parent": "initiative-d2c-launch"}, 1, "limited-writer")
            else:
                identifier = "task-launch-budget" if operation.endswith("restricted") else "task-launch-offer"
                store.update_record(identifier, {"status": "done"}, 1, "limited-writer")
    assert not (git_repo / ".chassis").exists()
    assert git(git_repo, "rev-parse", "HEAD") == before
    assert {path: path.read_bytes() for path in files} == files
