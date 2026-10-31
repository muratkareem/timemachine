"""Versioned transactional metadata; blobs are external immutable files."""

import json
import sqlite3
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .errors import IntegrityError

CURRENT_SCHEMA = 2
MIGRATION_2 = (
    "CREATE TABLE IF NOT EXISTS journal_steps ("
    "transaction_id TEXT NOT NULL REFERENCES transactions(id), "
    "sequence INTEGER NOT NULL, record TEXT NOT NULL, PRIMARY KEY(transaction_id,sequence))",
    "CREATE INDEX IF NOT EXISTS checkpoint_time ON checkpoints(created)",
    "CREATE INDEX IF NOT EXISTS run_order ON runs(state,sequence)",
    "CREATE INDEX IF NOT EXISTS transaction_time ON transactions(created)",
)

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
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
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
        if version not in (1, CURRENT_SCHEMA):
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
        for statement in MIGRATION_2:
            db.execute(statement)
        db.execute(f"PRAGMA user_version={CURRENT_SCHEMA}")
        db.commit()
    except sqlite3.Error as exc:
        raise IntegrityError(f"Cannot initialize metadata database: {exc}") from exc
    finally:
        db.close()
    (store / "metadata.sqlite3").chmod(0o600)


def checkpoint_metadata(row: Any) -> None:
    """Validate mutable catalog fields before interpreting retention authority."""
    from .models import strict_pairs

    try:
        tags = json.loads(row["tags"], object_pairs_hook=strict_pairs)
        if (
            row["status"] not in ("COMPLETE", "INCOMPLETE")
            or row["pinned"] not in (0, 1)
            or not isinstance(tags, list)
            or not all(isinstance(t, str) and 0 < len(t) <= 128 for t in tags)
            or len(tags) != len(set(tags))
        ):
            raise IntegrityError("Invalid checkpoint catalog fields")
        if row["status"] == "INCOMPLETE" and (
            row["manifest"] is not None or row["digest"] is not None
        ):
            raise IntegrityError("Incomplete checkpoint has contradictory manifest data")
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise IntegrityError("Malformed checkpoint catalog") from exc


def health(db: sqlite3.Connection) -> None:
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise IntegrityError("SQLite integrity check failed; preserve the whole store")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise IntegrityError("Broken metadata references; preserve the whole store")
    for row in db.execute("SELECT * FROM checkpoints"):
        checkpoint_metadata(row)
    for row in db.execute("SELECT * FROM runs"):
        if (
            row["status"]
            not in (
                "RUNNING",
                "FINALIZING",
                "COMPLETE",
                "INTERRUPTED",
                "LAUNCH_FAILED",
                "LATE_POST",
            )
            or row["state"] not in ("applied", "undone", "invalidated")
            or type(row["sequence"]) is not int
            or row["sequence"] < 1
        ):
            raise IntegrityError("Invalid run metadata")
        for key in ("pre", "post"):
            if (
                row[key] is not None
                and db.execute("SELECT status FROM checkpoints WHERE id=?", (row[key],)).fetchone()[
                    0
                ]
                != "COMPLETE"
            ):
                raise IntegrityError("Run references an incomplete checkpoint")
    if db.execute("SELECT sequence FROM runs GROUP BY sequence HAVING count(*)>1").fetchone():
        raise IntegrityError("Ambiguous run ordering")
    for row in db.execute("SELECT * FROM transactions"):
        if row["status"] not in ("PROTECTED", "APPLYING", "FAILED", "COMPLETE", "RECOVERED"):
            raise IntegrityError("Invalid recovery transaction state")
        if (
            db.execute("SELECT status FROM checkpoints WHERE id=?", (row["recovery"],)).fetchone()[
                0
            ]
            != "COMPLETE"
        ):
            raise IntegrityError("Recovery references an incomplete checkpoint")


def require_current(db: sqlite3.Connection) -> None:
    if db.execute("PRAGMA user_version").fetchone()[0] != CURRENT_SCHEMA:
        raise IntegrityError("Catalog upgrade required: preview and run timemachine migrate --yes")


def migration_plan(store: Path) -> dict[str, Any]:
    with connect(store) as db:
        version = db.execute("PRAGMA user_version").fetchone()[0]
    return {
        "from_version": version,
        "to_version": CURRENT_SCHEMA,
        "needed": version < CURRENT_SCHEMA,
        "effect": "Add indexed recovery steps; preserve manifests, objects and old journals",
    }


def migrate(store: Path) -> dict[str, Any]:
    """Caller holds project lock. SQLite DDL/version changes commit together."""
    import os
    import uuid

    result = migration_plan(store)
    if not result["needed"]:
        return result
    with connect(store) as db:
        health(db)
        backup = store / ("catalog-v1-" + uuid.uuid4().hex + ".sqlite3")
        destination = sqlite3.connect(backup)
        try:
            db.backup(destination)
        finally:
            destination.close()
        backup.chmod(0o600)
        fd = os.open(backup, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        from .security import sync_dir

        sync_dir(store)
        db.execute("BEGIN IMMEDIATE")
        for statement in MIGRATION_2:
            db.execute(statement)
        db.execute(f"PRAGMA user_version={CURRENT_SCHEMA}")
    return {
        **result,
        "backup": str(backup),
        "backup_scope": "Catalog only; keep a whole-store backup for independent recovery",
    }
