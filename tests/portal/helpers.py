"""Dependency-free fixture helpers, independent of pytest's conftest imports."""
import hashlib
import secrets
import subprocess

import yaml


class EphemeralToken(str):
    def __repr__(self):
        return "<ephemeral credential>"


def issue(root, agent):
    """Generate a fresh test credential in memory; persist its digest only."""
    path = root / ".chassis/agent-tokens.yaml"
    path.parent.mkdir(exist_ok=True)
    data = yaml.safe_load(path.read_text()) if path.exists() else {"version": 1, "tokens": {}}
    token = secrets.token_urlsafe(32)
    data["tokens"][agent] = hashlib.sha256(token.encode()).hexdigest()
    path.write_text(yaml.safe_dump(data))
    return EphemeralToken(token)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
