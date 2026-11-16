"""Real newline-delimited JSON-RPC client with a complete bidirectional wire log."""

import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time


class StdioClient:
    def __init__(self, root, **environment):
        self.transcript, self.stdout_lines, self.stderr_lines = [], [], []
        self.responses, self.sequence = queue.Queue(), 0
        self.log_events = queue.Queue()
        self.process = subprocess.Popen(
            [sys.executable, "-m", "chassis.mcp_server", "--vault", str(root)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", env=os.environ | environment, start_new_session=True)
        self.readers = [threading.Thread(target=self._read_stdout, daemon=True),
                        threading.Thread(target=self._read_stderr, daemon=True)]
        for reader in self.readers:
            reader.start()

    def _read_stdout(self):
        for line in self.process.stdout:
            self.stdout_lines.append(line)
            try:
                message = json.loads(line)
                self.transcript.append({"direction": "server_to_client", "message": message})
                self.responses.put(message)
            except ValueError as exc:
                self.responses.put(exc)
        self.responses.put(EOFError("Server stdout closed"))

    def _read_stderr(self):
        for line in self.process.stderr:
            self.stderr_lines.append(line)
            self.log_events.put(line)

    def wait_for_log(self, text, timeout=5):
        deadline = time.monotonic() + timeout
        while text not in self.log_events.get(timeout=max(0, deadline - time.monotonic())):
            pass

    def send(self, method, params=None, *, notification=False):
        self.sequence += 1
        message = {"jsonrpc": "2.0", "method": method}
        if not notification:
            message["id"] = self.sequence
        if params is not None:
            message["params"] = params
        self.transcript.append({"direction": "client_to_server", "message": message})
        self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        return self.sequence

    def receive(self, identifier, timeout=10):
        message = self.responses.get(timeout=timeout)
        if isinstance(message, Exception):
            raise message
        assert message["jsonrpc"] == "2.0" and message["id"] == identifier, message
        assert "error" not in message, message
        return message["result"]

    def request(self, method, params=None):
        return self.receive(self.send(method, params))

    def initialize(self):
        result = self.request("initialize", {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "chassis-acceptance-client", "version": "1.0"}})
        self.send("notifications/initialized", notification=True)
        return result

    def call(self, name, arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        payload = result["structuredContent"]
        assert json.loads(result["content"][0]["text"]) == payload
        assert result.get("isError", False) == ("error" in payload)
        return payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            self.process.stdin.close()
            self.process.wait(timeout=5)
        finally:
            if self.process.poll() is None:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=5)
            for reader in self.readers:
                reader.join(timeout=5)
            self.process.stdout.close()
            self.process.stderr.close()
        if exc[0] is None:
            assert self.process.returncode == 0, "".join(self.stderr_lines)
            assert all(not reader.is_alive() for reader in self.readers)
            try:
                os.killpg(self.process.pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise AssertionError("Server left an orphan process in its process group")
            assert self.stdout_lines
            assert all(json.loads(line)["jsonrpc"] == "2.0" for line in self.stdout_lines)
