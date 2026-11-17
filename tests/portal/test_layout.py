import json
from contextlib import contextmanager
from dataclasses import replace

import pytest
import yaml
from starlette.testclient import TestClient

from chassis.portal.app import create_app
from .helpers import git, issue
from .test_write_guard import editor_config, writer

EMPTY = {"positions": {}, "collapsed": [], "hidden": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}
LAYOUT = {"positions": {"task-launch-offer": {"x": 421.5, "y": -95}},
          "collapsed": ["initiative-d2c-launch"], "hidden": ["task-audience-interviews"],
          "viewport": {"x": 20, "y": -30, "zoom": 0.8}}


def test_layout_roundtrip_is_per_viewer_atomic_and_not_a_record_commit(writer, editor_config):
    root = editor_config.root
    before = git(root, "rev-parse", "HEAD")
    assert writer.get("/api/layout").json() == EMPTY
    response = writer.put("/api/layout", json=LAYOUT)
    assert response.status_code == 200 and response.json() == LAYOUT
    assert writer.get("/api/layout").json() == LAYOUT
    path = root / ".chassis/layout/reviewer.json"
    assert json.loads(path.read_text()) == LAYOUT
    assert git(root, "check-ignore", str(path)) == str(path)
    assert git(root, "rev-parse", "HEAD") == before
    assert not list(path.parent.glob("*.tmp"))
    other = replace(editor_config, allow_writes=False, viewer_agent="chief-of-staff",
                    viewer_token=issue(root, "chief-of-staff"))
    with TestClient(create_app(other), base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/layout").json() == EMPTY


def test_invisible_ids_are_removed_before_disk_and_response(writer, editor_config):
    hidden = "task-launch-budget"
    malicious = {"positions": {hidden: {"x": 1, "y": 2}, "task-missing": {"x": 2, "y": 3}},
                 "collapsed": [hidden], "hidden": [hidden], "viewport": EMPTY["viewport"]}
    response = writer.put("/api/layout", json=malicious)
    assert response.status_code == 200 and response.json() == EMPTY
    path = editor_config.root / ".chassis/layout/reviewer.json"
    assert hidden not in path.read_text()
    assert hidden not in writer.get("/api/layout").text
    # Old local state from a previously visible record is filtered on every read.
    path.write_text(json.dumps(malicious))
    assert writer.get("/api/layout").json() == EMPTY
    assert hidden not in path.read_text()
    assert "task-missing" not in path.read_text()


def test_newly_restricted_parent_removes_descendant_positions(writer, editor_config):
    assert writer.put("/api/layout", json=LAYOUT).status_code == 200
    path = editor_config.root / "records/initiatives/initiative-d2c-launch.md"
    path.write_text(path.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    expected = EMPTY | {"viewport": LAYOUT["viewport"]}
    assert writer.get("/api/layout").json() == expected
    assert writer.put("/api/layout", json=LAYOUT).json() == expected
    assert "task-launch-offer" not in (editor_config.root / ".chassis/layout/reviewer.json").read_text()


@pytest.mark.parametrize("contents", ["{", "[]", '{"positions":null}', "x" * 65537,
    '{"viewport":{"x":0,"y":0,"zoom":0}}'])
def test_corrupt_layout_is_empty(writer, editor_config, contents):
    path = editor_config.root / ".chassis/layout/reviewer.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    assert writer.get("/api/layout").json() == EMPTY
    assert path.read_text() == contents


@pytest.mark.parametrize("payload", [{"positions": {"../policy": {"x": 1, "y": 2}}},
    {"positions": {"task-launch-offer": {"x": "1", "y": 2}}},
    {"positions": {"task-launch-offer": {"x": 1000001, "y": 2}}},
    {"viewport": {"x": 0, "y": 0, "zoom": 0}}, {"agent": "chief-of-staff"}])
def test_invalid_layout_does_not_create_file(writer, editor_config, payload):
    assert writer.put("/api/layout", json=payload).status_code == 400
    assert not (editor_config.root / ".chassis/layout/reviewer.json").exists()


@pytest.mark.parametrize("kind", ["directory", "file"])
def test_layout_symlinks_never_read_or_write_the_destination(writer, editor_config, tmp_path, kind):
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = outside / "reviewer.json"
    destination.write_text(json.dumps(LAYOUT))
    directory = editor_config.root / ".chassis/layout"
    if kind == "directory":
        directory.symlink_to(outside, target_is_directory=True)
    else:
        directory.mkdir()
        (directory / "reviewer.json").symlink_to(destination)
    assert writer.get("/api/layout").status_code == 500
    assert writer.put("/api/layout", json=EMPTY).status_code == 500
    assert json.loads(destination.read_text()) == LAYOUT


def test_layout_checks_credentials_again_inside_vault_lock(writer, editor_config, monkeypatch):
    from chassis.portal import layout
    real_lock = layout.vault_lock
    @contextmanager
    def revoke(root):
        issue(root, "canvas-editor")
        with real_lock(root):
            yield
    monkeypatch.setattr(layout, "vault_lock", revoke)
    assert writer.put("/api/layout", json=LAYOUT).status_code == 404
    assert not (editor_config.root / ".chassis/layout/reviewer.json").exists()


def test_layout_uses_same_write_guard(writer, editor_config):
    del writer.headers["Origin"]
    assert writer.put("/api/layout", json=LAYOUT).status_code == 403
    assert not (editor_config.root / ".chassis/layout/reviewer.json").exists()
