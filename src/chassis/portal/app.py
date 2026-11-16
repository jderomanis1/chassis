"""One-process read-only JSON API using the authenticated library view."""
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.base import BaseHTTPMiddleware

from chassis.audit import record_event
from chassis.errors import AuthorizationError, NotFoundError
from chassis.index import RecordIndex
from chassis.policy import authorize_reader
from chassis.portal.config import validate_bind, version_etag
from chassis.portal.api import routes


def error(code, message, status):
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def create_app(config, *, clock=None):
    host = validate_bind(config.host)
    if authorize_reader(config.root, config.viewer_agent, config.viewer_token) is None:
        raise AuthorizationError("Portal viewer authentication failed")
    index = RecordIndex(config.root, agent=config.viewer_agent, token=config.viewer_token)

    def version(request):
        etag = version_etag(config.root)
        record_event(config.root, config.viewer_agent, "version", "ok")
        return JSONResponse({"etag": etag})

    async def http_error(request, exc):
        return error("not_found", "Not found", 404)

    app = Starlette(routes=[Route("/api/version", version, methods=["GET"]), *routes],
                    exception_handlers={404: http_error})
    app.state.index, app.state.config, app.state.clock = index, config, clock

    async def boundary(request, call_next):
        try:
            authority = f"[{host}]:{config.port}" if ":" in host else f"{host}:{config.port}"
            if request.method != "GET":
                response = error("validation", "Only GET is supported", 405)
            elif request.headers.get("host") != authority or (
                    request.headers.get("origin") not in {None, f"http://{authority}"}):
                response = error("validation", "Origin or host not permitted", 403)
            elif authorize_reader(config.root, config.viewer_agent, config.viewer_token) is None:
                record_event(config.root, config.viewer_agent, "portal_read", "denied")
                response = error("not_found", "Not found", 404)
            else:
                response = await call_next(request)
        except NotFoundError:
            response = error("not_found", "Not found", 404)
        except Exception:
            response = error("internal", "Request could not be completed", 500)
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=boundary)
    return app
