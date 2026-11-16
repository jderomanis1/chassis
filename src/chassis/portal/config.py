"""Portal configuration, clock, bind guard, and source revision fingerprint."""
import hashlib
import ipaddress
import os
import subprocess
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
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if not loopback and os.environ.get("CHASSIS_PORTAL_ALLOW_REMOTE") != "1":
        raise ValueError("Portal requires a loopback host; remote binding requires CHASSIS_PORTAL_ALLOW_REMOTE=1")
    return host


@dataclass(frozen=True)
class PortalConfig:
    root: Path
    host: str = "127.0.0.1"
    port: int = 8765
    viewer_agent: str = "reviewer"
    viewer_token: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls, root, host="127.0.0.1", port=8765):
        if not 1 <= port <= 65535:
            raise ValueError("Portal port must be between 1 and 65535")
        return cls(Path(root).resolve(), validate_bind(host), port,
                   os.environ.get("CHASSIS_PORTAL_VIEWER_AGENT", "reviewer"),
                   os.environ.get("CHASSIS_AGENT_TOKEN", ""))


def version_etag(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)

    head = git("rev-parse", "HEAD").decode().strip()
    paths = sorted(set(git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")) - {b""})
    digest = hashlib.sha256()
    for name in paths:
        path = root / os.fsdecode(name)
        data = os.fsencode(os.readlink(path)) if path.is_symlink() else (
            path.read_bytes() if path.is_file() else b"<deleted>")
        digest.update(name + b"\0" + len(data).to_bytes(8, "big") + data)
    return f"{head}:{digest.hexdigest()}"
