"""Per-viewer layout is ignored view state, filtered under the shared vault lock."""
import json
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from starlette.responses import JSONResponse
from starlette.routing import Route

from chassis.atomic import vault_lock, write_atomic
from chassis.audit import record_event
from chassis.errors import NotFoundError
from chassis.models import RecordId
from chassis.policy import authorize_reader
from chassis.portal.write_guard import MAX_BODY, editor_policy

Coordinate = Annotated[float, Field(strict=True, ge=-1000000, le=1000000, allow_inf_nan=False)]


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    x: Coordinate = 0
    y: Coordinate = 0


class Viewport(Point):
    zoom: Annotated[float, Field(ge=0.1, le=4, allow_inf_nan=False)] = 1


class Layout(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    positions: dict[RecordId, Point] = Field(default_factory=dict, max_length=2000)
    collapsed: list[RecordId] = Field(default_factory=list, max_length=2000)
    hidden: list[RecordId] = Field(default_factory=list, max_length=2000)
    viewport: Viewport = Field(default_factory=Viewport)


def layout_path(config):
    viewer = TypeAdapter(RecordId).validate_python(config.viewer_agent)
    path = config.root / ".chassis" / "layout" / f"{viewer}.json"
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("Unsafe layout path")
    return path


def filtered(layout, visible):
    return {"positions": {key: value.model_dump() for key, value in layout.positions.items() if key in visible},
            "collapsed": sorted(set(layout.collapsed) & visible), "hidden": sorted(set(layout.hidden) & visible),
            "viewport": layout.viewport.model_dump()}


def layout_route(request):
    config, index = request.app.state.config, request.app.state.index
    writing = request.method == "PUT"
    proposed = Layout.model_validate_json(request.state.payload) if writing else None
    with vault_lock(config.root):
        if authorize_reader(config.root, config.viewer_agent, config.viewer_token) is None:
            raise NotFoundError("Not found")
        if writing:
            editor_policy(config)
        path = layout_path(config)
        visible = {row["id"] for row in index._visible_locked()}
        if not writing:
            try:
                proposed = Layout.model_validate_json(path.read_bytes()) if path.stat().st_size <= MAX_BODY else Layout()
            except (ValueError, OSError):
                proposed = Layout()
        result = filtered(proposed, visible)
        if writing:
            path.parent.mkdir(mode=0o700, exist_ok=True)
            write_atomic(path, json.dumps(result, sort_keys=True, separators=(",", ":")).encode())
        record_event(config.root, config.viewer_agent, "layout_write" if writing else "layout_read", "ok",
                     count=len(result["positions"]))
    return JSONResponse(result)


routes = [Route("/api/layout", layout_route, methods=["GET", "PUT"])]
