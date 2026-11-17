"""API v1 projections, built exclusively from authenticated library reads."""
from datetime import datetime, timezone

from starlette.responses import JSONResponse
from starlette.routing import Route

from chassis.errors import NotFoundError
from chassis.portal.config import today, version_etag
from chassis.portal.health import health_map
from chassis.templates import GTM_SECTIONS

TASK_FIELDS = ("id", "title", "owner", "status", "due_at", "blocker_reason",
               "depends_on", "health", "last_activity_at")
CARD_FIELDS = ("id", "title", "health", "next_milestone", "milestone_due_at",
               "counts", "last_activity_at")


def read_state(request):
    """Retry a concurrent commit instead of labeling old data with a new etag."""
    root = request.app.state.config.root
    for _ in range(3):
        etag = version_etag(root)
        records = request.app.state.index.list_records()
        if etag == version_etag(root):
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


routes = [Route("/api/snapshot", snapshot, methods=["GET"]),
          Route("/api/ventures/{id}", venture, methods=["GET"]),
          Route("/api/initiatives/{id}", initiative, methods=["GET"])]
