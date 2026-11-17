import json

from starlette.testclient import TestClient

from chassis.demo import create_demo
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig
from test_security_cli import assert_no_leaks, restricted_terms


def test_demo_snapshot_and_graph_have_seven_live_ventures_and_visible_counts_only(tmp_path):
    root = tmp_path / "demo"
    credentials = create_demo(root)["credentials"]
    config = PortalConfig(root, viewer_token=credentials["reviewer"])
    with TestClient(create_app(config), base_url="http://127.0.0.1:8765") as client:
        snapshot = client.get("/api/snapshot").json()
        assert [v["id"] for v in snapshot["ventures"]] == ["venture-acme", "venture-atlas", "venture-cedar",
            "venture-juniper", "venture-lumen", "venture-northwind", "venture-ridgeview"]
        assert {v["health"]["color"] for v in snapshot["ventures"]} == {"green", "yellow", "red"}
        assert sum(v["counts"]["tasks"] for v in snapshot["ventures"]) == 41
        assert snapshot["ventures"][0]["counts"]["tasks"] == 5
        graph = client.get("/api/graph").json()
        assert len(graph["nodes"]) == 62
        assert {"from": "task-ridgeview-operations-3", "to": "task-atlas-launch-3", "blocking": True} in graph["edges"]
        outputs = [json.dumps(snapshot), json.dumps(graph)]
        for venture in snapshot["ventures"]:
            response = client.get(f'/api/ventures/{venture["id"]}')
            assert response.status_code == 200
            outputs.append(response.text)
        assert_no_leaks(outputs, restricted_terms(root))
