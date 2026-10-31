"""Conservative retention and reference-safe garbage collection."""

import json
import os
import stat
from typing import Any

from .checkpoint import get_checkpoint, manifest, verify
from .errors import TimeMachineError
from .journal import read_plan
from .metadata import checkpoint_metadata, connect
from .objects import ObjectStore
from .project import Project
from .security import sync_dir


def live_objects(project: Project) -> set[str]:
    with connect(project.store) as db:
        rows = db.execute("SELECT id FROM checkpoints WHERE status='COMPLETE'").fetchall()
        transactions = db.execute("SELECT plan FROM transactions").fetchall()
    live: set[str] = set()
    for row in rows:
        live.update(e.digest for e in manifest(project, row["id"]).values() if e.digest)
    # Retain journal-described bytes too, including historical completed journals.
    for transaction in transactions:
        from .models import Entry

        for change in read_plan(transaction["plan"])["changes"]:
            for key in ("expected", "target"):
                if change[key]:
                    entry = Entry.from_dict(change[key])
                    if entry.digest:
                        live.add(entry.digest)
    return live


def storage(project: Project) -> dict[str, Any]:
    live = live_objects(project)
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    files = list(objects.directory.iterdir())
    with connect(project.store) as db:
        count = db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
    return {
        "storage": str(project.store),
        "checkpoints": count,
        "object_count": len(files),
        "object_bytes": sum(p.lstat().st_size for p in files),
        "live_objects": len(live),
        "quota_bytes": project.config["quota_bytes"],
        "unreferenced_objects": sorted(p.name for p in files if p.name not in live),
        "retention": "Referenced, pinned, tagged and recovery snapshots retained",
    }


def tag(project: Project, identifier: str, label: str) -> None:
    checkpoint = get_checkpoint(project, identifier)
    if not label or len(label) > 128:
        raise TimeMachineError("Tag must have 1–128 characters")
    tags = sorted(set(json.loads(checkpoint["tags"])) | {label})
    with connect(project.store) as db:
        db.execute("UPDATE checkpoints SET tags=? WHERE id=?", (json.dumps(tags), identifier))


def pin(project: Project, identifier: str) -> None:
    get_checkpoint(project, identifier)
    with connect(project.store) as db:
        db.execute("UPDATE checkpoints SET pinned=1 WHERE id=?", (identifier,))


def deletion_plan(project: Project, identifier: str) -> dict[str, Any]:
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM checkpoints WHERE id=?", (identifier,)).fetchone()
        run = db.execute(
            "SELECT id FROM runs WHERE pre=? OR post=? LIMIT 1", (identifier, identifier)
        ).fetchone()
        transaction = db.execute(
            "SELECT id FROM transactions WHERE recovery=? LIMIT 1", (identifier,)
        ).fetchone()
    if row is None:
        raise TimeMachineError("Unknown checkpoint")
    checkpoint_metadata(row)
    if row["pinned"] or json.loads(row["tags"]) or run or transaction or row["kind"] == "recovery":
        raise TimeMachineError("Checkpoint retained: pinned, tagged, run or recovery reference")
    return {"delete": identifier, "objects": "Retained until explicit gc; shared objects preserved"}


def delete(project: Project, identifier: str) -> dict[str, Any]:
    result = deletion_plan(project, identifier)
    with connect(project.store) as db:
        db.execute("DELETE FROM checkpoints WHERE id=?", (identifier,))
    return result


def gc(project: Project, *, dry_run: bool = True) -> dict[str, Any]:
    # Manifest corruption prevents collection. Verify every live journal object too.
    verify(project)
    live = live_objects(project)
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    for digest in live:
        objects.verify(digest)
    candidates = [p for p in objects.directory.iterdir() if p.name not in live]
    for path in candidates:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise TimeMachineError("Unexpected object-store entry; inspect manually")
        if not (path.name.startswith(".tmp-") or len(path.name) == 64):
            raise TimeMachineError("Unexpected object-store filename; inspect manually")
    result = {
        "dry_run": dry_run,
        "objects": sorted(p.name for p in candidates),
        "reclaim_bytes": sum(p.lstat().st_size for p in candidates),
    }
    if not dry_run:
        for path in candidates:
            os.unlink(path)
        sync_dir(objects.directory)
    return result


def prune(project: Project, keep: int, *, preview: bool = True) -> dict[str, Any]:
    if keep < 0:
        raise TimeMachineError("keep must be nonnegative")
    with connect(project.store) as db:
        rows = db.execute("SELECT id FROM checkpoints ORDER BY created DESC").fetchall()
    candidates = []
    for row in rows[keep:]:
        try:
            deletion_plan(project, row["id"])
        except TimeMachineError:
            continue
        candidates.append(row["id"])
    if not preview:
        for identifier in candidates:
            delete(project, identifier)
    return {
        "preview": preview,
        "keep_recent": keep,
        "delete": candidates,
        "retained_references": "All run/recovery/tag/pin references preserved",
    }
