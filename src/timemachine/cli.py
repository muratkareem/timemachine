"""Terminal adapter. Core services have no dependency on this module."""

import json
from pathlib import Path
from typing import Any

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
    output(project.config, json_mode)


def main() -> None:
    try:
        app()
    except (TimeMachineError, OSError) as exc:
        typer.echo(json.dumps({"error": str(exc)}, ensure_ascii=True), err=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
