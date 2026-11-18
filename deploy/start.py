"""Start one disk-backed fictional vault, one loopback portal and one public front door."""
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

RUNTIME = Path("/var/data")
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


def portal_credentials(credentials):
    return portal_environment() | {
        "CHASSIS_PORTAL_VIEWER_AGENT": "reviewer",
        "CHASSIS_AGENT_TOKEN": credentials["reviewer"],
        "CHASSIS_PORTAL_EDITOR_AGENT": "canvas-editor",
        "CHASSIS_PORTAL_EDITOR_TOKEN": credentials["canvas-editor"],
    }


def initialize(vault):
    credentials = json.loads(chassis("demo-init", vault, env=portal_environment()))["credentials"]
    return portal_credentials(credentials)


def open_vault(root):
    vault = root / "current"
    previous = root / ".reset-previous"
    # Recover a reset interrupted between moving the old vault and publishing its replacement.
    if previous.exists() and not os.path.lexists(vault):
        previous.rename(vault)
    if vault.is_symlink() or (vault.exists() and not (vault / ".git").is_dir()):
        raise RuntimeError(f"Expected a demo Git vault at {vault}. Existing data was left in place.")
    if previous.exists():
        shutil.rmtree(previous)
    if vault.exists() and not (vault / ".chassis/reset-on-next-start").is_file():
        subprocess.run(["git", "-C", vault, "rev-parse", "--verify", "HEAD"],
                       check=True, stdout=subprocess.DEVNULL)
        credentials = {agent: chassis("agent-token", "create", agent, "--vault", vault,
                                      env=portal_environment()).strip()
                       for agent in ("reviewer", "canvas-editor")}
        return portal_credentials(credentials)

    # Stage on the same disk. A failed demo-init cannot change the active board.
    with tempfile.TemporaryDirectory(dir=root, prefix=".seed-") as staging:
        fresh = Path(staging) / "vault"
        env = initialize(fresh)
        if vault.exists():
            vault.rename(previous)  # The reset request travels with the old board.
        fresh.rename(vault)
    if previous.exists():
        shutil.rmtree(previous)
    return env


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
    # Linux mountinfo also identifies bind mounts on the same filesystem.
    mounts = Path("/proc/self/mountinfo").read_text().splitlines()
    if not any(line.split()[4] == str(RUNTIME) for line in mounts):
        raise RuntimeError(f"Mount the sandbox disk at {RUNTIME} before starting")
    vault = RUNTIME / "current"
    env = open_vault(RUNTIME)
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


if __name__ == "__main__":
    run()
