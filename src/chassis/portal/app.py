"""One-process local API using the authenticated library view."""
import json
from pathlib import Path
from secrets import token_urlsafe

from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from chassis.audit import record_event
from chassis.errors import AuditError, AuthorizationError, NotFoundError
from chassis.index import RecordIndex
from chassis.policy import authorize_reader
from chassis.portal.config import validate_bind, version_etag
from chassis.portal.api import routes
from chassis.portal.writes import routes as write_routes
from chassis.portal.layout import routes as layout_routes
from chassis.portal.write_guard import CSP, WriteGuard, editor_policy

ASSET_ROOT = Path(__file__).with_name("static")


def error(code, message, status):
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


async def response_payload(response):
    """Read a middleware response without assuming the body is already buffered."""
    body = getattr(response, "body", None)
    if body is None:
        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, memoryview):
                chunks.append(chunk.tobytes())
            elif isinstance(chunk, (bytes, bytearray)):
                chunks.append(bytes(chunk))
        body = b"".join(chunks)
    try:
        payload = json.loads(body or b"{}")
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


async def commit_audit_failure(response):
    """Keep commit recovery visible when the audit append fails after a successful write."""
    details = {}
    if response.status_code < 400:
        payload = await response_payload(response)
        commit = payload.get("commit")
        version = (payload.get("record") or {}).get("version")
        if commit and version is not None:
            details = {"committed": True, "commit": commit, "current_version": version}
    body = {"error": {"code": "audit_error", "message": "Audit unavailable", **details}}
    return JSONResponse(body, status_code=500)


def create_app(config, *, clock=None):
    host = validate_bind(config.host)
    if authorize_reader(config.root, config.viewer_agent, config.viewer_token) is None:
        raise AuthorizationError("Portal viewer authentication failed")
    if config.allow_writes:
        editor_policy(config)
    index = RecordIndex(config.root, agent=config.viewer_agent, token=config.viewer_token)

    def version(request):
        etag = version_etag(index)
        record_event(config.root, config.viewer_agent, "version", "ok")
        return JSONResponse({"etag": etag})

    def session(request):
        record_event(config.root, config.viewer_agent, "session", "ok")
        return JSONResponse({"csrf": request.app.state.csrf, "writes_enabled": config.allow_writes,
                             "viewer": config.viewer_agent})

    async def http_error(request, exc):
        return error("not_found", "Not found", 404)

    app = Starlette(routes=[Route("/api/session", session, methods=["GET"]),
                    Route("/api/version", version, methods=["GET"]), *routes, *write_routes, *layout_routes,
                    Route("/api/{path:path}", lambda request: error("not_found", "Not found", 404), methods=["GET"]),
                    Mount("/", app=StaticFiles(directory=ASSET_ROOT, html=True), name="static")],
                    exception_handlers={404: http_error})
    app.state.index, app.state.config, app.state.clock = index, config, clock
    app.state.csrf = token_urlsafe(32)
    guard = WriteGuard(config)

    async def boundary(request, call_next):
        try:
            authority = f"[{host}]:{config.port}" if ":" in host else f"{host}:{config.port}"
            if request.headers.get("host") != authority:
                response = (guard.refuse() if request.method != "GET" else
                            error("validation", "Origin or host not permitted", 403))
            elif request.method != "GET":
                response = await guard.check(request, authority)
                if response is None:
                    response = await call_next(request)
                    try:
                        record_event(config.root, config.editor_agent, "portal_write",
                                     "ok" if response.status_code < 400 else "refused")
                    except AuditError:
                        response = await commit_audit_failure(response)
            elif (
                    request.headers.get("origin") not in {None, f"http://{authority}"}):
                response = error("validation", "Origin or host not permitted", 403)
            elif authorize_reader(config.root, config.viewer_agent, config.viewer_token) is None:
                record_event(config.root, config.viewer_agent, "portal_read", "denied")
                response = error("not_found", "Not found", 404)
            else:
                response = await call_next(request)
        except (NotFoundError, AuthorizationError):
            response = error("not_found", "Not found", 404)
        except ValidationError:
            response = error("validation", "Invalid request", 400)
        except Exception:
            response = error("internal", "Request could not be completed", 500)
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = CSP
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=boundary)
    return app
