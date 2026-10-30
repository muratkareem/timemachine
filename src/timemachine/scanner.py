"""No-follow, descriptor-relative scanning with observed-race detection."""

import fnmatch
import hashlib
import os
import stat
import unicodedata
from dataclasses import dataclass

from .errors import IntegrityError, TimeMachineError
from .models import Entry, Manifest, fingerprint, mode_bits
from .objects import CHUNK, ObjectStore
from .project import MARKER, Project
from .security import DIR_FLAGS, safe_path


@dataclass
class Scan:
    entries: Manifest
    excluded: list[str]
    identities: dict[str, tuple[int, ...]]


def excluded(project: Project, path: str) -> bool:
    parts = path.split("/")
    if ".git" in parts or MARKER in parts:
        return True
    return any(
        fnmatch.fnmatchcase(path, p) or any(fnmatch.fnmatchcase(c, p) for c in parts)
        for p in project.config["exclude"]
    )


def scan(project: Project, *, capture: bool = False) -> Scan:
    entries: Manifest = {}
    skipped: list[str] = []
    identities: dict[str, tuple[int, ...]] = {}
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    portable: set[str] = set()

    def walk(directory_fd: int, prefix: str) -> None:
        directory_before = os.fstat(directory_fd)
        names = sorted(os.listdir(directory_fd))
        for name in names:
            path = f"{prefix}/{name}" if prefix else name
            if excluded(project, path):
                skipped.append(path)
                continue
            safe_path(path)
            collision = unicodedata.normalize("NFC", path).casefold()
            if collision in portable:
                raise IntegrityError(f"Portable filename collision: {path!r}")
            portable.add(collision)
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            identities[path] = fingerprint(before)
            if stat.S_ISDIR(before.st_mode):
                fd = os.open(name, DIR_FLAGS, dir_fd=directory_fd)
                try:
                    if fingerprint(os.fstat(fd)) != fingerprint(before):
                        raise IntegrityError("Directory changed while opening")
                    entries[path] = Entry("directory", mode_bits(before.st_mode))
                    walk(fd, path)
                finally:
                    os.close(fd)
            elif stat.S_ISLNK(before.st_mode):
                target = os.readlink(name, dir_fd=directory_fd)
                entries[path] = Entry("symlink", 0o777, target=target)
            elif stat.S_ISREG(before.st_mode):
                if before.st_nlink != 1:
                    raise IntegrityError(f"Hardlinked file unsupported: {path!r}")
                if before.st_size > project.config["max_file_bytes"]:
                    raise TimeMachineError(f"File exceeds max_file_bytes: {path!r}")
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                try:
                    if fingerprint(os.fstat(fd)) != fingerprint(before):
                        raise IntegrityError("File changed while opening")
                    if capture:
                        digest, size = objects.put_fd(fd, project.config["max_file_bytes"])
                    else:
                        hasher = hashlib.sha256()
                        size = 0
                        while data := os.read(fd, CHUNK):
                            size += len(data)
                            if size > project.config["max_file_bytes"]:
                                raise TimeMachineError("File grew beyond max_file_bytes")
                            hasher.update(data)
                        digest = hasher.hexdigest()
                    if fingerprint(before) != fingerprint(os.fstat(fd)):
                        raise IntegrityError(f"File changed during scan: {path!r}")
                    entries[path] = Entry("file", mode_bits(before.st_mode), size, digest)
                finally:
                    os.close(fd)
            else:
                raise IntegrityError(f"Special filesystem entry unsupported: {path!r}")
            if fingerprint(before) != fingerprint(
                os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            ):
                raise IntegrityError(f"Entry changed during scan: {path!r}")
        if fingerprint(directory_before) != fingerprint(os.fstat(directory_fd)) or names != sorted(
            os.listdir(directory_fd)
        ):
            raise IntegrityError("Directory changed during scan")

    root_fd = os.open(project.root, DIR_FLAGS)
    try:
        walk(root_fd, "")
    finally:
        os.close(root_fd)
    return Scan(entries, skipped, identities)
