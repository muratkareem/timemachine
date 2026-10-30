"""Keyboard-friendly checkpoint timeline, file preview and confirmed recovery."""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label, RichLog

from ..checkpoint import get_checkpoint
from ..diff import compare, text_content
from ..history import history
from ..objects import ObjectStore
from ..operations import redo, redo_plan, restore, restore_plan, undo, undo_plan
from ..project import Project
from ..restore_plan import Plan


def safe_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2)


class ConfirmRestore(ModalScreen[bool]):
    CSS = """
    ConfirmRestore { align: center middle; }
    #dialog { width: 80%; height: 80%; border: thick $warning; padding: 1 2; }
    #dialog RichLog { height: 1fr; }
    #dialog Horizontal { height: 3; }
    """
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, plan: Plan):
        super().__init__()
        self.plan = plan

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Confirm filesystem changes — recovery checkpoint retained")
            yield RichLog(id="plan", markup=False, highlight=False, wrap=True)
            with Horizontal():
                yield Button("Apply changes", id="apply", variant="warning")
                yield Button("Cancel", id="cancel", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#plan", RichLog).write(Text(safe_text(self.plan.data())))
        self.query_one("#cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "apply")

    def action_cancel(self) -> None:
        self.dismiss(False)


class TimeMachineApp(App[None]):
    TITLE = "TimeMachine — local checkpoint history"
    CSS = """
    #summary { height: 2; padding: 0 1; }
    #tables { height: 45%; }
    #timeline { width: 60%; }
    #files { width: 40%; }
    #preview { height: 1fr; border: solid $primary; }
    #activity { height: 1; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f5", "refresh", "Refresh"),
        ("b", "anchor", "Compare from"),
        ("d", "diff", "Diff"),
        ("r", "restore", "Restore"),
        ("u", "undo", "Undo"),
        ("ctrl+r", "redo", "Redo"),
    ]

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.selected_id: str | None = None
        self.anchor: str | None = None
        self.loaded: dict[str, Any] | None = None
        self.pending: Callable[[], dict[str, Any]] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Loading real history…", id="summary")
        with Horizontal(id="tables"):
            yield DataTable(id="timeline", cursor_type="row")
            yield DataTable(id="files", cursor_type="row")
        yield Label("Ready", id="activity")
        yield RichLog(id="preview", markup=False, highlight=False, wrap=True)
        yield Footer()

    async def on_mount(self) -> None:
        timeline = self.query_one("#timeline", DataTable)
        timeline.add_columns("Checkpoint", "UTC", "Kind/status", "Message", "Bytes")
        self.query_one("#files", DataTable).add_columns("Path", "Type", "Mode", "Bytes")
        await self.action_refresh()
        timeline.focus()

    def show_result(self, value: Any) -> None:
        log = self.query_one("#preview", RichLog)
        log.clear()
        log.write(Text(safe_text(value)))

    async def service(self, operation: Callable[[], Any]) -> Any:
        self.query_one("#activity", Label).update("Working — validating local data…")
        try:
            return await asyncio.to_thread(operation)
        finally:
            self.query_one("#activity", Label).update("Ready")

    async def action_refresh(self) -> None:
        try:
            data = await self.service(lambda: history(self.project, 200))
            table = self.query_one("#timeline", DataTable)
            table.clear()
            for item in data["checkpoints"]:
                table.add_row(
                    item["id"][:12],
                    item["created"],
                    f"{item['kind']}/{item['status']}",
                    Text(json.dumps(item["message"])),
                    str(item.get("size", "?")),
                    key=item["id"],
                )
            self.query_one("#summary", Label).update(
                Text(
                    f"{len(data['checkpoints'])} checkpoints | {len(data['runs'])} runs | "
                    f"{len(data['restores'])} restores | arrows/Tab navigate; file preview"
                )
            )
            if not data["checkpoints"]:
                self.show_result("No checkpoints. Create one with timemachine checkpoint or run.")
        except Exception as exc:
            self.show_result({"error": str(exc)})

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        try:
            key = str(event.row_key.value)
            if event.data_table.id == "timeline":
                self.selected_id = key
                self.loaded = await self.service(lambda: get_checkpoint(self.project, key))
                files = self.query_one("#files", DataTable)
                files.clear()
                for path, entry in sorted(self.loaded["entries"].items()):
                    files.add_row(
                        Text(json.dumps(path)),
                        entry.kind,
                        oct(entry.mode),
                        str(entry.size),
                        key=path,
                    )
                self.show_result(
                    {"checkpoint": key, "git": self.loaded["git"], "compare_from": self.anchor}
                )
            elif self.loaded and key in self.loaded["entries"]:
                entry = self.loaded["entries"][key]
                objects = ObjectStore(self.project.store, self.project.config["quota_bytes"])
                content = await self.service(lambda: text_content(objects, entry))
                self.show_result(
                    {
                        "path": key,
                        "content": content,
                        "summary": "Binary/non-UTF-8/large/link/directory"
                        if content is None
                        else "UTF-8 text (escaped safely)",
                    }
                )
        except Exception as exc:
            self.show_result({"error": str(exc)})

    def action_anchor(self) -> None:
        self.anchor = self.selected_id
        self.show_result({"compare_from": self.anchor})

    async def action_diff(self) -> None:
        if not self.anchor or not self.selected_id:
            self.show_result("Select the first checkpoint and press b, then another and press d.")
            return
        try:
            result = await self.service(
                lambda: compare(self.project, self.anchor, self.selected_id)
            )
            self.show_result(result)
        except Exception as exc:
            self.show_result({"error": str(exc)})

    def plan_restore(self, identifier: str) -> Plan:
        with self.project.lock():
            return restore_plan(self.project, identifier)

    async def action_restore(self) -> None:
        if not self.selected_id:
            return
        identifier = self.selected_id
        try:
            plan = await self.service(lambda: self.plan_restore(identifier))

            def apply() -> dict[str, Any]:
                with self.project.lock():
                    return restore(self.project, identifier, plan=plan)

            self.pending = apply
            self.push_screen(ConfirmRestore(plan), self.confirmed)
        except Exception as exc:
            self.show_result({"error": str(exc)})

    async def stack_action(self, redo_action: bool) -> None:
        def prepare() -> tuple[dict[str, Any], Plan]:
            with self.project.lock():
                return redo_plan(self.project) if redo_action else undo_plan(self.project)

        try:
            run_record, plan = await self.service(prepare)

            def apply() -> dict[str, Any]:
                with self.project.lock():
                    # PRE/POST expectations are fixed, even if the UI waits for consent.
                    return (redo if redo_action else undo)(
                        self.project,
                        acknowledge_git=True,
                        confirmed_plan=plan,
                        run_id=run_record["id"],
                    )

            self.pending = apply
            self.push_screen(ConfirmRestore(plan), self.confirmed)
        except Exception as exc:
            self.show_result({"error": str(exc)})

    async def action_undo(self) -> None:
        await self.stack_action(False)

    async def action_redo(self) -> None:
        await self.stack_action(True)

    async def confirmed(self, accepted: bool | None) -> None:
        operation, self.pending = self.pending, None
        if accepted and operation:
            try:
                result = await self.service(operation)
                await self.action_refresh()
                self.show_result(result)
            except Exception as exc:
                self.show_result({"error": str(exc)})
