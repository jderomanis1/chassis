import hashlib

from starlette.testclient import TestClient

from chassis.portal import app
from test_security_cli import assert_no_leaks, restricted_terms


def test_static_mount_uses_package_assets_and_never_the_vault(portal_config, tmp_path, monkeypatch):
    assets = tmp_path / "package-assets"
    assets.mkdir()
    (assets / "app.css").write_text("/* Fictional test asset */")
    monkeypatch.setattr(app, "ASSET_ROOT", assets)
    with TestClient(app.create_app(portal_config), base_url="http://127.0.0.1:8765") as client:
        response = client.get("/app.css")
        assert response.status_code == 200
        assert response.text == "/* Fictional test asset */"
        assert response.headers["content-type"].startswith("text/css")
        assert response.headers["cache-control"] == "private, no-store"
        assert client.post("/app.css").status_code == 405
        for path in ["/records/tasks/task-launch-budget.md", "/agents.yaml", "/.chassis/agent-tokens.yaml", "/api/ask"]:
            denied = client.get(path)
            assert denied.status_code == 404
            assert denied.json() == {"error": {"code": "not_found", "message": "Not found"}}
            assert_no_leaks([denied.text], restricted_terms(portal_config.root))


def test_boot_serves_the_approved_intro(client):
    page = client.get("/")
    assert 'src="/intro.mp3"' in page.text
    response = client.get("/intro.mp3")
    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "audio/mpeg"
    assert hashlib.sha256(response.content).hexdigest() == (
        "a6d1543544c714477fab343472d58b5ed07aea358d6bb0a9aea63724b1318a42"
    )
