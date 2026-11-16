"""Body-free, append-only local operation audit, separate from the vault lock."""
import fcntl
import inspect
import json
import os
import re
from pathlib import PurePosixPath
from datetime import datetime, timezone
from functools import wraps
from contextvars import ContextVar

from chassis.identity import caller_id
from chassis.errors import AuditError

_denied = ContextVar("read_denied", default=False)


def mark_denied():
    _denied.set(True)


def append_event(root, agent, tool, outcome, *, count=None, record_ids=()):
    directory, path = root / ".chassis", root / ".chassis/audit.jsonl"
    if directory.is_symlink() or path.is_symlink():
        raise ValueError("Audit paths cannot be symlinks")
    directory.mkdir(exist_ok=True, mode=0o700)
    safe_agent = agent if isinstance(agent, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,79}", agent) else ""
    entry = {"time": datetime.now(timezone.utc).isoformat(), "agent_id": safe_agent,
             "tool": tool, "outcome": outcome}
    entry.update({"count": count} if count is not None else {"record_ids": list(record_ids)})
    data = (json.dumps(entry, ensure_ascii=True) + "\n").encode()
    fd = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        while data:
            data = data[os.write(fd, data):]
        os.fsync(fd)
    finally:
        os.close(fd)


def record_event(root, agent, tool, outcome, *, recovery=None, **details):
    try:
        append_event(root, agent, tool, outcome, **details)
    except (OSError, ValueError) as exc:
        raise AuditError("Audit unavailable", **(recovery or {})) from exc


def audited(tool, *, many=False):
    def decorate(function):
        signature = inspect.signature(function)

        @wraps(function)
        def run(self, *args, **kwargs):
            arguments = signature.bind(self, *args, **kwargs).arguments
            agent = caller_id(arguments.get("agent", getattr(self, "agent", None)))
            context = _denied.set(False)
            try:
                result = function(self, *args, **kwargs)
            except Exception as exc:
                _denied.reset(context)
                recovery = {k: v for k, v in getattr(exc, "details", {}).items()
                            if k in {"committed", "commit", "current_version", "commit_state"}}
                record_event(self.root, agent, tool, getattr(exc, "code", "error"),
                             count=0 if many else None, recovery=recovery)
                raise
            ids = []
            if isinstance(result, dict):
                record = result.get("record", result)
                if "id" in record:
                    ids = [record["id"]]
                elif "nodes" in result:
                    ids = [node["id"] for node in result["nodes"]]
                elif "path" in result and "commit" in result:
                    ids = [PurePosixPath(result["path"]).stem]
            outcome = "denied" if _denied.get() else ("not_found" if result is None else "ok")
            _denied.reset(context)
            recovery = {}
            if isinstance(result, dict) and "commit" in result:
                recovery = {"committed": True, "commit": result["commit"]}
                if "record" in result:
                    recovery["current_version"] = result["record"]["version"]
            record_event(self.root, agent, tool, outcome, recovery=recovery,
                         count=(result if isinstance(result, int) else len(result)) if many else None,
                         record_ids=ids)
            return result
        return run
    return decorate
