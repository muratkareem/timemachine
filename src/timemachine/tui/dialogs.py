"""Cancel-first, bounded recovery reviews and a keyboard field guide."""

from rich import box
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, RichLog, Static

from ..presentation import safe, size
from ..restore_plan import Plan
from .design import DARK, LIGHT


class HelpScreen(ModalScreen[None]):
    CSS = """
    HelpScreen { align: center middle; }
    #help { width: 94%; max-width: 92; height: 90%; padding: 0 1;
            border: double $primary; background: $surface; }
    #help RichLog { height: 1fr; }
    #help Button { height: 3; }
    """
    BINDINGS = [("escape", "close", "Close"), ("question_mark", "close", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="help"):
            yield Static("FIELD GUIDE / LOCAL RECOVERY", classes="heading")
            yield RichLog(id="help-text", wrap=True, min_width=20)
            yield Button("Return [Esc]", id="close-help", variant="primary")

    def on_mount(self) -> None:
        self.query_one(RichLog).write(
            Text(
                "01 / SAVE A STATE\n"
                "timemachine init is setup, not a backup. Save a checkpoint or wrap a session.\n"
                "timemachine run -- codex captures PRE and POST. Other agents work too.\n\n"
                "02 / INSPECT\n"
                "1 Archive / 2 Files / 3 Inspector    Tab moves focus\n"
                "Arrows or j/k navigate; Enter/d opens the selected file.\n"
                "/ filters loaded archive entries; Load older fetches the next page.\n"
                "Find searches the bounded visible preview; Enter/n moves through matches.\n"
                "v toggles saved file/diff. b sets a saved comparison origin.\n\n"
                "03 / RECOVER DELIBERATELY\n"
                "u reviews Undo; Ctrl+R reviews Redo; the primary button follows session order.\n"
                "r reviews the selected full checkpoint. s restores only the selected file/path.\n"
                "Every review checks current files, then freezes and revalidates the intent.\n"
                "Cancel is always the default. Newer conflicts refuse writes.\n\n"
                "F5 refresh / t light-dark / Esc archive or cancel / q quit\n"
                "No animation, sound, daemon or automatic restore.\n\n"
                "SCOPE / Selected local bytes, modes, directories and opaque symlinks.\n"
                "Excluded trees and Git history/index are not restored. Ignored files can\n"
                "contain secrets. Stop external writers; recovery is not globally atomic.\n"
                "For interruption/corruption: preserve the store and run timemachine doctor.\n\n"
                "CLI alternative: timemachine --plain history; timemachine undo --preview --json"
            )
        )
        self.query_one("#close-help", Button).focus()

    def action_close(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self) -> None:
        self.action_close()


class ConfirmRestore(ModalScreen[bool]):
    CSS = """
    ConfirmRestore { align: center middle; }
    #dialog { width: 96%; max-width: 108; height: 92%; border: double $warning;
              padding: 0 1; background: $surface; }
    #review-title { height: 1; color: $warning; text-style: bold; }
    #review-context { height: auto; max-height: 2; color: $secondary; }
    #review-summary { height: auto; max-height: 3; color: $foreground; }
    #plan { height: 1fr; }
    #review-safety { height: auto; max-height: 3; color: $ink-muted; }
    #dialog Horizontal { height: 3; }
    #dialog Button { min-width: 10; margin-right: 1; height: 3; }
    """
    BINDINGS = [("escape", "cancel", "Cancel")]
    MAX_REVIEW = 500

    def __init__(self, plan: Plan, operation: str = "restore", context: str = ""):
        super().__init__()
        self.plan, self.operation, self.context = plan, operation, context

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("RECOVERY TERMINAL / REVIEW " + self.operation.upper(), id="review-title")
            yield Static(
                Text(safe(self.context) or "Frozen backend plan / no files changed yet"),
                id="review-context",
            )
            removed = sum(c.target is None for c in self.plan.changes)
            created = sum(c.expected is None for c in self.plan.changes)
            yield Static(
                f"{len(self.plan.changes)} entries / {created} create / {removed} remove / "
                f"{len(self.plan.changes) - created - removed} replace or mode",
                id="review-summary",
            )
            yield RichLog(id="plan", markup=False, wrap=True, min_width=20, max_lines=4000)
            yield Static(
                "Recovery checkpoint + journal before writes; revalidate after consent.\n"
                "Git history/index intact. Stop writers; multi-file recovery is not atomic.",
                id="review-safety",
            )
            with Horizontal():
                yield Button("Cancel [Esc]", id="cancel", variant="primary")
                yield Button("Apply changes", id="apply", variant="warning")

    def on_mount(self) -> None:
        colors = DARK if self.app.current_theme.dark else LIGHT
        table = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
        table.add_column("WRITE", width=8)
        table.add_column("EXACT PATH", ratio=2)
        table.add_column("BEFORE -> AFTER", ratio=1)
        for change in self.plan.changes[: self.MAX_REVIEW]:
            old, new = change.expected, change.target
            kind = "REMOVE" if new is None else "CREATE" if old is None else "REPLACE"
            role = "deleted" if new is None else "added" if old is None else "modified"
            description = " -> ".join(
                f"{e.kind} {oct(e.mode)} {size(e.size)}" if e else "absent" for e in (old, new)
            )
            table.add_row(
                Text(kind, style=colors[role]), Text(safe(change.path)), Text(description)
            )
        log = self.query_one("#plan", RichLog)
        log.write(table)
        for warning in self.plan.warnings:
            log.write(Text("GIT / " + safe(warning), style=colors["warning"]))
        apply = self.query_one("#apply", Button)
        if len(self.plan.changes) > self.MAX_REVIEW:
            apply.disabled = True
            log.write(
                Text(
                    "Review exceeds 500 entries. Application disabled in this view.\n"
                    "Use the CLI --preview to review the complete plan before applying.",
                    style=colors["warning"],
                )
            )
        elif not self.plan.changes and self.operation in ("undo", "redo"):
            apply.label = "Confirm history step"
            log.write(
                Text("No file changes. Confirmation advances only this session's history state.")
            )
        else:
            apply.disabled = not self.plan.changes
        self.query_one("#cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "apply" and not event.button.disabled)

    def action_cancel(self) -> None:
        self.dismiss(False)
