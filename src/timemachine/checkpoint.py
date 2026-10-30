"""Checkpoints become COMPLETE only after stable scans and durable object writes."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from .errors import IntegrityError, TimeMachineError
from .git_context import git_context
from .metadata import connect
from .models import Manifest, dump_manifest, load_manifest
from .objects import ObjectStore
from .project import Project
from .scanner import scan


def now() -> str:
    return datetime.now(UTC).isoformat()


def checkpoint(project: Project, message: str = "", kind: str = "manual") -> str:
    """Caller must hold project lock."""
    identifier = uuid.uuid4().hex
    with connect(project.store) as db:
        db.execute(
            "INSERT INTO checkpoints(id,created,message,kind,status) VALUES(?,?,?,?,?)",
            (identifier, now(), message, kind, "INCOMPLETE"),
        )
    before_git = git_context(project.root)
    first = scan(project, capture=True)
    second = scan(project)
    if (
        first.entries != second.entries
        or first.identities != second.identities
        or first.excluded != second.excluded
        or before_git != git_context(project.root)
    ):
        raise IntegrityError("Project changed during checkpoint; left INCOMPLETE")
    raw = dump_manifest(first.entries)
    with connect(project.store) as db:
        db.execute(
            "UPDATE checkpoints SET status='COMPLETE',manifest=?,digest=?,git=? WHERE id=?",
            (raw, hashlib.sha256(raw).hexdigest(), json.dumps(before_git), identifier),
        )
    return identifier


def get_checkpoint(project: Project, identifier: str) -> dict[str, Any]:
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM checkpoints WHERE id=?", (identifier,)).fetchone()
    if row is None:
        raise TimeMachineError(f"Unknown checkpoint: {identifier!r}")
    if row["status"] != "COMPLETE":
        raise IntegrityError("Checkpoint is INCOMPLETE and cannot be selected")
    result = dict(row)
    result["entries"] = load_manifest(bytes(row["manifest"]), row["digest"])
    result["git"] = json.loads(row["git"])
    return result


def manifest(project: Project, identifier: str) -> Manifest:
    entries: Manifest = get_checkpoint(project, identifier)["entries"]
    return entries


def verify(project: Project) -> dict[str, Any]:
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    with connect(project.store) as db:
        rows = db.execute("SELECT id,status FROM checkpoints").fetchall()
    checked: set[str] = set()
    complete = 0
    for row in rows:
        if row["status"] != "COMPLETE":
            continue
        complete += 1
        for entry in manifest(project, row["id"]).values():
            if entry.digest and entry.digest not in checked:
                objects.verify(entry.digest, entry.size)
                checked.add(entry.digest)
    return {
        "complete_checkpoints": complete,
        "objects_verified": len(checked),
        "incomplete_checkpoints": len(rows) - complete,
        "integrity": "verified",
    }
