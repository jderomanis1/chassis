"""Validated single-file persistence. Every caller must hold vault_lock."""

import sqlite3
from pathlib import Path

from chassis.atomic import write_atomic
from chassis.errors import CommittedIndexError, DirtyRecordError, WriteError
from chassis.git import Identity, commit_file, ensure_clean, run_git
from chassis.index import RecordIndex
from chassis.markdown import ParsedRecord, serialize_record


def persist_record(root: Path, item: ParsedRecord, original: bytes | None,
                   identity: Identity, message: str) -> dict:
    path = item.path
    relative = path.relative_to(root).as_posix()
    # Catch manual edits during validation before the atomic replacement.
    current = path.read_bytes() if path.exists() else None
    if current != original:
        raise DirtyRecordError(f"{relative}: uncommitted human edit during validation", path=relative)
    ensure_clean(root, path)
    before = run_git(root, "rev-parse", "HEAD")
    encoded = serialize_record(item.record, item.body)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(path, encoded)
        commit = commit_file(root, path, identity, message)
    except (OSError, ValueError) as exc:
        if run_git(root, "rev-parse", "HEAD") != before:
            raise WriteError(f"{relative}: Git HEAD changed during failed write; inspect before retrying",
                             path=relative, committed="unknown") from exc
        current = path.read_bytes() if path.exists() else None
        if current not in (original, encoded):
            raise WriteError(f"{relative}: file changed during failed write; human edits preserved",
                             path=relative) from exc
        if current != original:
            if original is None:
                path.unlink(missing_ok=True)
            else:
                write_atomic(path, original)
        raise
    record = refresh_committed(root, item, commit)
    return {"record": record, "commit": commit}


def refresh_committed(root: Path, item: ParsedRecord, commit: str) -> dict:
    """Refresh under the held lock; make post-commit failures unambiguous."""
    try:
        index = RecordIndex(root)
        index._rebuild_locked()
        return index._query_locked("WHERE id = ?", (item.record.id,))[0]
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise CommittedIndexError(
            f"{item.path.relative_to(root)}: record committed as {commit}; index refresh failed: {exc}",
            committed=True, commit=commit, id=item.record.id,
            current_version=item.record.version) from exc
