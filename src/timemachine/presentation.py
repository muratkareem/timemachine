"""Shared safe text, semantic colors and human-friendly units; no core services."""

import os
import unicodedata
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

COLORS = {
    "primary": "#82D9C4",
    "protected": "#C4B5FD",
    "success": "#8ED6A4",
    "warning": "#F2CA82",
    "error": "#F397A4",
    "added": "#8ED6A4",
    "modified": "#F2CA82",
    "deleted": "#F397A4",
    "conflict": "#F397A4",
}


def safe(value: Any, *, multiline: bool = False) -> str:
    """Keep readable Unicode; escape controls, surrogates and direction overrides."""
    result = []
    for char in str(value):
        if multiline and char == "\n":
            result.append(char)
        elif multiline and char == "\t":
            result.append("    ")
        elif unicodedata.category(char).startswith("C"):
            result.append(f"\\u{ord(char):04x}")
        else:
            result.append(char)
    return "".join(result)


def size(value: int) -> str:
    number = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if number < 1024 or unit == "TiB":
            return f"{number:.0f} {unit}" if unit == "B" else f"{number:.1f} {unit}"
        number /= 1024
    return str(value)


def short(identifier: str) -> str:
    return identifier[:8]


def console(*, plain: bool = False, stderr: bool = False) -> Console:
    return Console(
        stderr=stderr,
        no_color=plain or "NO_COLOR" in os.environ,
        force_terminal=False if plain else None,
        highlight=False,
        markup=False,
    )


def table(title: str, columns: tuple[str, ...], rows: list[list[Any]]) -> Table:
    result = Table(title=title, title_style="bold", box=None, padding=(0, 1), expand=True)
    for column in columns:
        result.add_column(column, overflow="fold")
    for row in rows:
        result.add_row(*(Text(safe(v)) for v in row))
    return result


def guidance(error: str) -> str:
    lower = error.lower()
    if "no initialized" in lower:
        return "Open your project directory and run: timemachine init"
    if "no applied" in lower or "no completed run" in lower:
        return "Start a protected session: timemachine run -- COMMAND"
    if "conflict" in lower or "concurrent" in lower or "stale" in lower:
        return "Keep your newer edits. Copy them somewhere safe, stop writers, then preview again."
    if "corrupt" in lower or "integrity" in lower or "hash mismatch" in lower:
        return (
            "Stop recovery/GC. Preserve the store and run timemachine doctor; see docs/RECOVERY.md."
        )
    if "unfinished" in lower or "incomplete" in lower:
        return "Stop external writers and run timemachine doctor for explicit recovery steps."
    if "busy" in lower:
        return "Wait for the other TimeMachine operation to finish, then retry."
    return "No success is claimed. Run timemachine doctor or consult timemachine --help."


def human(value: Any) -> Any:
    """Render known service results; raw values remain available via --json."""
    if isinstance(value, list):
        if not value:
            return Panel(
                "No checkpoints yet. Run timemachine checkpoint or wrap your agent.",
                title="Your timeline",
                border_style=COLORS["protected"],
            )
        return table(
            "Checkpoints",
            ("ID", "UTC", "Description", "State", "Size"),
            [
                [
                    short(v["id"]),
                    v["created"][:16].replace("T", " "),
                    v["message"] or v["kind"],
                    v["status"],
                    size(v.get("size", 0)),
                ]
                for v in value
            ],
        )
    if not isinstance(value, dict):
        return Text(safe(value, multiline=True))
    if value.get("initialized"):
        return Panel(
            Text(
                f"Ready to checkpoint · {safe(value['root'])}\n\n"
                "Initialization does not create a backup or watch for changes.\n"
                "Protects selected file bytes, modes, directories and link targets.\n"
                f"Snapshots: {safe(value['storage'])}\n"
                f"Scope: {value.get('scope', 'use timemachine status')}\n"
                f"Exclusions: {safe(value.get('exclusions', 'see timemachine status'))}\n\n"
                "Next: timemachine run -- codex\n"
                "Then: timemachine diff · timemachine undo --preview"
            ),
            title="TimeMachine is ready",
            border_style=COLORS["primary"],
        )
    if "changes" in value:
        rows = []
        for change in value["changes"]:
            old, new = (
                change.get("before", change.get("expected")),
                change.get("after", change.get("target")),
            )
            kind = change.get("change") or (
                "added" if old is None else "deleted" if new is None else "modified"
            )
            rows.append([kind.upper(), change["path"], size((new or old or {}).get("size", 0))])
        from rich.console import Group

        parts: list[Any] = [
            table(
                f"{value.get('change_count', len(rows))} file changes",
                ("Change", "Path", "Size"),
                rows,
            )
        ]
        for warning in value.get("warnings", []):
            parts.append(Text("Warning: " + safe(warning), style=COLORS["warning"]))
        for change in value["changes"]:
            if change.get("diff"):
                from rich.syntax import Syntax

                parts.append(
                    Syntax(
                        safe(change["diff"], multiline=True),
                        "diff",
                        word_wrap=True,
                        background_color="default",
                    )
                )
            elif change.get("preview"):
                parts.append(Text(safe(change["path"]) + ": " + safe(change["preview"])))
        if value.get("transaction"):
            parts.append(
                Text("Verified. Recovery checkpoint and journal retained.", style=COLORS["success"])
            )
        return Group(*parts)
    if "checkpoints" in value and "runs" in value:
        from rich.console import Group

        sessions = table(
            "Agent sessions",
            ("Session", "Agent", "UTC", "State", "Changes"),
            [
                [
                    short(r["id"]),
                    r["agent"],
                    r["created"][:16].replace("T", " "),
                    f"{r['status']} / {r['state']} / exit {r['exit_code']}",
                    r.get("change_count", "?"),
                ]
                for r in value["runs"]
            ],
        )
        return Group(
            sessions,
            human(value["checkpoints"]),
            Text(
                f"{len(value['restores'])} recovery operations · diff to inspect · undo --preview"
            ),
        )
    if "included" in value:
        from rich.console import Group

        categories = value.get("categories", {})
        return Group(
            Panel(
                Text(
                    f"{safe(value['project']['root'])}\n"
                    f"{len(value['included'])} in scope · {size(value['protected_bytes'])}\n"
                    "Current files were scanned; a checkpoint is a separate action."
                ),
                title="Protection scope",
                border_style=COLORS["protected"],
            ),
            table(
                "Included",
                ("Category", "Paths"),
                [[k.replace("_", " "), ", ".join(v) or "—"] for k, v in categories.items()],
            ),
            Text("Excluded (not recoverable): " + safe(", ".join(value["excluded"]) or "none")),
            Text("Next: timemachine run -- COMMAND"),
        )
    if "database" in value:
        from rich.console import Group

        issues = len(value["unfinished_runs"]) + len(value["unfinished_restores"])
        return Group(
            Panel(
                Text(
                    f"Database: {value['database']} · {issues} unfinished operations\n"
                    f"Integrity: {value['verification']['integrity']}\n"
                    "No automatic rollback was performed."
                ),
                title="Doctor",
            ),
            human(value["scope"]),
            Text(safe(value["guidance"])),
        )
    if value and all(isinstance(v, dict) and "available" in v for v in value.values()):
        return table(
            "Coding agents",
            ("Agent", "Installed", "Run with protection"),
            [[k, "yes" if v["available"] else "not found", v["wrapper"]] for k, v in value.items()],
        )
    return table(
        "TimeMachine", ("Detail", "Value"), [[k.replace("_", " "), v] for k, v in value.items()]
    )
