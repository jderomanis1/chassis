"""Authenticated Render edge for the unchanged loopback portal."""
import base64
import hmac
import http.client
from urllib.parse import urlsplit

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response

PORTAL_HOST = "127.0.0.1"
PORTAL_PORT = 8765
LOCAL_ORIGIN = f"http://{PORTAL_HOST}:{PORTAL_PORT}"
BODY_LIMIT = 64 * 1024
REQUEST_HEADERS = ("content-type", "x-chassis-csrf", "sec-fetch-site",
                   "if-none-match", "range", "if-range")
RESPONSE_HEADERS = ("content-type", "content-security-policy", "referrer-policy",
                    "x-content-type-options", "etag", "last-modified", "content-range",
                    "accept-ranges", "allow", "retry-after")


def relay(method, target, headers, body):
    upstream = http.client.HTTPConnection(PORTAL_HOST, PORTAL_PORT, timeout=20)
    try:
        upstream.request(method, target, body=body, headers=headers)
        reply = upstream.getresponse()
        outgoing = {key: reply.getheader(key) for key in RESPONSE_HEADERS if reply.getheader(key)}
        outgoing["cache-control"] = "private, no-store"
        return Response(reply.read(), status_code=reply.status, headers=outgoing)
    except (OSError, http.client.HTTPException):
        return refuse(502)
    finally:
        upstream.close()


def refuse(status):
    headers = {"cache-control": "private, no-store"}
    if status == 401:
        headers["www-authenticate"] = 'Basic realm="Chassis demo", charset="UTF-8"'
    return Response(status_code=status, headers=headers)


def create_door(public_origin, password):
    url = urlsplit(public_origin)
    if (not password.strip() or url.scheme != "https" or not url.hostname or
            url.username is not None or public_origin != f"https://{url.netloc}" or
            any(ch.isspace() for ch in public_origin) or "\\" in public_origin):
        raise ValueError("Set a password and a canonical HTTPS public origin")
    auth = b"Basic " + base64.b64encode(f"demo:{password}".encode())

    async def app(scope, receive, send):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        request = Request(scope, receive)
        response = await dispatch(request)
        await response(scope, receive, send)

    async def dispatch(request):
        headers = request.headers
        if headers.getlist("host") != [url.netloc]:
            return refuse(403)
        authorization = headers.getlist("authorization")
        if len(authorization) != 1 or not hmac.compare_digest(authorization[0].encode(), auth):
            return refuse(401)
        if request.method not in ("GET", "PATCH", "PUT"):
            return refuse(405)
        origins = headers.getlist("origin")
        writing = request.method != "GET"
        if (origins and origins != [public_origin]) or (writing and
                (not origins or headers.getlist("sec-fetch-site") != ["same-origin"])):
            return refuse(403)
        if any(len(headers.getlist(key)) > 1 for key in REQUEST_HEADERS):
            return refuse(403)
        forwarded = {k: headers[k] for k in REQUEST_HEADERS if k in headers}
        if origins:
            forwarded["origin"] = LOCAL_ORIGIN
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > BODY_LIMIT:
                return refuse(413)
            body.extend(chunk)
        raw = request.scope["raw_path"]
        query = request.scope["query_string"]
        target = raw + (b"?" + query if query else b"")
        if not raw.startswith(b"/") or raw.startswith(b"//") or not target.isascii():
            return refuse(400)
        return await run_in_threadpool(relay, request.method, target.decode("ascii"),
                                       forwarded, bytes(body))

    return app


def from_environment():
    import os
    return create_door(os.environ["PUBLIC_ORIGIN"], os.environ["DEMO_PASSWORD"])
