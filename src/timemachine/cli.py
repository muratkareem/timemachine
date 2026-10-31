"""Terminal adapter. Core services have no dependency on this module."""

import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated, Any

import typer

from .errors import TimeMachineError
from .presentation import console, guidance, human
from .project import Project
from .ui_data import resolve_checkpoint

app = typer.Typer(
    no_args_is_help=True,
    help="Ctrl+Z for coding agents. Local snapshots, safe recovery.",
    epilog="Start: timemachine quickstart. Automate: add --json. Nothing runs in the background.",
)


_human: ContextVar[bool] = ContextVar("human_output", default=False)
_plain: ContextVar[bool] = ContextVar("plain_output", default=False)


@app.callback()
def options(
    human_output: bool = typer.Option(
        False, "--human", help="Readable output, including in pipes."
    ),
    plain: bool = typer.Option(False, "--plain", help="Readable output without color/animation."),
) -> None:
    """Checkpoint → run your agent → inspect → preview undo. Use --json for automation."""
    _human.set(human_output or plain or sys.stdout.isatty())
    _plain.set(plain)


def output(value: Any, json_mode: bool = False) -> None:
    if json_mode or not _human.get():
        typer.echo(json.dumps(value, ensure_ascii=True, indent=None if json_mode else 2))
    else:
        console(plain=_plain.get()).print(human(value))


@contextmanager
def working(label: str, json_mode: bool = False) -> Iterator[None]:
    if (
        not json_mode
        and _human.get()
        and sys.stderr.isatty()
        and not _plain.get()
        and "NO_COLOR" not in os.environ
    ):
        with console(stderr=True).status(label, spinner="dots"):
            yield
    else:
        yield


