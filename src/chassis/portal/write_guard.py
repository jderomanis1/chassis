"""One local browser write boundary, shared by record and view-state routes."""
import hmac
from collections import deque
from time import monotonic

from starlette.responses import JSONResponse

from chassis.audit import record_event
from chassis.errors import AuthorizationError
from chassis.policy import authorize_reader, authorize_writer

MAX_BODY = 64 * 1024
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
       "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
       "form-action 'none'; frame-ancestors 'none'")


def editor_policy(config):
    if (not config.editor_agent or not config.editor_token or
            config.editor_agent == config.viewer_agent or
            hmac.compare_digest(config.editor_token.encode(), (config.viewer_token or "").encode())):
        raise AuthorizationError("Portal requires a separate proven normal editor")
    policy = authorize_writer(config.root, config.editor_agent, config.editor_token)
    if policy.agents[config.editor_agent].clearance != "normal":
        raise AuthorizationError("Portal editor must have normal clearance")
    return policy


class WriteGuard:
    def __init__(self, config):
        self.config, self.requests = config, deque()

    def refuse(self, code="validation", message="Write not permitted", status=403):
        record_event(self.config.root, self.config.editor_agent, "portal_write", "denied")
        return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)

    async def check(self, request, authority):
        config, now = self.config, monotonic()
        while self.requests and self.requests[0] <= now - 60:
            self.requests.popleft()
        if len(self.requests) >= 60:
            return self.refuse("rate_limited", "Too many writes. Try again shortly.", 429)
        self.requests.append(now)
        if not config.allow_writes:
            response = self.refuse("validation", "Only GET is supported", 405)
            response.headers["Allow"] = "GET"
            return response
        if (request.headers.get("host") != authority or
                request.headers.get("origin") != f"http://{authority}" or
                request.headers.get("sec-fetch-site") != "same-origin" or
                request.headers.get("content-type") != "application/json" or
                not hmac.compare_digest(request.headers.get("x-chassis-csrf", "").encode(),
                                        request.app.state.csrf.encode())):
            return self.refuse()
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BODY:
                return self.refuse()
            body.extend(chunk)
        request.state.payload = bytes(body)
        try:
            editor_policy(config)
            if authorize_reader(config.root, config.viewer_agent, config.viewer_token) is None:
                raise AuthorizationError("Viewer unavailable")
        except AuthorizationError:
            return self.refuse("not_found", "Not found", 404)
        # A failed pre-write audit must stop before any mutation.
        record_event(config.root, config.editor_agent, "portal_write", "attempt")
        return None
