"""Project identity, explicit scope and cooperating-writer serialization."""

import fcntl
import json
import os
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import TimeMachineError
from .metadata import connect, initialize
from .security import atomic_write, encode, private_directory

MARKER = ".timemachine.json"
DEFAULT_EXCLUDES = [
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


def default_base() -> Path:
    if os.environ.get("XDG_DATA_HOME"):
        return Path(os.environ["XDG_DATA_HOME"]) / "timemachine"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/TimeMachine"
    return Path.home() / ".local/share/timemachine"


@dataclass(frozen=True)
class Project:
    root: Path
    store: Path
    config: dict[str, Any]

    @classmethod
    def init(cls, root: Path, storage: Path | None = None) -> "Project":
        if root.is_symlink():
            raise TimeMachineError("Project root cannot be a symlink")
        root = root.resolve(strict=True)
        if os.path.lexists(root / MARKER):
            raise TimeMachineError("Project already initialized; use status")
        identifier = uuid.uuid4().hex
        store = (storage or default_base() / identifier).expanduser().resolve()
        cls.validate_store(root, store)
        if store.exists() and any(store.iterdir()):
            raise TimeMachineError("Storage directory must be empty")
        private_directory(store)
        private_directory(store / "objects")
        config = {
            "version": 1,
            "id": identifier,
            "root": str(root),
            "storage": str(store),
            "exclude": DEFAULT_EXCLUDES.copy(),
            "max_file_bytes": 256 * 1024**2,
            "quota_bytes": 10 * 1024**3,
        }
        initialize(store)
        atomic_write(
            store / "project.json", encode({"version": 1, "id": identifier, "root": str(root)})
        )
        atomic_write(root / MARKER, encode(config))
        return cls(root, store, config)

    @staticmethod
    def validate_store(root: Path, store: Path) -> None:
        if store.is_relative_to(root) or root.is_relative_to(store) or ".git" in store.parts:
            raise TimeMachineError("Storage must be outside project and Git metadata")

    @classmethod
    def discover(cls, cwd: Path | None = None, *, allow_moved: bool = False) -> "Project":
        current = (cwd or Path.cwd()).resolve()
        for root in (current, *current.parents):
            marker = root / MARKER
            if not os.path.lexists(marker):
                continue
            if marker.is_symlink() or not marker.is_file():
                raise TimeMachineError("Project marker must be a regular file")
            try:
                config = json.loads(marker.read_bytes())
                if (
                    config["version"] != 1
                    or not isinstance(config["id"], str)
                    or not isinstance(config["exclude"], list)
                    or not all(isinstance(p, str) for p in config["exclude"])
                    or type(config["max_file_bytes"]) is not int
                    or type(config["quota_bytes"]) is not int
                    or config["max_file_bytes"] < 0
                    or config["quota_bytes"] < 0
                ):
                    raise ValueError("Invalid schema")
                raw_store = Path(config["storage"])
                store = raw_store.resolve(strict=True)
                if not raw_store.is_absolute() or raw_store.is_symlink():
                    raise ValueError("Storage must be an absolute real directory")
                cls.validate_store(root, store)
                identity = json.loads((store / "project.json").read_bytes())
                if identity["id"] != config["id"] or identity["version"] != 1:
                    raise ValueError("Project identity mismatch")
                if not allow_moved and (
                    config["root"] != str(root) or identity["root"] != str(root)
                ):
                    raise TimeMachineError("Project moved: run timemachine rebind explicitly")
                return cls(root, store, config)
            except (KeyError, ValueError, OSError, TypeError) as exc:
                raise TimeMachineError(f"Invalid project configuration: {exc}") from exc
        raise TimeMachineError("No initialized project found; run timemachine init")

    @contextmanager
    def lock(self, *, allow_pending: bool = False) -> Iterator[None]:
        fd = os.open(self.store / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise TimeMachineError(
                    "Project busy: another TimeMachine writer holds the lock"
                ) from exc
            if not allow_pending:
                with connect(self.store) as db:
                    pending = db.execute(
                        "SELECT id FROM transactions "
                        "WHERE status NOT IN ('COMPLETE','RECOVERED') LIMIT 1"
                    ).fetchone()
                if pending:
                    raise TimeMachineError(f"Unfinished restore {pending[0]}; run doctor/recover")
            yield
        finally:
            os.close(fd)
