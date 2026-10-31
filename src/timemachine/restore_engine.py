"""Journaled, no-follow per-entry restore. Caller holds the project writer lock."""

import hashlib
import os
import stat
import uuid
from collections.abc import Callable
from typing import Any

from .checkpoint import checkpoint, manifest, now
from .errors import ConflictError, IntegrityError
from .git_context import git_context
from .journal import pack
from .metadata import connect
from .models import Entry, fingerprint, mode_bits
from .objects import CHUNK, ObjectStore
from .project import Project
from .restore_plan import Change, Plan
from .scanner import scan
from .security import DIR_FLAGS, encode, parent_fd, safe_path


def observe(fd: int, name: str) -> tuple[Entry | None, tuple[int, ...] | None]:
    try:
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return None, None
    if stat.S_ISDIR(info.st_mode):
        value = Entry("directory", mode_bits(info.st_mode))
    elif stat.S_ISLNK(info.st_mode):
        value = Entry("symlink", 0o777, target=os.readlink(name, dir_fd=fd))
    elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
        source = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            if fingerprint(os.fstat(source)) != fingerprint(info):
                raise ConflictError("File identity changed before mutation")
            hasher = hashlib.sha256()
            size = 0
            while data := os.read(source, CHUNK):
                hasher.update(data)
                size += len(data)
            if fingerprint(os.fstat(source)) != fingerprint(info):
                raise ConflictError("File changed while revalidating")
            value = Entry("file", mode_bits(info.st_mode), size, hasher.hexdigest())
        finally:
            os.close(source)
    else:
        raise ConflictError("Unsupported entry encountered before mutation")
    if fingerprint(os.stat(name, dir_fd=fd, follow_symlinks=False)) != fingerprint(info):
        raise ConflictError("Path changed while revalidating")
    return value, fingerprint(info)


