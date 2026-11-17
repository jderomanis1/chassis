from datetime import date

from starlette.testclient import TestClient

from conftest import issue
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig


def test_health_uses_frozen_clock_and_only_viewer_visible_children(git_repo, portal_config):
    path = git_repo / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("status: planned", "status: blocked\nblocker_reason: Fictional private delay"))
    for agent, config, expected, count in [
        ("normal", portal_config, {"color": "green", "reasons": ["on_track"]}, 2),
        ("restricted", PortalConfig(git_repo, viewer_agent="chief-of-staff", viewer_token=issue(git_repo, "chief-of-staff")),
         {"color": "red", "reasons": ["blocked"]}, 3),
    ]:
        with TestClient(create_app(config, clock=lambda: date(2026, 11, 16)), base_url="http://127.0.0.1:8765") as client:
            venture = client.get("/api/snapshot").json()["ventures"][0]
            assert venture["health"] == expected, agent
            assert venture["counts"]["tasks"] == count, agent
            data = client.get("/api/initiatives/initiative-d2c-launch").json()
            assert data["initiative"]["health"] == expected, agent
            assert data["initiative"]["progress"] == {"done": 0, "total": count}, agent
