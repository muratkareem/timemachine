"""Terminal adapter. Core services have no dependency on this module."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from .errors import TimeMachineError
from .project import Project

app = typer.Typer(no_args_is_help=True, help="Local checkpoints and safe undo for coding agents.")


def output(value: Any, json_mode: bool = False) -> None:
    # JSON escaping also protects terminal control sequences in all text output.
    typer.echo(json.dumps(value, ensure_ascii=True, indent=2 if not json_mode else None))


@app.command()
def init(
    storage: Path | None = typer.Option(None, help="Empty external snapshot directory"),
) -> None:
    """Initialize this directory without changing Git state."""
    project = Project.init(Path.cwd(), storage)
    output({"root": str(project.root), "storage": str(project.store), "initialized": True})


@app.command()
def status(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Show project identity and exact protection policy."""
    project = Project.discover()
    from .history import status as project_status

    output(project_status(project), json_mode)


def main() -> None:
    try:
        app()
    except (TimeMachineError, OSError) as exc:
        typer.echo(json.dumps({"error": str(exc)}, ensure_ascii=True), err=True)
        raise SystemExit(1) from exc


@app.command("checkpoint")
def checkpoint_command(
    message: str = typer.Option("", "-m", "--message"),
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Capture a stable, durable checkpoint."""
    from .checkpoint import checkpoint

    project = Project.discover()
    with project.lock():
        identifier = checkpoint(project, message)
    output({"id": identifier, "status": "COMPLETE"}, json_mode)


@app.command("list")
def list_command(
    limit: int = typer.Option(20, min=0), json_mode: bool = typer.Option(False, "--json")
) -> None:
    """List checkpoints, their sizes and integrity state."""
    from .history import checkpoints

    output(checkpoints(Project.discover(), limit), json_mode)


@app.command("show")
@app.command("inspect")
def show_command(checkpoint_id: str, json_mode: bool = typer.Option(False, "--json")) -> None:
    """Inspect a checkpoint manifest and Git context."""
    from .history import show

    output(show(Project.discover(), checkpoint_id), json_mode)


@app.command("history")
def history_command(
    limit: int = typer.Option(20, min=0), json_mode: bool = typer.Option(False, "--json")
) -> None:
    """Show checkpoints, agent runs and restores with their relationships."""
    from .history import history

    output(history(Project.discover(), limit), json_mode)


@app.command("diff")
def diff_command(
    checkpoint_a: Annotated[str | None, typer.Argument()] = None,
    checkpoint_b: Annotated[str | None, typer.Argument()] = None,
    stat: bool = False,
    name_only: bool = False,
    path: str | None = None,
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Compare checkpoints; no IDs selects the latest completed run."""
    from .diff import compare

    result = compare(
        Project.discover(), checkpoint_a, checkpoint_b, path, include_text=not (stat or name_only)
    )
    if name_only:
        result = {"paths": [c["path"] for c in result["changes"]]}
    output(result, json_mode)


@app.command("doctor")
def doctor_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Verify integrity and report unfinished work without automatic rollback."""
    from .history import doctor

    project = Project.discover()
    with project.lock(allow_pending=True):
        output(doctor(project), json_mode)


@app.command("verify")
def verify_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Validate all retained complete manifests and referenced objects."""
    from .checkpoint import verify

    project = Project.discover()
    with project.lock(allow_pending=True):
        output(verify(project), json_mode)


def confirm(preview: bool, yes: bool, json_mode: bool, plan: dict[str, Any]) -> bool:
    if preview:
        output(plan, json_mode)
        return False
    if plan.get("warnings") and not json_mode:
        output({"warnings": plan["warnings"]}, json_mode)
    if not yes:
        if json_mode:
            raise TimeMachineError("Noninteractive mutation requires --yes or --preview")
        output(plan)
        if not typer.confirm("Apply this filesystem operation (recovery checkpoint retained)?"):
            raise typer.Abort()
    return True


@app.command("undo")
def undo_command(
    preview: bool = False, yes: bool = False, json_mode: bool = typer.Option(False, "--json")
) -> None:
    """Undo the latest applied run, refusing newer conflicting edits."""
    from .operations import undo, undo_plan

    project = Project.discover()
    with project.lock():
        _, plan = undo_plan(project)
        if confirm(preview, yes, json_mode, plan.data()):
            output(undo(project, acknowledge_git=True), json_mode)


@app.command("recover")
def recover_command(
    transaction_id: str,
    preview: bool = False,
    yes: bool = False,
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Recover a partial restore explicitly; refuse subsequent conflicting edits."""
    from .operations import recover

    project = Project.discover()
    with project.lock(allow_pending=True):
        plan = recover(project, transaction_id, preview=True)
        if confirm(preview, yes, json_mode, plan):
            output(recover(project, transaction_id), json_mode)


@app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_command(ctx: typer.Context) -> None:
    """Checkpoint and execute: run -- COMMAND [ARGS...]; inherit terminal and env."""
    from .runner import run

    project = Project.discover()
    args = ctx.args
    if args and args[0] == "--":
        args = args[1:]
    with project.lock():
        result = run(project, args)
    typer.echo(json.dumps(result, ensure_ascii=True), err=True)
    raise typer.Exit(result["exit_code"])


@app.command("finish-run")
def finish_run_command(run_id: str, yes: bool = False) -> None:
    """Record a late POST for a crashed run after stopping all external writers."""
    from .runner import finish_run

    project = Project.discover()
    with project.lock(allow_unfinished=True):
        if confirm(False, yes, False, {}):
            output(finish_run(project, run_id))


@app.command("redo")
def redo_command(
    preview: bool = False, yes: bool = False, json_mode: bool = typer.Option(False, "--json")
) -> None:
    """Replay the most recently undone run, refusing newer conflicting edits."""
    from .operations import redo, redo_plan

    project = Project.discover()
    with project.lock():
        _, plan = redo_plan(project)
        if confirm(preview, yes, json_mode, plan.data()):
            output(redo(project, acknowledge_git=True), json_mode)


@app.command("restore")
def restore_command(
    checkpoint_id: str,
    path: str | None = None,
    preview: bool = False,
    yes: bool = False,
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Restore all protected entries or a selected relative file/directory."""
    from .operations import restore, restore_plan

    project = Project.discover()
    with project.lock():
        plan = restore_plan(project, checkpoint_id, path)
        if confirm(preview, yes, json_mode, plan.data()):
            output(restore(project, checkpoint_id, path, plan=plan), json_mode)


@app.command("rebind")
def rebind_command(yes: bool = False) -> None:
    """Explicitly bind a moved project identity to its current canonical root."""
    from .security import atomic_write, encode

    project = Project.discover(allow_moved=True)
    with project.lock():
        if confirm(False, yes, False, {}):
            config = {**project.config, "root": str(project.root)}
            atomic_write(
                project.store / "project.json",
                encode({"id": config["id"], "version": 1, "root": str(project.root)}),
            )
            atomic_write(project.root / ".timemachine.json", encode(config))
            output({"rebound": str(project.root), "id": config["id"]})


@app.command("storage")
def storage_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Report deduplicated bytes, quota, live references and reclaimable objects."""
    from .retention import storage

    project = Project.discover()
    with project.lock(allow_pending=True):
        output(storage(project), json_mode)


@app.command("tag")
def tag_command(checkpoint_id: str, label: str) -> None:
    """Attach a retention-protecting label to a complete checkpoint."""
    from .retention import tag

    project = Project.discover()
    with project.lock():
        tag(project, checkpoint_id, label)
    output({"tagged": checkpoint_id, "label": label})


@app.command("pin")
def pin_command(checkpoint_id: str) -> None:
    """Retain a complete checkpoint against deletion/pruning."""
    from .retention import pin

    project = Project.discover()
    with project.lock():
        pin(project, checkpoint_id)
    output({"pinned": checkpoint_id})


@app.command("delete")
def delete_command(checkpoint_id: str, preview: bool = False, yes: bool = False) -> None:
    """Delete an unreferenced, unpinned, untagged checkpoint; gc is separate."""
    from .retention import delete, deletion_plan

    project = Project.discover()
    with project.lock():
        plan = deletion_plan(project, checkpoint_id)
        if confirm(preview, yes, False, plan):
            output(delete(project, checkpoint_id))


@app.command("gc")
def gc_command(dry_run: bool = False, yes: bool = False) -> None:
    """Collect only unreferenced objects after integrity verification."""
    from .retention import gc

    project = Project.discover()
    with project.lock():
        plan = gc(project)
        if confirm(dry_run, yes, False, plan):
            output(gc(project, dry_run=False))


@app.command("prune")
def prune_command(
    keep: int = typer.Option(20, min=0), preview: bool = False, yes: bool = False
) -> None:
    """Prune older unreferenced manual checkpoints, retaining protected history."""
    from .retention import prune

    project = Project.discover()
    with project.lock():
        plan = prune(project, keep)
        if confirm(preview, yes, False, plan):
            output(prune(project, keep, preview=False))


@app.command("tui")
def tui_command() -> None:
    """Browse real checkpoints, file previews and confirmed restores interactively."""
    try:
        from .tui.app import TimeMachineApp
    except ImportError as exc:
        raise TimeMachineError(
            "Install the optional TUI: pip install 'timemachine-cli[tui]'"
        ) from exc
    TimeMachineApp(Project.discover()).run()


@app.command("agents")
def agents_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Discover agent executables without launching them or requiring accounts."""
    from .integrations import capabilities

    output(capabilities(), json_mode)


if __name__ == "__main__":
    main()
