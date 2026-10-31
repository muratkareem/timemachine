"""SHA-256 immutable object store; validate every read."""

import hashlib
import os
import re
import tempfile
from pathlib import Path

from .errors import IntegrityError, TimeMachineError
from .security import sync_dir

CHUNK = 1024 * 1024


class ObjectStore:
    def __init__(self, store: Path, quota: int):
        self.directory = store / "objects"
        self.quota = quota
        self._known_bytes: int | None = None

    def path(self, digest: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise IntegrityError("Invalid object ID")
        return self.directory / digest

    def usage(self) -> int:
        return sum(p.lstat().st_size for p in self.directory.iterdir())

    def put_fd(self, source: int, max_size: int) -> tuple[str, int]:
        if self._known_bytes is None:
            self._known_bytes = self.usage()
        fd, name = tempfile.mkstemp(prefix=".tmp-", dir=self.directory)
        hasher = hashlib.sha256()
        size = 0
        try:
            with os.fdopen(fd, "wb") as destination:
                while data := os.read(source, CHUNK):
                    size += len(data)
                    if size > max_size:
                        raise TimeMachineError("File exceeds max_file_bytes; checkpoint incomplete")
                    hasher.update(data)
                    destination.write(data)
                destination.flush()
                os.fsync(destination.fileno())
            digest = hasher.hexdigest()
            target = self.path(digest)
            if os.path.lexists(target):
                self.verify(digest, size)
            else:
                if self._known_bytes + size > self.quota:
                    raise TimeMachineError("Storage quota exceeded; checkpoint incomplete")
                os.replace(name, target)
                self._known_bytes += size
                sync_dir(self.directory)
                self.verify(digest, size)
            return digest, size
        finally:
            if os.path.lexists(name):
                os.unlink(name)

    def verify(self, digest: str, size: int | None = None) -> None:
        fd = os.open(self.path(digest), os.O_RDONLY | os.O_NOFOLLOW)
        try:
            from .models import fingerprint

            before = os.fstat(fd)
            import stat

            if not stat.S_ISREG(before.st_mode):
                raise IntegrityError("Object is not a regular file")
            hasher = hashlib.sha256()
            count = 0
            while data := os.read(fd, CHUNK):
                hasher.update(data)
                count += len(data)
            if (
                hasher.hexdigest() != digest
                or (size is not None and count != size)
                or fingerprint(before) != fingerprint(os.fstat(fd))
            ):
                raise IntegrityError(f"Object integrity failure: {digest}")
        finally:
            os.close(fd)

    def read(self, digest: str) -> bytes:
        self.verify(digest)
        fd = os.open(self.path(digest), os.O_RDONLY | os.O_NOFOLLOW)
        try:
            with os.fdopen(fd, "rb") as stream:
                data = stream.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise IntegrityError("Object changed during read")
            return data
        except BaseException:
            # fdopen owns fd once entered.
            raise
