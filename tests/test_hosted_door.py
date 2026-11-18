"""Deployment boundary checks. The core test matrix has no portal extra."""
import base64
import secrets
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from starlette.testclient import TestClient
except ImportError:
    raise unittest.SkipTest("portal extra required")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "deploy"))
from door import create_door


class DoorTests(unittest.TestCase):
    def setUp(self):
        self.origin = "https://fictional.invalid"
        self.password = secrets.token_urlsafe()
        auth = base64.b64encode(f"demo:{self.password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {auth}"}
        self.client = TestClient(create_door(self.origin, self.password), base_url=self.origin)
        relay = patch("door.relay")
        self.relay = relay.start()
        self.addCleanup(relay.stop)
        self.addCleanup(self.client.close)
        from starlette.responses import Response
        self.relay.return_value = Response(status_code=204)

    def test_password_required_for_every_resource(self):
        for path in ["/", "/api/session", "/assets/app.js", "/intro.mp3"]:
            for headers in [{}, {"Authorization": "Basic invalid"}]:
                response = self.client.get(path, headers=headers)
                self.assertEqual(response.status_code, 401)
                self.assertIn("Basic", response.headers["WWW-Authenticate"])
                self.assertIn("no-store", response.headers["Cache-Control"])
        self.relay.assert_not_called()

    def test_reads_preserve_etag_and_drop_credentials(self):
        response = self.client.get("/api/version", headers=self.headers | {
            "If-None-Match": '"abcd"', "Cookie": "unused=1"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.relay.call_args.args,
                         ("GET", "/api/version", {"if-none-match": '"abcd"'}, b""))

    def test_mutations_require_exact_evidence_before_origin_translation(self):
        headers = self.headers | {"Origin": self.origin, "Sec-Fetch-Site": "same-origin",
                                  "Content-Type": "application/json", "X-Chassis-CSRF": "launch-token"}
        for name, value in [("Origin", "https://elsewhere.invalid"), ("Origin", None),
                            ("Sec-Fetch-Site", "cross-site"), ("Sec-Fetch-Site", None),
                            ("Host", "other.invalid")]:
            invalid = headers.copy()
            if value is None:
                del invalid[name]
            else:
                invalid[name] = value
            self.assertEqual(self.client.patch("/api/records/id", headers=invalid,
                                               content=b"{}").status_code, 403)
        self.relay.assert_not_called()
        self.assertEqual(self.client.patch("/api/records/id", headers=headers,
                                           content=b"{}").status_code, 204)
        self.assertEqual(self.relay.call_args.args[2], {
            "origin": "http://127.0.0.1:8765", "sec-fetch-site": "same-origin",
            "content-type": "application/json", "x-chassis-csrf": "launch-token"})

    def test_body_cap_and_duplicate_origin(self):
        headers = self.headers | {"Origin": self.origin, "Sec-Fetch-Site": "same-origin"}
        self.assertEqual(self.client.put("/api/layout", headers=headers,
                                         content=b"x" * 65537).status_code, 413)
        duplicate = list(headers.items()) + [("Origin", self.origin)]
        self.assertEqual(self.client.put("/api/layout", headers=duplicate).status_code, 403)
        self.relay.assert_not_called()

    def test_configuration_fails_closed(self):
        for origin in ["", "http://fictional.invalid", self.origin + "/other",
                       "https://user@fictional.invalid", self.origin + "?x"]:
            with self.assertRaises(ValueError):
                create_door(origin, self.password)
        with self.assertRaises(ValueError):
            create_door(self.origin, "")
