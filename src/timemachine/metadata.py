"""Versioned transactional metadata; blobs are external immutable files."""

import sqlite3
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .errors import IntegrityError

SCHEMA = """
CREATE TABLE IF NOT EXISTS checkpoints (
 id TEXT PRIMARY KEY, created TEXT NOT NULL, message TEXT NOT NULL,
 kind TEXT NOT NULL, status TEXT NOT NULL, manifest BLOB, digest TEXT,
 git TEXT, pinned INTEGER NOT NULL DEFAULT 0, tags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS runs (
 id TEXT PRIMARY KEY, created TEXT NOT NULL, agent TEXT NOT NULL,
 pre TEXT NOT NULL REFERENCES checkpoints(id), post TEXT REFERENCES checkpoints(id),
 status TEXT NOT NULL, exit_code INTEGER, pid INTEGER NOT NULL,
 state TEXT NOT NULL DEFAULT 'applied', sequence INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
 id TEXT PRIMARY KEY, created TEXT NOT NULL, kind TEXT NOT NULL,
 status TEXT NOT NULL, recovery TEXT NOT NULL REFERENCES checkpoints(id),
 plan TEXT NOT NULL, progress TEXT NOT NULL DEFAULT '[]', error TEXT,
 run_id TEXT REFERENCES runs(id)
);
"""


@contextmanager
def connect(store: Path) -> Iterator[sqlite3.Connection]:
    path = store / "metadata.sqlite3"
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise IntegrityError("Metadata database must be a regular file")
    except FileNotFoundError as exc:
        raise IntegrityError("Metadata database missing; restore a whole-store backup") from exc
    try:
        db = sqlite3.connect(path, timeout=0)
    except sqlite3.Error as exc:
        raise IntegrityError(f"Cannot open metadata database: {exc}") from exc
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version != 1:
            raise IntegrityError(f"Unsupported database schema: {version}")
        with db:
            yield db
    except sqlite3.Error as exc:
        raise IntegrityError(f"Metadata database failure: {exc}") from exc
    finally:
        db.close()


def initialize(store: Path) -> None:
    try:
        db = sqlite3.connect(store / "metadata.sqlite3")
    except sqlite3.Error as exc:
        raise IntegrityError(f"Cannot initialize metadata database: {exc}") from exc
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.executescript(SCHEMA)
        db.execute("PRAGMA user_version=1")
        db.commit()
    finally:
        db.close()
    (store / "metadata.sqlite3").chmod(0o600)
