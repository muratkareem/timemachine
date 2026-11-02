"""A real local-recovery workspace. Mutations always use the core safety engine."""

import asyncio
import difflib
import os
from collections.abc import Callable
from functools import partial
from pathlib import PurePosixPath
from typing import Any

from rich.syntax import Syntax
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, RichLog, Select, Static
from textual.worker import Worker

from ..diff import text_content
from ..git_context import git_context
from ..objects import ObjectStore
from ..operations import redo, redo_plan, restore, restore_plan, undo, undo_plan
from ..presentation import guidance, human, safe, short, size
from ..project import Project
from ..restore_plan import Plan
from ..ui_data import Workspace
from .components import SaveSlot, archive_record
from .design import DARK, LIGHT, SaveStateSyntax, console_theme
from .dialogs import ConfirmRestore, HelpScreen


class TimeMachineApp(App[None]):
    TITLE = "TimeMachine"
    CSS_PATH = "theme.tcss"
    BINDINGS = [
        Binding("u", "undo", "Undo preview"),
        Binding("a", "mode", "Simple / Advanced", show=False),
        Binding("r", "restore", "Restore"),
        Binding("s", "restore_file", "Restore file", show=False),
        Binding("f", "file_search", "Filter paths", show=False),
        Binding("d", "diff", "Diff"),
        Binding("slash", "search", "Search"),
        Binding("question_mark", "help", "Help"),
        Binding("escape", "history", "Back"),
        Binding("q", "quit", "Quit"),
        Binding("f5", "refresh", "Refresh", show=False),
        Binding("j", "next_row", "Next", show=False),
        Binding("k", "previous_row", "Previous", show=False),
        Binding("enter", "diff", "Open", show=False),
        Binding("b", "anchor", "Compare", show=False),
        Binding("v", "toggle_file", "File/diff", show=False),
        Binding("n", "find_next", "Next match", show=False),
        Binding("ctrl+r", "redo", "Redo", show=False),
        Binding("t", "theme", "Theme", show=False),
        Binding("1", "history", "Archive", show=False),
        Binding("2", "files", "Files", show=False),
        Binding("3", "inspect", "Inspector", show=False),
    ]

    def __init__(self, project: Project, *, advanced: bool = False):
        super().__init__()
        self.advanced = advanced
        self.project = project
        self.workspace = Workspace(project)
        self.selected_id: str | None = None
        self.anchor: str | None = None
        self.selected_event: dict[str, Any] | None = None
        self.selection: dict[str, Any] | None = None
        self.events: list[dict[str, Any]] = []
        self.visible_events: dict[str, dict[str, Any]] = {}
        self.file_items: dict[str, dict[str, Any]] = {}
        self.pending: Callable[[], dict[str, Any]] | None = None
        self.preview_epoch = 0
        self.preview_text = ""
        self.preview_lexer = "text"
        self.preview_path: str | None = None
        self.preview_item: dict[str, Any] | None = None
        self.file_mode = False
        self.match_index = -1
        self.catalog: dict[str, Any] = {}
        self.primary_operation: str | None = None
        self.has_more = False
        self.file_offset = 0
        self.file_page_size = 200
        self.page_size = 50
        self.service_lock = asyncio.Lock()
        self.selection_worker: Worker[None] | None = None
        self.preview_worker: Worker[None] | None = None
        self.register_theme(console_theme())
        self.register_theme(console_theme(light=True))
        self.theme = "timemachine"
        self.animation_level = "none"
        self.ascii = os.environ.get("TIMEMACHINE_ASCII") == "1" or os.environ.get("TERM") == "dumb"

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if isinstance(self.screen, ModalScreen) and action in {
            "undo",
            "redo",
            "restore",
            "refresh",
            "theme",
            "anchor",
            "diff",
            "toggle_file",
            "search",
            "history",
            "help",
            "files",
            "inspect",
            "restore_file",
            "file_search",
            "mode",
        }:
            return False
        return True

    def compose(self) -> ComposeResult:
        with Horizontal(id="brandbar"):
            yield Static(
                Text("[]==[]\n  ><  \n[]==[]" if self.ascii else "██▀▀██\n ▀██▀ \n██▄▄██"),
                id="pixel-mark",
            )
            yield Static(
                Text("TIME / MACHINE\nSAVE-STATE CONSOLE  /  " + safe(self.project.root.name)),
                id="brand",
            )
            yield Static("LOCAL ONLY\nNO DAEMON  /  ? GUIDE", id="tagline")
        with Grid(id="dashboard"):
            for name in ("protection", "session", "changes", "storage"):
                yield SaveSlot("Reading archive…", id=f"card-{name}", classes="card")
        yield Static("Reading archive…", id="overview")
        with Horizontal(id="actions"):
            yield Button("Review undo [u]", id="undo-button", variant="primary")
            yield Button("Restore [r]", id="restore-button")
            yield Button("Refresh [F5]", id="refresh-button")
            yield Button("Help (?)", id="help-button")
            yield Button("Advanced [a]", id="mode-button")
        yield Static("Reading session order…", id="action-context")
        yield Static(
            "Saved snapshots are not a live backup. Review checks current files.", id="notice"
        )
        with Horizontal(id="pane-tabs"):
            yield Button("1 Archive", id="tab-archive", classes="active")
            yield Button("2 Files", id="tab-files")
            yield Button("3 Inspector", id="tab-inspect")
        with Grid(id="workarea"):
            with Vertical(id="history-pane"):
                with Horizontal(id="filterbar"):
                    yield Input(placeholder="Search archive /", id="filter")
                    yield Select(
                        [
                            ("All", "all"),
                            ("Sessions", "run"),
                            ("Saves", "checkpoint"),
                            ("Recovery", "restore"),
                        ],
                        value="all",
                        allow_blank=False,
                        id="kind",
                    )
                yield DataTable(
                    id="timeline",
                    cursor_type="row",
                    zebra_stripes=True,
                    show_row_labels=False,
                    cell_padding=1,
                )
                yield Button("Load older entries", id="more")
            with Vertical(id="files-pane"):
                yield Static("Select an archive entry", id="selection")
                yield Input(placeholder="Filter file / directory paths [f]", id="path-filter")
                yield DataTable(
                    id="files",
                    cursor_type="row",
                    zebra_stripes=True,
                    show_row_labels=False,
                    cell_padding=1,
                )
                with Horizontal(id="file-page"):
                    yield Button("Previous files", id="previous-files")
                    yield Button("Next files", id="next-files")
            with Horizontal(id="preview-pane"):
                with Vertical(id="diff-column"):
                    yield Static("Select a saved file", id="preview-title")
                    yield Input(placeholder="Find text / Enter: next match", id="find")
                    yield RichLog(
                        id="preview",
                        markup=False,
                        highlight=False,
                        wrap=False,
                        auto_scroll=False,
                        min_width=20,
                        max_lines=2100,
                    )
                with Vertical(id="ledger"):
                    yield Static("SAVE-STATE LEDGER", classes="heading")
                    yield Static("Select a session or checkpoint.", id="ledger-content")
                    yield Static(
                        "SCOPE / LOCAL FILES\nGit history and index stay intact.\n"
                        "Stop external writers before recovery.",
                        id="scope-note",
                    )
        yield Static("Ready · navigation reads saved snapshots", id="activity")
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#history-pane").border_title = "1 / SESSION ARCHIVE"
        self.query_one("#files-pane").border_title = "2 / FILE INVENTORY"
        self.query_one("#preview-pane").border_title = "3 / CHANGE INSPECTOR"
        self.query_one(
            "#restore-button", Button
        ).tooltip = (
            "Review full selected save. May remove newer paths. s reviews only the selected file."
        )
        self.query_one(
            "#undo-button", Button
        ).tooltip = (
            "Session-order candidate only. Live files are checked before the confirmation dialog."
        )
        self.query_one(
            "#files", DataTable
        ).tooltip = "Enter opens file / s reviews recovery for this path / v toggles saved bytes"
        self.query_one("#timeline", DataTable).add_column("UTC / STATE", width=18, key="event")
        self.query_one("#timeline", DataTable).add_column(
            "SESSION / SAVE POINT", key="description", width=30
        )
        files = self.query_one("#files", DataTable)
        files.add_column("STATE", key="state", width=8)
        files.add_column("FILE / RELATIVE PATH", key="path", width=24)
        files.add_column("SIZE", key="bytes", width=7)
        self.set_class(self.ascii, "ascii")
        self.layout_width(self.size.width)
        self.present_mode()
        await self.action_refresh()
        self.action_history() if self.advanced else self.action_files()
        if not self.events and not self.advanced:
            await self.action_inspect()
        self.call_after_refresh(self.fit_tables)

    def present_mode(self) -> None:
        self.set_class(not self.advanced, "simple")
        self.query_one("#mode-button", Button).label = (
            "Simple (a)" if self.advanced else "Advanced (a)"
        )
        for name, title in (
            ("history", "History"),
            ("files", "Changed Files"),
            ("preview", "What Changed"),
        ):
            self.query_one("#" + name + "-pane").border_title = title
        for name, title in (("archive", "1 History"), ("files", "2 Files"), ("inspect", "3 Diff")):
            self.query_one("#tab-" + name, Button).label = title
        self.query_one("#filter", Input).placeholder = "Search history /"

    async def action_mode(self) -> None:
        if isinstance(self.screen, ModalScreen):
            return
        self.advanced = not self.advanced
        self.present_mode()
        self.render_timeline(repaint=True)
        if self.catalog:
            self.render_dashboard(self.catalog)
        if self.selection:
            self.render_files(repaint=True)
        if self.preview_path:
            await self.preview_file(self.preview_path)
        self.recovery_controls()
        self.action_history() if self.advanced else self.action_files()

    def fit_tables(self) -> None:
        for name, column, reserved in (("timeline", "description", 24), ("files", "path", 23)):
            table = self.query_one("#" + name, DataTable)
            if not table.columns or not table.display:
                continue
            key = next(k for k in table.columns if k.value == column)
            width = max(8, table.size.width - reserved)
            if table.columns[key].width == width:
                continue
            table.columns[key].width = width
            if table.row_count:
                row = next(iter(table.rows))
                # Public update API invalidates cached line widths and virtual size.
                table.update_cell(row, key, table.get_cell(row, key), update_width=True)
            table.refresh(layout=True)

    def layout_width(self, width: int) -> None:
        self.set_class(width < 120, "compact")
        self.set_class(width < 90, "narrow")
        self.set_class(self.size.height <= 30, "short")
        self.set_class(width >= 150, "wide")

    def on_resize(self, event: events.Resize) -> None:
        self.layout_width(event.size.width)
        if self.query("#timeline"):
            self.call_after_refresh(self.fit_tables)
            if self.catalog:
                self.render_brand()

    def notify_state(self, message: str, state: str = "") -> None:
        widget = self.query_one("#notice", Static)
        widget.set_classes(state)
        widget.update(Text(safe(message)))

    def show_result(self, value: Any) -> None:
        self.preview_epoch += 1
        self.preview_path = None
        self.preview_item = None
        self.preview_text = ""
        log = self.query_one("#preview", RichLog)
        log.clear()
        log.wrap = True
        log.write(human(value))

    def failure(self, exc: Exception) -> None:
        self.catalog = {}
        self.primary_operation = None
        self.query_one("#undo-button", Button).disabled = True
        self.query_one("#restore-button", Button).disabled = True
        self.query_one("#action-context", Static).update(
            "Review unavailable / resolve the error, then F5 refresh"
        )
        self.notify_state(f"Cannot proceed: {safe(exc)}  {guidance(str(exc))}", "error")
        self.query_one("#preview-title", Static).update("Recovery needs attention")
        if not self.advanced:
            self.remove_class("pane-files", "pane-history")
            self.add_class("detail-mode")
            self.update_tabs("inspect")
        self.show_result(Text("No success is claimed.\n" + safe(exc) + "\n\n" + guidance(str(exc))))

    async def service(self, operation: Callable[[], Any]) -> Any:
        async with self.service_lock:
            self.query_one("#activity", Static).update(
                "Working · reading or validating local data…"
            )
            try:
                return await asyncio.to_thread(operation)
            finally:
                self.query_one("#activity", Static).update("Ready · F5 refreshes saved state")

    def dashboard(self) -> dict[str, Any]:
        data = self.workspace.dashboard()
        data["bytes"] = sum(p.lstat().st_size for p in (self.project.store / "objects").iterdir())
        data["git"] = git_context(self.project.root)
        run = data["run"]
        data["git_warning"] = False
        if run and run["post"]:
            pre = self.workspace.checkpoint(run["pre"])
            post = self.workspace.checkpoint(run["post"])
            data["git_warning"] = pre["git"] != post["git"] or post["git"] != data["git"]
        return data

    def recovery_controls(self) -> None:
        """Candidates come from the engine's catalog query; review still checks live files."""
        choices: list[tuple[str, dict[str, Any]]] = []
        for kind in ("undo", "redo"):
            candidate = self.catalog.get(kind)
            if isinstance(candidate, dict):
                choices.append((kind, candidate))
        selected = self.selected_event
        if selected and selected["category"] == "run":
            choices = [(kind, run) for kind, run in choices if run["id"] == selected["id"]]
        # A later undone session takes priority over an older applied session.
        choices.sort(key=lambda item: item[1]["sequence"], reverse=True)
        button = self.query_one("#undo-button", Button)
        restore_button = self.query_one("#restore-button", Button)
        restore_button.disabled = not self.selected_id or bool(self.catalog.get("blocked"))
        if choices:
            kind, run = choices[0]
            self.primary_operation = kind
            button.label = "Review redo [^R]" if kind == "redo" else "Review undo [u]"
            button.disabled = False
            context = f"NEXT / {kind.upper()} #{short(run['id'])} / live check required"
            if not self.advanced:
                button.label = "Redo Changes (^R)" if kind == "redo" else "Undo AI Changes (u)"
                context = "Review first. Apply only after you confirm."
        else:
            self.primary_operation = None
            button.label = "No session action"
            button.disabled = True
            context = self.catalog.get("blocked") or (
                "Session order differs: select the next applied/undone session or refresh."
                if selected and selected["category"] == "run"
                else "No session to undo or redo. Save a checkpoint or run -- COMMAND."
            )
        self.query_one("#action-context", Static).update(Text(context))

    async def action_refresh(self) -> None:
        try:

            def refresh_page() -> list[dict[str, Any]]:
                self.workspace.reset()
                return self.workspace.timeline(self.page_size + 1)

            page = await self.service(refresh_page)
            self.has_more = len(page) > self.page_size
            self.events = page[: self.page_size]
            self.render_timeline()
            data = await self.service(self.dashboard)
            self.catalog = data
            self.recovery_controls()
            self.render_dashboard(data)
        except Exception as exc:
            self.failure(exc)

    def render_brand(self) -> None:
        self.query_one("#brand", Static).update(
            Text(
                (
                    "TIME / MACHINE / "
                    if self.has_class("narrow") and self.has_class("short")
                    else "TIME / MACHINE\nProject: "
                )
                + safe(self.project.root.name)
            )
        )

    def render_dashboard(self, data: dict[str, Any]) -> None:
        cp, run = data["checkpoint"], data["run"]
        needs_attention = bool(data["blocked"])
        if needs_attention:
            state = "Recovery needs attention"
        elif cp and cp["status"] != "COMPLETE":
            state = "Latest checkpoint incomplete"
        elif cp:
            state = "Checkpoint available"
        else:
            state = "Ready to checkpoint"
        self.notify_state(
            "Current files are checked when you review recovery."
            if not self.advanced
            else "Saved snapshots only / live files checked at review."
        )
        self.render_brand()
        self.query_one("#card-protection", SaveSlot).show(
            "SYSTEM STATUS",
            state,
            "Live files not scanned",
            self.palette,
            "warning" if needs_attention else "protected",
        )
        self.query_one("#card-session", SaveSlot).show(
            "LATEST SESSION",
            (run["agent"] + " / " + run["state"].upper()) if run else "NO SESSIONS",
            f"{run['status']} / exit {run['exit_code']}" if run else "run -- COMMAND to begin",
            self.palette,
            "primary",
        )
        percent = min(100.0, data["bytes"] / self.project.config["quota_bytes"] * 100)
        filled = min(8, int(percent / 12.5))
        meter = "[" + "#" * filled + "." * (8 - filled) + f"] {percent:.1f}% quota"
        self.query_one("#card-storage", SaveSlot).show(
            "OBJECT STORAGE",
            size(data["bytes"]) + " / " + size(self.project.config["quota_bytes"]),
            meter,
            self.palette,
            "text",
        )
        self.query_one("#card-changes", Static).update(
            "SELECTED CHANGES\nSelect a session\nUndo preview checks conflicts"
        )
        self.query_one("#overview", Static).update(
            Text(state + " · " + size(data["bytes"]) + " saved")
        )
        if not self.advanced:
            status = "Ready, but no files saved yet. Help [?] explains your first session."
            if cp:
                status = "Saved files available. Current files have not been checked."
            if cp and cp["status"] != "COMPLETE":
                status = "Latest save incomplete. Run timemachine doctor for guidance."
            if run:
                status = (
                    "Last session reverted. Review Redo to bring its changes back."
                    if run["state"] == "undone"
                    else "Last session captured. Review its changes below."
                )
                if run["status"] not in ("COMPLETE", "LATE_POST"):
                    status = "Session incomplete. Run timemachine doctor before recovery."
                elif run["exit_code"]:
                    status = "Command failed; captured changes can still be reviewed."
            self.query_one("#overview", Static).update(Text(status))
        if data["git_warning"]:
            self.notify_state(
                "Git context differs. File recovery never reverses commits or index.", "error"
            )
        if needs_attention:
            self.notify_state(
                "Session/recovery unfinished. Run timemachine doctor for next steps.",
                "error",
            )
        if not self.events:
            self.query_one("#preview-title", Static).update("Start with one protected session")
            self.show_result(
                "No snapshots yet.\n\nIn your terminal:\n"
                "  timemachine run -- YOUR_COMMAND\n"
                "Any executable works; no particular AI agent is required.\n\n"
                "Or save a manual checkpoint:\n"
                "  timemachine checkpoint -m 'Before my changes'\n\n"
                "Initialization alone does not back up your project."
            )

    def render_timeline(self, *, repaint: bool = False) -> None:
        self.set_class(not self.events, "empty-project")
        table = self.query_one("#timeline", DataTable)
        if repaint:
            for key, item in self.visible_events.items():
                stamp, body = archive_record(item, self.palette, simple=not self.advanced)
                table.update_cell(key, "event", stamp)
                table.update_cell(key, "description", body)
            return
        previous = self.selected_event["id"] if self.selected_event else None
        table.clear()
        self.visible_events.clear()
        query = self.query_one("#filter", Input).value.casefold()
        kind = self.query_one("#kind", Select).value
        selected_row = 0
        for item in self.events:
            if kind != "all" and item["category"] != kind:
                continue
            if query and query not in " ".join(str(v) for v in item.values()).casefold():
                continue
            key = item["category"] + ":" + item["id"]
            self.visible_events[key] = item
            if item["id"] == previous:
                selected_row = table.row_count
            stamp, body = archive_record(item, self.palette, simple=not self.advanced)
            table.add_row(stamp, body, key=key, height=2)
        more_button = self.query_one("#more", Button)
        more_button.disabled = not self.has_more
        more_button.label = (
            "Load older / next 50"
            if self.has_more
            else f"Archive loaded / {len(self.events)} entries"
        )
        if table.row_count:
            table.move_cursor(row=selected_row)
        else:
            self.selected_id = None
            self.selected_event = None
            self.recovery_controls()
            self.file_items.clear()
            self.selection = None
            self.query_one("#files", DataTable).clear()
            self.query_one("#preview-title", Static).update("No matching selection")
            self.show_result(
                "No matching history. Clear the filter or load older entries."
                if self.events
                else "No files saved yet. Initialization is setup, not a backup.\n\n"
                "In your project terminal:\n  timemachine run -- YOUR_COMMAND\n\n"
                "Replace YOUR_COMMAND with any executable and arguments.\n"
                "Or save manually:\n  timemachine checkpoint -m 'Before my changes'\n\n"
                "Help (?) has a runnable Python example."
            )
            if not self.events:
                self.query_one("#preview-title", Static).update("Your first saved session")

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        key = str(event.row_key.value)
        if event.data_table.id == "timeline" and key in self.visible_events:
            item = self.visible_events[key]
            if item is self.selected_event and (
                self.selection is not None
                or self.selection_worker is not None
                and not self.selection_worker.is_finished
            ):
                return
            self.selected_event = item
            self.selected_id = None
            self.selection = None
            self.file_items.clear()
            self.query_one("#files", DataTable).clear()
            self.recovery_controls()
            self.query_one("#preview-title", Static).update("Reading saved selection…")
            self.selection_worker = self.run_worker(
                partial(self.read_selection, item, self.anchor), group="selection", exclusive=True
            )
        elif event.data_table.id == "files" and key in self.file_items:
            if self.preview_path == key and self.preview_item is self.file_items[key]:
                return
            self.preview_worker = self.run_worker(
                partial(self.read_preview, key), group="preview", exclusive=True
            )

    async def read_selection(self, item: dict[str, Any], anchor: str | None) -> None:
        try:
            selected = await self.service(lambda: self.workspace.selection(item, anchor))
            if self.selected_event is not item:
                return
            self.selection = selected
            self.file_offset = 0
            self.selected_id = selected["target"]
            self.file_items = {f["path"]: f for f in selected["files"]}
            self.recovery_controls()
            self.render_files()
        except Exception as exc:
            if self.selected_event is item:
                self.failure(exc)

    def render_files(self, *, repaint: bool = False) -> None:
        selected = self.selection
        if selected is None:
            return
        files = self.query_one("#files", DataTable)
        selected_path = (
            str(files.coordinate_to_cell_key(files.cursor_coordinate).row_key.value)
            if files.row_count
            else None
        )
        if not repaint:
            self.preview_epoch += 1
            files.clear()
        counts = {
            kind: sum(
                f["change"] == kind and (f["after"] or f["before"]).kind != "directory"
                for f in selected["files"]
            )
            for kind in ("added", "modified", "deleted", "metadata", "type")
        }
        self.query_one("#card-changes", Static).update(
            Text(
                f"CHANGES\n+{counts['added']} added ~{counts['modified']} edited\n"
                f"-{counts['deleted']} deleted "
                f"{counts['metadata'] + counts['type']} mode/type"
            )
        )
        self.query_one("#selection", Static).update(
            Text(
                (
                    f"Recovery safeguard BEFORE {self.selected_event['kind']}"
                    if self.selected_event and self.selected_event["category"] == "restore"
                    else f"{len(selected['files'])} entries / {short(selected['target'])}"
                )
                + "\n"
                + (
                    "Compared with " + short(selected["base"])
                    if selected["base"]
                    else "Saved baseline"
                )
            )
        )
        if not self.advanced:
            self.query_one("#selection", Static).update(
                f"{len(selected['files'])} paths / +{counts['added']} added / "
                f"{counts['modified']} edited / {counts['deleted']} deleted"
            )
        self.update_ledger()
        labels = {
            "added": "+ ADD",
            "modified": "~ EDIT",
            "deleted": "- DEL",
            "type": "! TYPE",
            "metadata": "= MODE",
            "saved": "S SAVE",
        }
        path_query = self.query_one("#path-filter", Input).value.casefold()
        matches = [p for p in self.file_items if not path_query or path_query in p.casefold()]
        visible_paths = matches[self.file_offset : self.file_offset + self.file_page_size]
        self.query_one("#file-page").display = len(matches) > self.file_page_size
        self.query_one("#previous-files", Button).disabled = self.file_offset == 0
        self.query_one("#next-files", Button).disabled = (
            self.file_offset + self.file_page_size >= len(matches)
        )
        if len(matches) > self.file_page_size:
            self.query_one("#selection", Static).update(
                f"Showing {self.file_offset + 1}-{self.file_offset + len(visible_paths)}"
                f" / {len(matches)} matches\n"
                "Filter paths to locate any file"
            )
        for path in visible_paths:
            change = self.file_items[path]
            label = change["change"]
            name = PurePosixPath(path)
            parent = str(name.parent)
            entry = change["after"] or change["before"]
            state = Text(labels[label], style=self.palette.get(label, ""))
            file = Text(
                safe(name.name) + ("\n" + safe(parent) if parent != "." else ""),
                overflow="ellipsis",
                no_wrap=True,
            )
            byte_text = Text(
                "dir" if entry.kind == "directory" else size(entry.size),
                style=self.palette["muted"],
            )
            if repaint:
                for column, value in (("state", state), ("path", file), ("bytes", byte_text)):
                    files.update_cell(path, column, value)
            else:
                files.add_row(state, file, byte_text, key=path, height=2 if parent != "." else 1)
        if not repaint and selected_path in visible_paths:
            files.move_cursor(row=visible_paths.index(selected_path))
        self.call_after_refresh(self.fit_tables)
        if not visible_paths:
            message = (
                "No matching paths. Clear the path filter."
                if self.file_items
                else "No filesystem differences in this selection."
            )
            self.query_one("#preview-title", Static).update(message)
            self.show_result(message)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "timeline":
            await self.action_diff()
        elif event.data_table.id == "files":
            await self.action_inspect()

    def update_ledger(self, path: str | None = None) -> None:
        if not self.selection:
            return
        text = Text("ORIGIN  ", style=self.palette["muted"])
        text.append(short(self.selection["base"]) if self.selection["base"] else "baseline")
        text.append("\nSAVE    " + short(self.selection["target"]))
        event = self.selected_event
        if event:
            text.append("\nSTATE   " + safe(event["status"]), style=self.palette["protected"])
            if event["category"] == "run":
                text.append(" / " + event["state"].upper())
                text.append("\nPRE     " + short(event["pre"]))
                text.append(
                    "\nPOST    " + (short(event["post"]) if event["post"] else "not captured")
                )
        if path and path in self.file_items:
            item = self.file_items[path]
            text.append("\n\n" + safe(path), style="bold " + self.palette["text"])
            for label, key in (("BEFORE", "before"), ("AFTER", "after")):
                entry = item[key]
                text.append("\n" + label + " / ", style=self.palette["muted"])
                text.append(
                    f"{entry.kind} {oct(entry.mode)}\n{size(entry.size)}" if entry else "absent"
                )
            text.append("\n\ns / restore selected path\nv / saved file or unified diff")
        self.query_one("#ledger-content", Static).update(text)

    async def read_preview(self, path: str) -> None:
        item = self.file_items.get(path)
        try:
            await self.preview_file(path)
        except Exception as exc:
            if self.file_items.get(path) is item:
                self.failure(exc)

    async def preview_file(self, path: str) -> None:
        epoch = self.preview_epoch
        change = self.file_items[path]
        self.update_ledger(path)

        def read() -> str:
            objects = ObjectStore(self.project.store, self.project.config["quota_bytes"])
            before, after = (
                text_content(objects, change["before"]),
                text_content(objects, change["after"]),
            )
            entry = change["after"] or change["before"]
            if before is None or after is None:
                return (
                    f"{change['change'].upper()} · {entry.kind} · {size(entry.size)}\n"
                    "Binary, non-UTF-8, link, directory or file over 1 MiB.\n"
                    + (
                        f"Mode: {oct(entry.mode)} · SHA-256: "
                        f"{entry.digest or 'not a regular file'}\n"
                        if self.advanced
                        else "Switch to Advanced for file details.\n"
                    )
                    + f"Link target: {safe(entry.target) if entry.target else '—'}"
                )
            if self.file_mode or not self.selection or not self.selection["base"]:
                return after if change["after"] else before
            return (
                "".join(
                    difflib.unified_diff(
                        before.splitlines(True),
                        after.splitlines(True),
                        fromfile="before / " + safe(path),
                        tofile="after / " + safe(path),
                    )
                )
                or "Content unchanged; inspect mode/type metadata."
            )

        text = await self.service(read)
        if (
            epoch != self.preview_epoch
            or path not in self.file_items
            or self.file_items[path] is not change
        ):
            return
        lines = text.splitlines()
        display_lines = [safe(line) for line in lines[:2000]]
        clipped = len(lines) > 2000 or any(len(line) > 500 for line in display_lines)
        self.preview_text = "\n".join(line[:500] for line in display_lines)
        if clipped:
            self.preview_text += (
                "\n[Truncated: 2,000 lines / 500 chars per line. Saved bytes intact.]"
            )
        self.match_index = -1
        before_entry, after_entry = change["before"], change["after"]
        metadata = (
            f"Mode {oct(before_entry.mode) if before_entry else 'absent'} → "
            f"{oct(after_entry.mode) if after_entry else 'absent'} · "
            f"{size(before_entry.size) if before_entry else '0 B'} → "
            f"{size(after_entry.size) if after_entry else '0 B'}"
        )
        self.query_one("#preview-title", Static).update(
            Text(
                safe(path)
                + "\n"
                + change["change"].upper()
                + " · "
                + (
                    "Saved file"
                    if self.file_mode
                    else "Unified diff / metadata"
                    if self.advanced
                    else "Changes"
                )
                + " · v toggle\n"
                + (metadata if self.advanced else "Review before applying recovery.")
            )
        )
        self.preview_path, self.preview_item = path, change
        self.preview_lexer = (
            Syntax.guess_lexer(path, code=self.preview_text)
            if (self.file_mode or not self.selection or not self.selection["base"])
            else "diff"
        )
        self.draw_preview()
        self.query_one("#preview", RichLog).scroll_home(animate=False)

    def draw_preview(self) -> None:
        log = self.query_one("#preview", RichLog)
        log.wrap = False
        log.clear()
        log.write(
            Syntax(
                self.preview_text or "Empty file",
                self.preview_lexer,
                line_numbers=True,
                word_wrap=False,
                theme=SaveStateSyntax(self.palette),
            )
        )

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter":
            self.render_timeline()
        elif event.input.id == "path-filter":
            self.file_offset = 0
            self.render_files()
        elif event.input.id == "find":
            self.match_index = -1
            self.action_find_next()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "kind":
            self.render_timeline()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "find":
            self.action_find_next()
        elif event.input.id == "path-filter":
            self.action_files()
        else:
            self.query_one("#timeline", DataTable).focus()

    def action_find_next(self) -> None:
        query = self.query_one("#find", Input).value.casefold()
        matches = [
            i
            for i, line in enumerate(self.preview_text.splitlines())
            if query and query in line.casefold()
        ]
        if matches:
            self.match_index = (self.match_index + 1) % len(matches)
            self.query_one("#preview", RichLog).scroll_to(
                y=max(0, matches[self.match_index] - 2), animate=False
            )
            self.query_one("#activity", Static).update(
                f"Match {self.match_index + 1} of {len(matches)}"
            )
        elif query:
            self.query_one("#activity", Static).update("No matches in this preview")

    def action_file_search(self) -> None:
        self.action_files()
        self.query_one("#path-filter", Input).focus()

    def action_search(self) -> None:
        self.action_history()
        self.query_one("#filter", Input).focus()

    def action_next_row(self) -> None:
        if isinstance(self.focused, DataTable):
            self.focused.action_cursor_down()

    def action_previous_row(self) -> None:
        if isinstance(self.focused, DataTable):
            self.focused.action_cursor_up()

    async def action_diff(self) -> None:
        self.remove_class("pane-files", "pane-history")
        self.add_class("detail-mode")
        self.update_tabs("inspect")
        self.query_one("#files", DataTable).focus()
        table = self.query_one("#files", DataTable)
        if table.row_count:
            await self.preview_file(
                str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            )

    async def action_toggle_file(self) -> None:
        self.file_mode = not self.file_mode
        await self.action_diff()

    async def action_anchor(self) -> None:
        self.anchor = self.selected_id
        self.notify_state(
            "Comparison origin: " + short(self.anchor or "none") + ". Select another history entry."
        )

    def update_tabs(self, active: str) -> None:
        for name in ("archive", "files", "inspect"):
            self.query_one("#tab-" + name, Button).set_class(name == active, "active")

    def action_files(self) -> None:
        self.remove_class("detail-mode", "pane-history")
        self.add_class("pane-files")
        self.update_tabs("files")
        self.query_one("#files", DataTable).focus()
        self.call_after_refresh(self.fit_tables)

    async def action_inspect(self) -> None:
        await self.action_diff()
        self.query_one("#preview", RichLog).focus()

    def action_history(self) -> None:
        self.remove_class("detail-mode", "pane-files")
        self.add_class("pane-history")
        self.update_tabs("archive")
        self.query_one("#timeline", DataTable).focus()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    @property
    def palette(self) -> dict[str, str]:
        return LIGHT if self.theme == "timemachine-light" else DARK

    async def action_theme(self) -> None:
        self.theme = "timemachine-light" if self.theme == "timemachine" else "timemachine"
        if self.catalog:
            self.render_dashboard(self.catalog)
        self.render_timeline(repaint=True)
        if self.selection:
            self.render_files(repaint=True)
            if self.preview_path:
                self.update_ledger(self.preview_path)
                self.draw_preview()
        self.recovery_controls()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(self.screen, ModalScreen):
            return
        if event.button.id == "mode-button":
            await self.action_mode()
        elif event.button.id == "tab-archive":
            self.action_history()
        elif event.button.id == "tab-files":
            self.action_files()
        elif event.button.id == "tab-inspect":
            await self.action_inspect()
        elif event.button.id == "undo-button":
            if self.primary_operation == "redo":
                await self.action_redo()
            elif self.primary_operation == "undo":
                await self.action_undo()
        elif event.button.id == "restore-button":
            await self.action_restore()
        elif event.button.id == "refresh-button":
            await self.action_refresh()
        elif event.button.id == "help-button":
            self.action_help()
        elif event.button.id in ("previous-files", "next-files"):
            self.file_offset += self.file_page_size * (1 if event.button.id == "next-files" else -1)
            self.render_files()
        elif event.button.id == "more":
            await self.load_older()

    async def load_older(self) -> None:
        if not self.events or not self.has_more:
            return
        last = self.events[-1]
        before = last["created"], last["category"], last["id"]
        more = await self.service(
            lambda: self.workspace.timeline(self.page_size + 1, before=before)
        )
        self.has_more = len(more) > self.page_size
        self.events.extend(more[: self.page_size])
        self.render_timeline()

    def plan_restore(self, identifier: str, selector: str | None = None) -> Plan:
        with self.project.lock():
            return restore_plan(self.project, identifier, selector)

    async def action_restore_file(self) -> None:
        files = self.query_one("#files", DataTable)
        if not files.row_count:
            self.notify_state("Select a saved file/path first.")
            return
        path = str(files.coordinate_to_cell_key(files.cursor_coordinate).row_key.value)
        await self.review_restore(path)

    async def action_restore(self) -> None:
        await self.review_restore()

    async def review_restore(self, selector: str | None = None) -> None:
        if isinstance(self.screen, ModalScreen):
            return
        if not self.selected_id:
            self.notify_state("Select a saved checkpoint or session first.")
            return
        identifier = self.selected_id
        try:
            plan = await self.service(lambda: self.plan_restore(identifier, selector))

            def apply() -> dict[str, Any]:
                with self.project.lock():
                    return restore(self.project, identifier, selector, plan=plan)

            self.pending = apply
            self.push_screen(
                ConfirmRestore(
                    plan,
                    "restore",
                    (
                        "SAVE "
                        + short(identifier)
                        + " / "
                        + (safe(selector) if selector else "FULL CHECKPOINT")
                    )
                    if self.advanced
                    else (
                        "Restore " + safe(selector)
                        if selector
                        else "Restore all files from this save."
                    ),
                ),
                self.confirmed,
            )
        except Exception as exc:
            self.failure(exc)

    async def stack_action(self, redo_action: bool) -> None:
        if isinstance(self.screen, ModalScreen):
            return

        def prepare() -> tuple[dict[str, Any], Plan]:
            with self.project.lock():
                return redo_plan(self.project) if redo_action else undo_plan(self.project)

        try:
            run_record, plan = await self.service(prepare)
            if (
                self.selected_event
                and self.selected_event["category"] == "run"
                and self.selected_event["id"] != run_record["id"]
            ):
                self.notify_state(
                    "Undo/redo follows session order. Select session "
                    + short(run_record["id"])
                    + " first.",
                    "error",
                )
                return

            def apply() -> dict[str, Any]:
                with self.project.lock():
                    return (redo if redo_action else undo)(
                        self.project,
                        acknowledge_git=True,
                        confirmed_plan=plan,
                        run_id=run_record["id"],
                    )

            self.pending = apply
            self.push_screen(
                ConfirmRestore(
                    plan,
                    "redo" if redo_action else "undo",
                    (
                        "SESSION "
                        + short(run_record["id"])
                        + " / PRE "
                        + short(run_record["pre"])
                        + " / POST "
                        + short(run_record["post"])
                    )
                    if self.advanced
                    else (
                        "Bring back the reviewed session changes."
                        if redo_action
                        else "Revert the reviewed session changes. Unrelated edits are preserved."
                    ),
                ),
                self.confirmed,
            )
        except Exception as exc:
            self.failure(exc)

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
                self.show_result(
                    result
                    if self.advanced
                    else "Changes verified. Use the main action to review the next step."
                )
                self.notify_state(
                    f"Verified {result['change_count']} changes. Recovery data retained.",
                    "success",
                )
            except Exception as exc:
                self.failure(exc)
