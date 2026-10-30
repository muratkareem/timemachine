"""Run-based undo services; no Git mutations."""

from typing import Any

from .checkpoint import get_checkpoint
from .diff import changed
from .errors import TimeMachineError
from .git_context import git_context
from .metadata import connect
from .project import Project
from .restore_engine import execute
from .restore_plan import Plan, make_plan


def undo_plan(project: Project) -> tuple[dict[str, Any], Plan]:
    with connect(project.store) as db:
        row = db.execute(
            "SELECT * FROM runs WHERE state='applied' AND post IS NOT NULL "
            "ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
    if row is None:
        raise TimeMachineError("No applied completed run to undo")
    run = dict(row)
    pre, post = get_checkpoint(project, run["pre"]), get_checkpoint(project, run["post"])
    warnings: tuple[str, ...] = ()
    if post["git"] != git_context(project.root) or pre["git"] != post["git"]:
        warnings = (
            "Git HEAD/branch/refs/index differ. Filesystem undo does not reverse Git changes.",
        )
    return run, make_plan(
        project, post["entries"], pre["entries"], changed(pre["entries"], post["entries"]), warnings
    )


def undo(project: Project, *, acknowledge_git: bool = False) -> dict[str, Any]:
    run, plan = undo_plan(project)
    if plan.warnings and not acknowledge_git:
        raise TimeMachineError(
            "Git metadata mismatch: preview and explicitly acknowledge with --yes"
        )
    transaction = execute(project, plan, "undo", run["id"])
    with connect(project.store) as db:
        db.execute("UPDATE runs SET state='undone' WHERE id=?", (run["id"],))
    return {"run": run["id"], "transaction": transaction, **plan.data()}


def recover(project: Project, transaction_id: str, *, preview: bool = False) -> dict[str, Any]:
    """Explicitly restore a failed transaction's pre-state, refusing later edits."""
    import json

    from .errors import ConflictError
    from .models import Entry
    from .scanner import scan
    from .security import safe_path

    with connect(project.store) as db:
        row = db.execute("SELECT * FROM transactions WHERE id=?", (transaction_id,)).fetchone()
    if row is None or row["status"] in ("COMPLETE", "RECOVERED"):
        raise TimeMachineError("No unfinished transaction with that ID")
    value = json.loads(row["plan"])
    progress = json.loads(row["progress"])
    current = scan(project)
    paths = []
    for change in value["changes"]:
        path = safe_path(change["path"])
        paths.append(path)
        old = Entry.from_dict(change["expected"]) if change["expected"] else None
        target = Entry.from_dict(change["target"]) if change["target"] else None
        allowed = [old, target]
        if any(p["path"] == path and p["action"] == "remove" for p in progress):
            allowed.append(None)
        if any(p["path"] == path and p["action"] == "directory" for p in progress):
            allowed.append(Entry("directory", 0o700))
        if current.entries.get(path) not in allowed:
            raise ConflictError(f"Recovery conflict: later edit at {path!r}; no files changed")
    recovery = get_checkpoint(project, row["recovery"])
    plan = make_plan(project, current.entries, recovery["entries"], paths)
    if preview:
        return {"transaction": transaction_id, **plan.data()}
    identifier = execute(project, plan, "recover")
    with connect(project.store) as db:
        db.execute("UPDATE transactions SET status='RECOVERED' WHERE id=?", (transaction_id,))
    return {"recovered": transaction_id, "transaction": identifier, **plan.data()}


def redo_plan(project: Project) -> tuple[dict[str, Any], Plan]:
    with connect(project.store) as db:
        row = db.execute(
            "SELECT * FROM runs WHERE state='undone' AND post IS NOT NULL "
            "ORDER BY sequence ASC LIMIT 1"
        ).fetchone()
    if row is None:
        raise TimeMachineError("No run available to redo")
    run = dict(row)
    pre, post = get_checkpoint(project, run["pre"]), get_checkpoint(project, run["post"])
    warnings: tuple[str, ...] = ()
    if post["git"] != git_context(project.root) or pre["git"] != post["git"]:
        warnings = ("Git metadata differs. Redo changes files only, never Git history/index.",)
    return run, make_plan(
        project, pre["entries"], post["entries"], changed(pre["entries"], post["entries"]), warnings
    )


def redo(project: Project, *, acknowledge_git: bool = False) -> dict[str, Any]:
    run, plan = redo_plan(project)
    if plan.warnings and not acknowledge_git:
        raise TimeMachineError(
            "Git metadata mismatch: preview and explicitly acknowledge with --yes"
        )
    transaction = execute(project, plan, "redo", run["id"])
    with connect(project.store) as db:
        db.execute("UPDATE runs SET state='applied' WHERE id=?", (run["id"],))
    return {"run": run["id"], "transaction": transaction, **plan.data()}


def restore_plan(project: Project, identifier: str, selector: str | None = None) -> Plan:
    from .diff import selected
    from .security import safe_path

    if selector is not None:
        safe_path(selector)
    from .scanner import scan

    target = get_checkpoint(project, identifier)
    current = scan(project)
    paths = [p for p in changed(current.entries, target["entries"]) if selected(p, selector)]
    # Selective child restore may need absent directory ancestors from the target.
    for path in tuple(paths):
        parent = path.rpartition("/")[0]
        while parent:
            if (
                parent not in current.entries
                and parent in target["entries"]
                and parent not in paths
            ):
                paths.append(parent)
            parent = parent.rpartition("/")[0]
    warnings: tuple[str, ...] = ()
    if target["git"] != git_context(project.root):
        warnings = ("Git metadata differs from checkpoint. Restore does not modify Git metadata.",)
    return make_plan(project, current.entries, target["entries"], sorted(paths), warnings)


def restore(
    project: Project, identifier: str, selector: str | None = None, *, plan: Plan | None = None
) -> dict[str, Any]:
    # Keep a confirmed immutable plan: do not rescan/rebase expected states after consent.
    intent = plan if plan is not None else restore_plan(project, identifier, selector)
    transaction = execute(project, intent, "restore")
    return {"checkpoint": identifier, "transaction": transaction, **intent.data()}
