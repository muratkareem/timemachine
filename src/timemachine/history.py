"""Structured read-only history, status and diagnostics."""

import json
from dataclasses import asdict
from typing import Any

from .checkpoint import get_checkpoint, verify
from .errors import TimeMachineError
from .git_context import git_context, path_categories
from .journal import read_plan, read_transaction_progress
from .metadata import connect
from .project import Project
from .scanner import scan


def checkpoints(project: Project, limit: int = 20) -> list[dict[str, Any]]:
    with connect(project.store) as db:
        rows = db.execute(
            "SELECT id,created,message,kind,status,pinned,tags FROM checkpoints "
            "ORDER BY created DESC LIMIT ?",
            (max(0, limit),),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item["tags"])
        if item["status"] == "COMPLETE":
            entries = get_checkpoint(project, item["id"])["entries"]
            item["entry_count"] = len(entries)
            item["size"] = sum(e.size for e in entries.values())
            item["integrity"] = "manifest verified; use verify for objects"
        else:
            item["integrity"] = "incomplete"
        result.append(item)
    return result


def show(project: Project, identifier: str) -> dict[str, Any]:
    result = get_checkpoint(project, identifier)
    del result["manifest"]
    result["tags"] = json.loads(result["tags"])
    result["entries"] = {p: asdict(e) for p, e in result["entries"].items()}
    return result


def history(project: Project, limit: int = 20) -> dict[str, Any]:
    with connect(project.store) as db:
        runs = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM runs ORDER BY sequence DESC LIMIT ?", (max(0, limit),)
            )
        ]
        transactions = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM transactions ORDER BY created DESC LIMIT ?", (max(0, limit),)
            )
        ]
    from .diff import compare

    for run in runs:
        if run["post"]:
            run["change_count"] = compare(project, run["pre"], run["post"], include_text=False)[
                "change_count"
            ]
    for run in runs:
        if run["post"]:
            entries = get_checkpoint(project, run["post"])["entries"]
            run["size"] = sum(e.size for e in entries.values())
            run["integrity"] = "manifests verified; use verify for objects"
    for transaction in transactions:
        transaction["plan"] = read_plan(transaction["plan"])
        with connect(project.store) as db:
            transaction["progress"] = read_transaction_progress(db, transaction)
        transaction["change_count"] = transaction["plan"]["change_count"]
    return {"checkpoints": checkpoints(project, limit), "runs": runs, "restores": transactions}


def status(project: Project) -> dict[str, Any]:
    result = scan(project)
    return {
        "project": project.config,
        "git": git_context(project.root),
        "included": sorted(result.entries),
        "categories": path_categories(project.root, set(result.entries)),
        "excluded": result.excluded,
        "protected_bytes": sum(e.size for e in result.entries.values()),
        "limitations": "Bytes/modes/links/directories only; see docs/SAFETY.md",
    }


def doctor(project: Project) -> dict[str, Any]:
    with connect(project.store) as db:
        stale = [
            dict(r)
            for r in db.execute(
                "SELECT id,pid,status FROM runs WHERE status IN ('RUNNING','FINALIZING')"
            )
        ]
        transactions = [
            dict(r)
            for r in db.execute(
                "SELECT id,status,recovery,error FROM transactions "
                "WHERE status NOT IN ('COMPLETE','RECOVERED')"
            )
        ]
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    verification = verify(project)
    try:
        scope = status(project)
    except (OSError, TimeMachineError) as exc:
        scope = {"error": str(exc), "policy": project.config}
    return {
        "scope": scope,
        "database": integrity,
        "verification": verification,
        "unfinished_runs": stale,
        "unfinished_restores": transactions,
        "guidance": "Quiesce writers. Recover unfinished restores explicitly; never auto-rollback.",
    }
