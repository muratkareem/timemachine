"""Checkpoints become COMPLETE only after stable scans and durable object writes."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from .errors import IntegrityError, TimeMachineError
from .git_context import git_context
from .journal import read_plan, read_progress
from .metadata import connect
from .models import Entry, Manifest, dump_manifest, load_manifest
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
    try:
        result["entries"] = load_manifest(bytes(row["manifest"]), row["digest"])
        result["git"] = json.loads(row["git"])
        if not isinstance(result["git"], dict):
            raise IntegrityError("Invalid checkpoint Git context")
    except (ValueError, TypeError) as exc:
        raise IntegrityError("Corrupt checkpoint metadata") from exc
    return result


def manifest(project: Project, identifier: str) -> Manifest:
    entries: Manifest = get_checkpoint(project, identifier)["entries"]
    return entries


def verify(project: Project) -> dict[str, Any]:
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    with connect(project.store) as db:
        rows = db.execute("SELECT id,status FROM checkpoints").fetchall()
        journals = db.execute("SELECT plan,progress FROM transactions").fetchall()
    checked: dict[str, int] = {}

    def check(entry: Entry) -> None:
        if entry.digest:
            if entry.digest in checked:
                if checked[entry.digest] != entry.size:
                    raise IntegrityError("Conflicting sizes for a shared object")
            else:
                objects.verify(entry.digest, entry.size)
                checked[entry.digest] = entry.size

    complete = 0
    for row in rows:
        if row["status"] != "COMPLETE":
            continue
        complete += 1
        for entry in manifest(project, row["id"]).values():
            check(entry)
    for journal in journals:
        plan = read_plan(journal["plan"])
        read_progress(journal["progress"])
        for change in plan["changes"]:
            for key in ("expected", "target"):
                if change[key]:
                    entry = Entry.from_dict(change[key])
                    check(entry)
    return {
        "journals_verified": len(journals),
        "complete_checkpoints": complete,
        "objects_verified": len(checked),
        "incomplete_checkpoints": len(rows) - complete,
        "integrity": "verified",
    }
