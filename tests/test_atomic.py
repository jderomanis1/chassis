import os
import subprocess
import sys

import pytest

from chassis import atomic


def test_write_atomic_syncs_complete_sibling_before_replace(tmp_path, monkeypatch):
    target = tmp_path / "record.md"
    target.write_bytes(b"old bytes")
    events = []
    sync, replace = os.fsync, os.replace

    def synced(fd):
        events.append("sync")
        sync(fd)

    def replaced(source, destination):
        assert source.parent == target.parent
        assert source.read_bytes() == b"new bytes"
        assert target.read_bytes() == b"old bytes"
        assert events == ["sync"]
        events.append("replace")
        replace(source, destination)

    monkeypatch.setattr(atomic.os, "fsync", synced)
    monkeypatch.setattr(atomic.os, "replace", replaced)
    atomic.write_atomic(target, b"new bytes")
    assert target.read_bytes() == b"new bytes"
    assert list(tmp_path.iterdir()) == [target]


def test_crash_before_replace_preserves_original(tmp_path):
    target = tmp_path / "record.md"
    target.write_bytes(b"original complete file")
    result = subprocess.run([sys.executable, "-c", """
import os, sys
from pathlib import Path
from chassis import atomic
atomic.os.replace = lambda *args: os._exit(73)
atomic.write_atomic(Path(sys.argv[1]), b'complete replacement')
""", str(target)], capture_output=True)
    assert result.returncode == 73
    assert target.read_bytes() == b"original complete file"
    leftovers = [path for path in tmp_path.iterdir() if path != target]
    assert len(leftovers) == 1 and leftovers[0].read_bytes() == b"complete replacement"


def test_failed_replace_cleans_temporary_file(tmp_path, monkeypatch):
    target = tmp_path / "record.md"
    target.write_bytes(b"original")

    def failed(*args):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(atomic.os, "replace", failed)
    with pytest.raises(OSError, match="simulated replacement failure"):
        atomic.write_atomic(target, b"replacement")
    assert target.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [target]


def test_lock_excludes_another_process_and_releases(tmp_path):
    probe = """
import fcntl, sys
with open(sys.argv[1], 'rb') as handle:
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(42)
"""
    command = [sys.executable, "-c", probe, str(tmp_path / ".chassis/write.lock")]
    with atomic.vault_lock(tmp_path):
        assert subprocess.run(command).returncode == 42
    assert subprocess.run(command).returncode == 0
