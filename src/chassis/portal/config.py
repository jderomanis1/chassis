"""Portal configuration, clock, bind guard, and source revision fingerprint."""
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TASK_DUE_SOON_DAYS = 3
MILESTONE_SOON_DAYS = 7
STALE_DAYS = 14
PHOENIX = ZoneInfo("America/Phoenix")


def today():
    return datetime.now(PHOENIX).date()


def validate_bind(host):
    host = "127.0.0.1" if host == "localhost" else host
    if host not in {"127.0.0.1", "::1"}:
        raise ValueError("Portal requires a loopback host: 127.0.0.1 or ::1 only")
    return host


@dataclass(frozen=True)
class PortalConfig:
    root: Path
    host: str = "127.0.0.1"
    port: int = 8765
    viewer_agent: str = "reviewer"
    viewer_token: str | None = field(default=None, repr=False)
    allow_writes: bool = False
    editor_agent: str = ""
    editor_token: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls, root, host="127.0.0.1", port=8765, *, allow_writes=False):
        if not 1 <= port <= 65535:
            raise ValueError("Portal port must be between 1 and 65535")
        return cls(Path(root).resolve(), validate_bind(host), port,
                   os.environ.get("CHASSIS_PORTAL_VIEWER_AGENT", "reviewer"),
                   os.environ.get("CHASSIS_AGENT_TOKEN", ""), allow_writes,
                   os.environ.get("CHASSIS_PORTAL_EDITOR_AGENT", ""),
                   os.environ.get("CHASSIS_PORTAL_EDITOR_TOKEN", ""))


def version_etag(index):
    """Fingerprint only the caller's authorized view, including visible activity."""
    records = index.list_records()
    payload = json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
