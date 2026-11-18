"""Visible counts stay the same when a restricted task is added or removed."""


def published(client):
    snapshot = client.get("/api/snapshot").json()
    view = {}
    for venture in snapshot["ventures"]:
        detail = client.get(f"/api/ventures/{venture['id']}").json()
        initiatives = {}
        for initiative in detail["initiatives"]:
            tasks = client.get(f"/api/initiatives/{initiative['id']}").json()["tasks"]
            initiatives[initiative["id"]] = {"progress": initiative["progress"], "tasks": len(tasks)}
        graph = client.get(f"/api/graph?venture={venture['id']}").json()
        cards = sum(item["tasks"] for item in initiatives.values())
        view[venture["id"]] = {
            "counts": venture["counts"],
            "initiatives": initiatives,
            "cards": cards,
            "graph_tasks": sum(node["type"] == "task" for node in graph["nodes"]),
        }
        assert venture["counts"]["tasks"] == cards == view[venture["id"]]["graph_tasks"]
        assert sum(item["progress"]["total"] for item in initiatives.values()) == cards
        assert venture["counts"]["done"] + venture["counts"]["blocked"] <= cards
    return view


def test_restricted_task_does_not_change_tile_detail_or_graph_counts(client, git_repo):
    before = published(client)
    source = (git_repo / "records/tasks/task-launch-budget.md").read_text()
    extra = source.replace("id: task-launch-budget", "id: task-hidden-extra").replace(
        "title: Set the internal launch test budget", "title: Hidden extra fictional task")
    (git_repo / "records/tasks/task-hidden-extra.md").write_text(extra)
    assert published(client) == before
    blob = client.get("/api/snapshot").text + client.get("/api/ventures/venture-acme").text
    assert "task-hidden-extra" not in blob and "Hidden extra fictional task" not in blob
    (git_repo / "records/tasks/task-launch-budget.md").unlink()
    (git_repo / "records/tasks/task-hidden-extra.md").unlink()
    assert published(client) == before
