"""Start one disposable vault, one loopback portal and one public front door."""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

RUNTIME = Path("/run/chassis-demo")
LOCAL_PORT = 8765


def chassis(*args, env=None):
    installed = Path(sys.executable).with_name("chassis")
    binary = str(installed) if installed.is_file() else shutil.which("chassis")
    if not binary:
        raise RuntimeError("Install the Chassis console script first")
    return subprocess.check_output([binary, *args], text=True, env=env)


def portal_environment():
    return {key: value for key, value in os.environ.items()
            if key in {"PATH", "LANG", "LC_ALL", "HOME", "TZ", "PYTHONPATH"}}


def initialize(vault):
    env = portal_environment()
    credentials = json.loads(chassis("demo-init", vault, env=env))["credentials"]
    return env | {"CHASSIS_PORTAL_VIEWER_AGENT": "reviewer",
                  "CHASSIS_AGENT_TOKEN": credentials["reviewer"],
                  "CHASSIS_PORTAL_EDITOR_AGENT": "canvas-editor",
                  "CHASSIS_PORTAL_EDITOR_TOKEN": credentials["canvas-editor"]}


def run():
    from door import create_door
    origin = os.environ.get("PUBLIC_ORIGIN") or os.environ.get("RENDER_EXTERNAL_URL", "")
    password = os.environ.get("DEMO_PASSWORD", "")
    create_door(origin, password)  # Validate before creating a vault or opening a socket.
    port = int(os.environ["PORT"])
    if not 1 <= port <= 65535 or port == LOCAL_PORT:
        raise ValueError("PORT must be a valid port distinct from the local portal port")
    os.umask(0o077)
    stopping = False

    def shutdown(*_):
        nonlocal stopping
        stopping = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, shutdown)
    children = []
    with tempfile.TemporaryDirectory(dir=RUNTIME) as generation:
        vault = Path(generation) / "vault"
        env = initialize(vault)
        try:
            portal = subprocess.Popen([sys.executable, "-m", "chassis.cli", "portal", "--vault",
                                       vault, "--host", "127.0.0.1", "--port", str(LOCAL_PORT),
                                       "--allow-writes"], env=env)
            children.append(portal)
            opener = build_opener(ProxyHandler({}))
            deadline = time.monotonic() + 30
            while not stopping:
                if portal.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Loopback portal failed its startup check")
                try:
                    with opener.open(f"http://127.0.0.1:{LOCAL_PORT}/api/session", timeout=1) as r:
                        if json.load(r)["writes_enabled"]:
                            break
                except OSError:
                    pass
                time.sleep(0.1)
            if stopping:
                return
            link = Path(generation) / "current"
            link.symlink_to(vault, target_is_directory=True)
            link.replace(RUNTIME / "current")
            door_env = portal_environment() | {"PUBLIC_ORIGIN": origin, "DEMO_PASSWORD": password}
            door = subprocess.Popen([sys.executable, "-m", "uvicorn", "door:from_environment",
                                     "--factory", "--app-dir", str(Path(__file__).resolve().parent),
                                     "--host", "0.0.0.0", "--port", str(port), "--lifespan", "off",
                                     "--no-proxy-headers", "--no-access-log"], env=door_env)
            children.append(door)
            while not stopping:
                if any(child.poll() is not None for child in children):
                    raise RuntimeError("A demo service exited")
                time.sleep(0.25)
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
            for child in children:
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            current = RUNTIME / "current"
            if current.is_symlink() and current.readlink() == vault:
                current.unlink()


if __name__ == "__main__":
    run()