@app.command()
def init(
    storage: Path | None = typer.Option(None, help="Empty external snapshot directory"),
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Initialize this directory without changing Git state."""
    project = Project.init(Path.cwd(), storage)
    result: dict[str, Any] = {
        "root": str(project.root),
        "storage": str(project.store),
        "initialized": True,
    }
    if _human.get() and not json_mode:
        from .scanner import scan

        try:
            scope = scan(project)
            result["scope"] = f"{len(scope.entries)} entries ready to capture (no backup yet)"
            result["exclusions"] = ", ".join(
                [".git", ".timemachine.json", *project.config["exclude"]]
            )
        except (TimeMachineError, OSError) as exc:
            result["scope"] = f"Needs attention before checkpoint: {exc}"
        output(result)
    else:
        output(result, json_mode)


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
        if _human.get() and "--json" not in sys.argv:
            from rich.panel import Panel
            from rich.text import Text

            from .presentation import safe

            console(plain=_plain.get(), stderr=True).print(
                Panel(Text(safe(exc) + "\n\n" + guidance(str(exc))), title="Cannot proceed")
            )
        else:
            typer.echo(json.dumps({"error": str(exc)}, ensure_ascii=True), err=True)
        raise SystemExit(1) from exc


@app.command("checkpoint", rich_help_panel="Everyday")
def checkpoint_command(
    message: str = typer.Option("", "-m", "--message"),
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Capture a stable, durable checkpoint."""
    from .checkpoint import checkpoint

    project = Project.discover()
    with project.lock(), working("Saving a verified checkpoint…", json_mode):
        identifier = checkpoint(project, message)
    output({"id": identifier, "status": "COMPLETE"}, json_mode)


@app.command("list", rich_help_panel="Everyday")
def list_command(
    limit: int = typer.Option(20, min=0), json_mode: bool = typer.Option(False, "--json")
) -> None:
    """List checkpoints, their sizes and integrity state."""
    from .history import checkpoints

    output(checkpoints(Project.discover(), limit), json_mode)


@app.command("show", rich_help_panel="Everyday")
@app.command("inspect", rich_help_panel="Everyday")
def show_command(checkpoint_id: str, json_mode: bool = typer.Option(False, "--json")) -> None:
    """Inspect a checkpoint manifest and Git context."""
    from .history import show

    project = Project.discover()
    output(show(project, resolve_checkpoint(project, checkpoint_id)), json_mode)


@app.command("history", rich_help_panel="Everyday")
def history_command(
    limit: int = typer.Option(20, min=0),
    json_mode: bool = typer.Option(False, "--json"),
    search: str | None = typer.Option(None, help="Filter this page by ID, agent or description"),
) -> None:
    """Show checkpoints, agent runs and restores with their relationships."""
    from .history import history

    result = history(Project.discover(), limit)
    if search:
        query = search.casefold()
        result = {
            key: [item for item in values if query in str(item).casefold()]
            for key, values in result.items()
        }
    output(result, json_mode)


@app.command("diff", rich_help_panel="Everyday")
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

    project = Project.discover()
    result = compare(
        project,
        resolve_checkpoint(project, checkpoint_a) if checkpoint_a else None,
        resolve_checkpoint(project, checkpoint_b) if checkpoint_b else None,
        path,
        include_text=not (stat or name_only),
    )
    if name_only:
        result = {"paths": [c["path"] for c in result["changes"]]}
    output(result, json_mode)


@app.command("doctor", rich_help_panel="Storage & diagnostics")
def doctor_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Verify integrity and report unfinished work without automatic rollback."""
    from .history import doctor

    project = Project.discover()
    with (
        project.lock(allow_pending=True),
        working("Checking integrity and recovery state…", json_mode),
    ):
        output(doctor(project), json_mode)


@app.command("verify", rich_help_panel="Storage & diagnostics")
def verify_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Validate all retained complete manifests and referenced objects."""
    from .checkpoint import verify

    project = Project.discover()
    with project.lock(allow_pending=True), working("Verifying saved data…", json_mode):
        output(verify(project), json_mode)


def confirm(preview: bool, yes: bool, json_mode: bool, plan: dict[str, Any]) -> bool:
    if preview:
        output(plan, json_mode)
        return False
    if plan.get("warnings") and not json_mode and yes:
        output({"warnings": plan["warnings"]}, json_mode)
    if not yes:
        if json_mode:
            raise TimeMachineError("Noninteractive mutation requires --yes or --preview")
        output(plan)
        if not typer.confirm("Apply this filesystem operation (recovery checkpoint retained)?"):
            raise typer.Abort()
    return True


@app.command("undo", rich_help_panel="Recovery")
def undo_command(
    preview: bool = False, yes: bool = False, json_mode: bool = typer.Option(False, "--json")
) -> None:
    """Undo the latest applied run, refusing newer conflicting edits."""
    from .operations import undo, undo_plan

    project = Project.discover()
    with project.lock():
        run_record, plan = undo_plan(project)
        if confirm(preview, yes, json_mode, plan.data()):
            output(
                undo(project, acknowledge_git=True, confirmed_plan=plan, run_id=run_record["id"]),
                json_mode,
            )


@app.command("recover", rich_help_panel="Recovery")
def recover_command(
    transaction_id: str,
    preview: bool = False,
    yes: bool = False,
    json_mode: bool = typer.Option(False, "--json"),
) -> None:
    """Recover a partial restore explicitly; refuse subsequent conflicting edits."""
    from .operations import recover, recovery_plan

    project = Project.discover()
    with project.lock(allow_pending=True):
        plan = recovery_plan(project, transaction_id)
        if confirm(preview, yes, json_mode, {"transaction": transaction_id, **plan.data()}):
            output(recover(project, transaction_id, confirmed_plan=plan), json_mode)


@app.command(
    "run",
    rich_help_panel="Everyday",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run_command(ctx: typer.Context) -> None:
    """Checkpoint and execute: run -- COMMAND [ARGS...]; inherit terminal and env."""
    from .runner import run

    project = Project.discover()
    args = ctx.args
    if args and args[0] == "--":
        args = args[1:]
    with project.lock():
        result = run(project, args)
    if _human.get():
        console(plain=_plain.get(), stderr=True).print(human(result))
        if result["status"] == "LAUNCH_FAILED":
            console(plain=_plain.get(), stderr=True).print(
                "Could not launch the executable. Check its path/permissions; "
                "timemachine agents lists detected tools. No raw arguments were logged."
            )
    else:
        typer.echo(json.dumps(result, ensure_ascii=True), err=True)
    raise typer.Exit(result["exit_code"])


@app.command("finish-run", rich_help_panel="Recovery")
def finish_run_command(run_id: str, yes: bool = False) -> None:
    """Record a late POST for a crashed run after stopping all external writers."""
    from .runner import finish_run

    project = Project.discover()
    with project.lock(allow_unfinished=True):
        if confirm(False, yes, False, {}):
            output(finish_run(project, run_id))


@app.command("redo", rich_help_panel="Recovery")
def redo_command(
    preview: bool = False, yes: bool = False, json_mode: bool = typer.Option(False, "--json")
) -> None:
    """Replay the most recently undone run, refusing newer conflicting edits."""
    from .operations import redo, redo_plan

    project = Project.discover()
    with project.lock():
        run_record, plan = redo_plan(project)
        if confirm(preview, yes, json_mode, plan.data()):
            output(
                redo(project, acknowledge_git=True, confirmed_plan=plan, run_id=run_record["id"]),
                json_mode,
            )


@app.command("restore", rich_help_panel="Recovery")
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
        checkpoint_id = resolve_checkpoint(project, checkpoint_id)
        plan = restore_plan(project, checkpoint_id, path)
        if confirm(preview, yes, json_mode, plan.data()):
            output(restore(project, checkpoint_id, path, plan=plan), json_mode)


@app.command("rebind", rich_help_panel="Recovery")
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


@app.command("storage", rich_help_panel="Storage & diagnostics")
def storage_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Report deduplicated bytes, quota, live references and reclaimable objects."""
    from .retention import storage

    project = Project.discover()
    with project.lock(allow_pending=True):
        output(storage(project), json_mode)


@app.command("tag", rich_help_panel="Storage & diagnostics")
def tag_command(checkpoint_id: str, label: str) -> None:
    """Attach a retention-protecting label to a complete checkpoint."""
    from .retention import tag

    project = Project.discover()
    with project.lock():
        checkpoint_id = resolve_checkpoint(project, checkpoint_id)
        tag(project, checkpoint_id, label)
    output({"tagged": checkpoint_id, "label": label})


@app.command("pin", rich_help_panel="Storage & diagnostics")
def pin_command(checkpoint_id: str) -> None:
    """Retain a complete checkpoint against deletion/pruning."""
    from .retention import pin

    project = Project.discover()
    with project.lock():
        checkpoint_id = resolve_checkpoint(project, checkpoint_id)
        pin(project, checkpoint_id)
    output({"pinned": checkpoint_id})


@app.command("delete", rich_help_panel="Storage & diagnostics")
def delete_command(checkpoint_id: str, preview: bool = False, yes: bool = False) -> None:
    """Delete an unreferenced, unpinned, untagged checkpoint; gc is separate."""
    from .retention import delete, deletion_plan

    project = Project.discover()
    with project.lock():
        checkpoint_id = resolve_checkpoint(project, checkpoint_id)
        plan = deletion_plan(project, checkpoint_id)
        if confirm(preview, yes, False, plan):
            output(delete(project, checkpoint_id))


@app.command("gc", rich_help_panel="Storage & diagnostics")
def gc_command(dry_run: bool = False, yes: bool = False) -> None:
    """Collect only unreferenced objects after integrity verification."""
    from .retention import gc

    project = Project.discover()
    with project.lock():
        plan = gc(project)
        if confirm(dry_run, yes, False, plan):
            output(gc(project, dry_run=False))


@app.command("prune", rich_help_panel="Storage & diagnostics")
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


@app.command("tui", rich_help_panel="Everyday")
def tui_command() -> None:
    """Browse real checkpoints, file previews and confirmed restores interactively."""
    try:
        from .tui.app import TimeMachineApp
    except ImportError as exc:
        raise TimeMachineError(
            "TUI extra missing. From the TimeMachine checkout: pip install -e '.[tui]'"
        ) from exc
    TimeMachineApp(Project.discover()).run()


@app.command("agents", rich_help_panel="Everyday")
def agents_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Discover agent executables without launching them or requiring accounts."""
    from .integrations import capabilities

    output(capabilities(), json_mode)


@app.command("quickstart", rich_help_panel="Everyday")
def quickstart_command(json_mode: bool = typer.Option(False, "--json")) -> None:
    """Learn the workflow and discover agents. Does not initialize or launch anything."""
    from .integrations import capabilities

    guide = {
        "workflow": "1. cd your/project  2. timemachine init  3. timemachine run -- COMMAND",
        "inspect": "timemachine diff · timemachine history · timemachine tui",
        "recover": "timemachine undo --preview, then timemachine undo",
        "scope": "Selected local files; exclusions and Git history are not restored",
        "automatic_protection": "None: wrap each session or create a checkpoint explicitly",
    }
    if json_mode or not _human.get():
        output({**guide, "agents": capabilities()}, json_mode)
    else:
        output(guide)
        output(capabilities())


@app.command("migrate", rich_help_panel="Storage & diagnostics")
def migrate_command(
    preview: bool = False, yes: bool = False, json_mode: bool = typer.Option(False, "--json")
) -> None:
    """Explicitly upgrade a v1 catalog; preserve existing snapshots and journals."""
    from .metadata import migrate, migration_plan

    project = Project.discover(allow_moved=True)
    with project.lock(allow_pending=True):
        plan = migration_plan(project.store)
        if confirm(preview, yes, json_mode, plan):
            output(migrate(project.store), json_mode)


if __name__ == "__main__":
    main()
