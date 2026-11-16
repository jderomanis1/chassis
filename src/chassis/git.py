"""Local Git operations; no network calls and no commits of unrelated staging."""

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from chassis.errors import DirtyRecordError, GitError, WriteError


@dataclass(frozen=True)
class Identity:
    name: str
    email: str

    @classmethod
    def from_env(cls, role: str):
        values = []
        for field in ("NAME", "EMAIL"):
            key = f"CHASSIS_{role}_{field}"
            value = os.environ.get(key, "").strip()
            if not value or any(char in value for char in "\r\n<>"):
                raise WriteError(f"Set a valid {key} before writing")
            values.append(value)
        return cls(*values)


def run_git(root: Path, *args: str, identity: Identity | None = None) -> str:
    # Inherited Git routing/index variables must not redirect a record commit.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    if identity is not None:
        for role in ("AUTHOR", "COMMITTER"):
            env[f"GIT_{role}_NAME"] = identity.name
            env[f"GIT_{role}_EMAIL"] = identity.email
    result = subprocess.run(["git", "-C", str(root), "--literal-pathspecs", *args],
                            env=env, capture_output=True, text=True)
    if result.returncode:
        raise GitError(f"git {args[0]} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def ensure_repository(root: Path) -> None:
    if Path(run_git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise GitError(f"{root}: vault must be the Git repository root")
    run_git(root, "rev-parse", "--verify", "HEAD")


def record_activity(root: Path) -> dict[str, str]:
    """Latest HEAD-history commit per record path, using committer time in UTC."""
    if not (root / ".git").exists() or not run_git(root, "rev-parse", "--revs-only", "HEAD"):
        return {}
    history = run_git(root, "log", "--topo-order", "--format=chassis-commit:%cI",
                      "--name-only", "-z", "HEAD", "--", "records/")
    activity, timestamp = {}, None
    for part in history.split("\0"):
        part = part.lstrip("\n")
        if part.startswith("chassis-commit:"):
            timestamp = datetime.fromisoformat(part.removeprefix("chassis-commit:")).astimezone(
                timezone.utc).isoformat()
        elif part.startswith("records/") and timestamp is not None:
            activity.setdefault(part, timestamp)
    return activity


def has_record_changes(root: Path, path: Path) -> bool:
    """Shared dirty-state check; hidden index flags require explicit human repair."""
    relative = path.relative_to(root).as_posix()
    tracked = run_git(root, "ls-files", "-v", "--", relative)
    if any(line[0] == "S" or line[0].islower() for line in tracked.splitlines()):
        raise DirtyRecordError(f"{relative}: uncommitted human edit; "
                               "clear the assume-unchanged/skip-worktree flag first, "
                               f"then run chassis commit-human {relative}", path=relative)
    status = run_git(root, "status", "--porcelain=v1", "--untracked-files=all", "--", relative)
    if status:
        return True
    return path.is_file() and (not tracked or
        run_git(root, "hash-object", f"--path={relative}", "--", relative)
        != run_git(root, "rev-parse", f"HEAD:{relative}"))


def ensure_clean(root: Path, path: Path) -> None:
    if has_record_changes(root, path):
        relative = path.relative_to(root).as_posix()
        raise DirtyRecordError(f"{relative}: uncommitted human edit; "
                               f"run chassis commit-human {relative}", path=relative)


def commit_file(root: Path, path: Path, identity: Identity, message: str) -> str:
    relative = path.relative_to(root).as_posix()
    untracked = not run_git(root, "ls-files", "--", relative)
    if untracked:
        run_git(root, "add", "--intent-to-add", "--", relative)
    try:
        run_git(root, "commit", "--only", "-m", message, "--", relative, identity=identity)
    except GitError:
        if untracked:
            run_git(root, "reset", "--", relative)
        raise
    return run_git(root, "rev-parse", "HEAD")
