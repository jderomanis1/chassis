"""API v1 projections, built exclusively from authenticated library reads."""
from datetime import datetime, timezone

from pydantic import TypeAdapter
from starlette.responses import JSONResponse
from starlette.routing import Route

from chassis.errors import NotFoundError
from chassis.models import RecordId
from chassis.read_model import neutral_graph
from chassis.portal.config import today, version_etag
from chassis.portal.health import health_map
from chassis.templates import GTM_SECTIONS

TASK_FIELDS = ("id", "title", "version", "owner", "status", "next_step", "due_at", "blocker_reason",
               "depends_on", "health", "last_activity_at")
CARD_FIELDS = ("id", "title", "version", "health", "next_milestone", "milestone_due_at",
               "counts", "last_activity_at")


def read_state(request):
    """Retry a concurrent commit instead of labeling old data with a new etag."""
    index = request.app.state.index
    for _ in range(3):
        etag = version_etag(index)
        records = index.list_records()
        if etag == version_etag(index):
            return etag, records
    raise RuntimeError("Source changed repeatedly during the read")


def gtm(body):
    sections, current = {name: "" for name in GTM_SECTIONS}, None
    for line in body.splitlines(keepends=True):
        if line.startswith("## "):
            heading = line[3:].strip()
            current = heading if heading in sections else None
        elif current is not None:
            sections[current] += line
    return {name: value.strip() for name, value in sections.items()}


def projections(request, records):
    health = health_map(records, (request.app.state.clock or today)())
    rows = [r | {"health": health[r["id"]]} for r in records]
    for record in rows:
        tasks = [r for r in rows if r["type"] == "task" and (
            r["venture"] == record["id"] if record["type"] == "venture" else r["parent"] == record["id"])]
        if record["type"] == "venture":
            record["counts"] = {"initiatives": sum(r["type"] == "initiative" and r["parent"] == record["id"] for r in rows),
                                "tasks": len(tasks), "blocked": sum(r["status"] == "blocked" for r in tasks),
                                "done": sum(r["status"] == "done" for r in tasks)}
        elif record["type"] == "initiative":
            record["progress"] = {"done": sum(r["status"] == "done" for r in tasks), "total": len(tasks)}
            record["gtm"] = gtm(record["body"])
    return rows


def snapshot(request):
    etag, records = read_state(request)
    rows = projections(request, records)
    return JSONResponse({"etag": etag, "generated_at": datetime.now(timezone.utc).isoformat(),
                         "ventures": [{key: r[key] for key in CARD_FIELDS} for r in rows if r["type"] == "venture"]})


def detail(request, kind):
    TypeAdapter(RecordId).validate_python(request.path_params["id"])
    _, records = read_state(request)
    rows = projections(request, records)
    record = next((r for r in rows if r["id"] == request.path_params["id"] and r["type"] == kind), None)
    if record is None:
        raise NotFoundError("Not found")
    if kind == "venture":
        return JSONResponse({"venture": record, "initiatives": [r for r in rows
                             if r["type"] == "initiative" and r["parent"] == record["id"]]})
    return JSONResponse({"initiative": record, "tasks": [{key: r[key] for key in TASK_FIELDS}
                         for r in rows if r["type"] == "task" and r["parent"] == record["id"]]})


def venture(request):
    return detail(request, "venture")


def initiative(request):
    return detail(request, "initiative")


def graph(request):
    venture = request.query_params.get("venture") or None
    if venture is not None:
        TypeAdapter(RecordId).validate_python(venture)
    _, records = read_state(request)
    if venture is not None and not any(r["id"] == venture and r["type"] == "venture" for r in records):
        raise NotFoundError("Not found")
    rows = projections(request, records)
    view = neutral_graph(rows, venture)
    by_id = {row["id"]: row for row in rows}
    view["nodes"] = [node | {key: by_id[node["id"]][key] for key in ("health", "version")}
                     for node in view["nodes"]]
    return JSONResponse(view)


def search(request):
    records = request.app.state.index.search(request.query_params.get("q", ""))
    return JSONResponse({"hits": [{key: r[key] for key in ("id", "type", "title")} for r in records]})


routes = [Route("/api/snapshot", snapshot, methods=["GET"]),
          Route("/api/ventures/{id}", venture, methods=["GET"]),
          Route("/api/initiatives/{id}", initiative, methods=["GET"]),
          Route("/api/graph", graph, methods=["GET"]),
          Route("/api/search", search, methods=["GET"])]
