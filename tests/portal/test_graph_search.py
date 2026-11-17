from starlette.testclient import TestClient

from .helpers import issue
from chassis.portal.app import create_app
from chassis.portal.config import PortalConfig
from test_security_cli import assert_no_leaks, restricted_terms


def test_neutral_graph_contract_counts_and_dependency_direction(client):
    response = client.get("/api/graph")
    assert response.status_code == 200
    graph = response.json()
    assert set(graph) == {"nodes", "edges"}
    assert len(graph["nodes"]) == 12
    assert all(set(node) == {"id", "type", "parent", "status", "health", "version"} for node in graph["nodes"])
    assert all(set(node["health"]) == {"color", "reasons"} for node in graph["nodes"])
    assert graph["edges"] == [
        {"from": "task-maintenance-quotes", "to": "task-maintenance-plan", "blocking": True},
        {"from": "task-maintenance-inventory", "to": "task-maintenance-quotes", "blocking": False}]
    acme = client.get("/api/graph", params={"venture": "venture-acme"}).json()
    assert [n["id"] for n in acme["nodes"]] == ["initiative-d2c-launch", "task-audience-interviews",
                                                "task-launch-offer", "venture-acme"]
    assert acme["edges"] == []
    assert client.get("/api/graph?venture=").json() == graph


def test_search_contract_literal_matching_empty_query_and_restricted_queries(client, git_repo):
    response = client.get("/api/search", params={"q": "THREE MOST REPEATED"})
    assert response.status_code == 200
    assert response.json() == {"hits": [{"id": "task-audience-interviews", "type": "task",
                                        "title": "Summarize the sample audience interviews"}]}
    assert client.get("/api/search").json() == {"hits": []}
    assert client.get("/api/search", params={"q": "%_"}).json() == {"hits": []}
    for term in restricted_terms(git_repo):
        assert client.get("/api/search", params={"q": term}).json() == {"hits": []}


def test_all_endpoint_outputs_have_zero_restricted_values_and_no_hidden_total(client, git_repo):
    paths = ["/api/version", "/api/snapshot", "/api/ventures/venture-acme", "/api/ventures/venture-ridgeview",
             "/api/initiatives/initiative-d2c-launch", "/api/initiatives/initiative-maintenance",
             "/api/initiatives/initiative-resident-updates", "/api/graph", "/api/graph?venture=venture-acme",
             "/api/graph?venture=venture-ridgeview", "/api/search?q=fictional"]
    responses = [client.get(path) for path in paths]
    assert [r.status_code for r in responses] == [200] * len(paths)
    assert_no_leaks([r.text for r in responses], restricted_terms(git_repo))
    cards = responses[1].json()["ventures"]
    assert sum(c["counts"]["tasks"] for c in cards) == 7
    assert sum(c["counts"]["initiatives"] for c in cards) == 3
    assert len(responses[7].json()["nodes"]) == 12
    assert responses[4].json()["initiative"]["progress"]["total"] == 2


def test_graph_hidden_dependency_has_no_edge_or_waiting_reason(client, git_repo):
    path = git_repo / "records/tasks/task-launch-offer.md"
    path.write_text(path.read_text().replace("depends_on: []", "depends_on: [task-launch-budget]"))
    response = client.get("/api/graph?venture=venture-acme")
    assert response.status_code == 200
    graph = response.json()
    assert graph["edges"] == []
    assert all("waiting_on" not in node["health"]["reasons"] for node in graph["nodes"])
    assert_no_leaks([str(graph)], restricted_terms(git_repo))


def test_restricted_viewer_with_grant_gets_record_and_request_cannot_select_clearance(client, git_repo):
    normal = client.get("/api/graph?viewer_agent=chief-of-staff&clearance=restricted").json()
    assert len(normal["nodes"]) == 12
    config = PortalConfig(git_repo, viewer_agent="chief-of-staff", viewer_token=issue(git_repo, "chief-of-staff"))
    with TestClient(create_app(config), base_url="http://127.0.0.1:8765") as privileged:
        graph = privileged.get("/api/graph").json()
        assert len(graph["nodes"]) == 13
        assert [node["id"] for node in graph["nodes"] if node["id"] == "task-launch-budget"] == ["task-launch-budget"]
        assert privileged.get("/api/ventures/venture-acme").json()["venture"]["counts"]["tasks"] == 3
        assert privileged.get("/api/search", params={"q": restricted_terms(git_repo)[1]}).json()["hits"] == [
            {"id": "task-launch-budget", "type": "task", "title": restricted_terms(git_repo)[1]}]
