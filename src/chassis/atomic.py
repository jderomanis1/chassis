"""Shared POSIX process lock and the single file-replacement primitive."""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile


@contextmanager
def vault_lock(root: Path):
    """Serialize Chassis writes and cache changes; never unlink a live lock."""
    directory = root / ".chassis"
    path = directory / "write.lock"
    if directory.is_symlink() or path.is_symlink():
        raise ValueError(f"{path}: lock paths cannot be symlinks")
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)  # The kernel releases the lock, including after process exit.


def write_atomic(path: Path, data: bytes) -> None:
    """Flush a complete sibling temp file before replacing the destination."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"{path}: atomic destination cannot be a symlink")
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}-",
                                suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            if path.exists():
                os.fchmod(handle.fileno(), path.stat().st_mode & 0o777)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
