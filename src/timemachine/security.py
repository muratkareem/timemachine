"""POSIX boundary checks and durable private storage writes."""

import json
import os
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .errors import TimeMachineError

NOFOLLOW = os.O_NOFOLLOW
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | NOFOLLOW


def safe_path(path: str) -> str:
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or "\x00" in path
        or any(
            p.casefold() in ("", ".", "..", ".git", ".timemachine.json") for p in path.split("/")
        )
    ):
        raise TimeMachineError(f"Unsafe relative path: {path!r}")
    return path


def sync_dir(path: Path) -> None:
    fd = os.open(path, DIR_FLAGS)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_dir(path.parent)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)


def encode(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def private_directory(path: Path) -> None:
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise TimeMachineError("Storage must be a real directory owned by this user")
    os.chmod(path, 0o700)


@contextmanager
def parent_fd(root: Path, relative: str) -> Iterator[tuple[int, str]]:
    parts = safe_path(relative).split("/")
    fd = os.open(root, DIR_FLAGS)
    try:
        for component in parts[:-1]:
            next_fd = os.open(component, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd, parts[-1]
    finally:
        os.close(fd)


def read_json_object(path: Path, *, limit: int = 65536) -> dict[str, Any]:
    """Read bounded regular JSON metadata without following a final symlink."""
    from .errors import IntegrityError
    from .models import strict_pairs

    fd = os.open(path, os.O_RDONLY | NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            raise IntegrityError("Metadata must be a bounded, non-hardlinked regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise IntegrityError("Metadata exceeds size limit")
        value = json.loads(raw, object_pairs_hook=strict_pairs)
        if not isinstance(value, dict):
            raise IntegrityError("Metadata must be a JSON object")
        return value
    except (ValueError, TypeError) as exc:
        raise IntegrityError("Malformed JSON metadata") from exc
    finally:
        os.close(fd)