def execute(
    project: Project,
    plan: Plan,
    kind: str,
    run_id: str | None = None,
    hook: Callable[[str, str], None] | None = None,
) -> str | None:
    """hook is a deterministic fault-injection seam; never used by the CLI."""

    def check_context() -> None:
        if (
            plan.git_fingerprint is not None
            and encode(git_context(project.root)) != plan.git_fingerprint
        ):
            raise ConflictError("Git metadata changed after preview; preview and acknowledge again")
        for path, device, inode in plan.identities:
            if path:
                with parent_fd(project.root, path) as (fd, name):
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            else:
                info = project.root.lstat()
            if (info.st_dev, info.st_ino) != (device, inode):
                raise ConflictError(f"Path identity changed after preview: {path!r}")

    check_context()
    if not plan.changes and not plan.observed:
        return None
    paths = [safe_path(c.path) for c in plan.changes]
    if len(set(paths)) != len(paths):
        raise IntegrityError("Duplicate restore-plan paths")
    for change in plan.changes:
        if change.expected:
            change.expected.validate()
        if change.target:
            change.target.validate()
            if (
                change.target.kind == "symlink"
                and project.config.get("symlink_policy", "record") == "reject"
            ):
                raise ConflictError("Symlink target refused by current policy")
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    for change in plan.changes:
        if change.target and change.target.digest:
            objects.verify(change.target.digest, change.target.size)
    initial = scan(project)
    for path, value in plan.observed:
        if initial.entries.get(path) != value:
            raise ConflictError(f"Path changed after preview: {path!r}")
    if not plan.changes:
        return None
    for change in plan.changes:
        if initial.entries.get(change.path) != change.expected:
            raise ConflictError(f"Plan stale before recovery checkpoint: {change.path!r}")
    recovery = checkpoint(project, f"Recovery before {kind}", "recovery")
    recovery_entries = manifest(project, recovery)
    for change in plan.changes:
        if recovery_entries.get(change.path) != change.expected:
            raise ConflictError(f"Plan changed during recovery checkpoint: {change.path!r}")
    check_context()
    identifier = uuid.uuid4().hex
    with connect(project.store) as db:
        db.execute(
            "INSERT INTO transactions(id,created,kind,status,recovery,plan,run_id,progress) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                identifier,
                now(),
                kind,
                "PROTECTED",
                recovery,
                pack("plan", plan.data()),
                run_id,
                pack("progress", []),
            ),
        )
    progress: list[dict[str, Any]] = []
    expected = {c.path: c.expected for c in plan.changes}
    identities = {p: (v[0], v[1]) for p, v in initial.identities.items()}
    root_info = project.root.stat()
    root_identity = root_info.st_dev, root_info.st_ino

    def journal(path: str, action: str, state: str) -> None:
        progress.append({"path": path, "action": action, "state": state})
        with connect(project.store) as db:
            db.execute(
                "UPDATE transactions SET status='APPLYING',progress=? WHERE id=?",
                (pack("progress", progress), identifier),
            )

    def guard(path: str) -> None:
        current_root = project.root.lstat()
        if (current_root.st_dev, current_root.st_ino) != root_identity:
            raise ConflictError("Root identity changed")
        parent = path.rpartition("/")[0]
        while parent:
            with parent_fd(project.root, parent) as (fd, name):
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if not stat.S_ISDIR(info.st_mode) or identities.get(parent) != (
                    info.st_dev,
                    info.st_ino,
                ):
                    raise ConflictError(f"Ancestor identity changed: {parent!r}")
            parent = parent.rpartition("/")[0]

    def mutate(change: Change, action: str) -> None:
        path = change.path
        if hook:
            hook(path, action)
        guard(path)
        journal(path, action, "before")
        with parent_fd(project.root, path) as (fd, name):
            actual, identity = observe(fd, name)
            if actual != expected[path]:
                raise ConflictError(f"Concurrent edit before mutation: {path!r}")
            if identity is not None and identities.get(path) != identity[:2]:
                raise ConflictError(f"Path identity changed: {path!r}")
            parent = path.rpartition("/")[0]
            expected_parent = identities.get(parent) if parent else root_identity
            parent_info = os.fstat(fd)
            if (parent_info.st_dev, parent_info.st_ino) != expected_parent:
                raise ConflictError(f"Parent identity changed before mutation: {path!r}")
            guard(path)
            target = change.target
            temporary = ".timemachine-stage-" + uuid.uuid4().hex
            try:
                if action == "remove":
                    if actual and actual.kind == "directory":
                        os.rmdir(name, dir_fd=fd)
                    else:
                        os.unlink(name, dir_fd=fd)
                    expected[path] = None
                    identities.pop(path, None)
                elif action == "directory":
                    assert target is not None
                    # Temporary writable mode; final directory modes applied last.
                    os.mkdir(name, 0o700, dir_fd=fd)
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    expected[path] = Entry("directory", 0o700)
                    identities[path] = (info.st_dev, info.st_ino)
                elif action == "mode":
                    assert target is not None
                    directory_fd = os.open(name, DIR_FLAGS, dir_fd=fd)
                    try:
                        if fingerprint(os.fstat(directory_fd)) != identity:
                            raise ConflictError("Directory changed before mode update")
                        os.fchmod(directory_fd, target.mode)
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                    expected[path] = target
                else:
                    assert target is not None
                    if target.kind == "symlink":
                        assert target.target is not None
                        os.symlink(target.target, temporary, dir_fd=fd)
                    else:
                        assert target.digest is not None
                        stage = os.open(
                            temporary,
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                            0o600,
                            dir_fd=fd,
                        )
                        try:
                            # Stream verified objects without loading large files into RAM.
                            objects.verify(target.digest, target.size)
                            source = os.open(
                                objects.path(target.digest), os.O_RDONLY | os.O_NOFOLLOW
                            )
                            hasher = hashlib.sha256()
                            count = 0
                            try:
                                while data := os.read(source, CHUNK):
                                    hasher.update(data)
                                    count += len(data)
                                    view = memoryview(data)
                                    while view:
                                        written = os.write(stage, view)
                                        if written <= 0:
                                            raise OSError("No progress writing staged file")
                                        view = view[written:]
                            finally:
                                os.close(source)
                            if hasher.hexdigest() != target.digest or count != target.size:
                                raise IntegrityError("Object changed while staging")
                            os.fchmod(stage, target.mode)
                            os.fsync(stage)
                        finally:
                            os.close(stage)
                    # Staging may be slow. Revalidate again immediately before replacement.
                    guard(path)
                    again, again_identity = observe(fd, name)
                    if again != actual or again_identity != identity:
                        raise ConflictError(f"Concurrent edit while staging: {path!r}")
                    os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
                    expected[path] = target
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    identities[path] = (info.st_dev, info.st_ino)
                os.fsync(fd)
            finally:
                try:
                    os.unlink(temporary, dir_fd=fd)
                except FileNotFoundError:
                    pass
        journal(path, action, "after")

    try:
        # Delete deepest first, including type transitions; never recursive delete.
        for change in sorted(plan.changes, key=lambda c: (-c.path.count("/"), c.path)):
            old, target = change.expected, change.target
            if old and (target is None or old.kind != target.kind):
                mutate(change, "remove")
        for change in sorted(plan.changes, key=lambda c: (c.path.count("/"), c.path)):
            target = change.target
            if target and target.kind == "directory" and expected[change.path] is None:
                mutate(change, "directory")
        for change in plan.changes:
            if change.target and change.target.kind != "directory":
                mutate(change, "write")
        for change in sorted(plan.changes, key=lambda c: (-c.path.count("/"), c.path)):
            if change.target and change.target.kind == "directory":
                mutate(change, "mode")
        final = scan(project)
        for change in plan.changes:
            if final.entries.get(change.path) != change.target:
                raise IntegrityError(f"Restore verification failed: {change.path!r}")
        with connect(project.store) as db:
            db.execute("UPDATE transactions SET status='COMPLETE' WHERE id=?", (identifier,))
            if run_id and kind == "undo":
                db.execute("UPDATE runs SET state='undone' WHERE id=?", (run_id,))
            if run_id and kind == "redo":
                db.execute("UPDATE runs SET state='applied' WHERE id=?", (run_id,))
            if kind == "restore":
                db.execute("UPDATE runs SET state='invalidated' WHERE state='undone'")
    except BaseException as exc:
        with connect(project.store) as db:
            db.execute(
                "UPDATE transactions SET status='FAILED',error=? WHERE id=?",
                (type(exc).__name__, identifier),
            )
        raise IntegrityError(
            f"Restore {identifier} incomplete; recovery checkpoint {recovery}. "
            "Run doctor and recover after stopping external writers."
        ) from exc
    return identifier
