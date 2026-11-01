"""A real local-recovery workspace. Mutations always use the core safety engine."""

import asyncio
import difflib
import os
from collections.abc import Callable
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
        Binding("r", "restore", "Restore"),
        Binding("s", "restore_file", "Restore file", show=False),
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

    def __init__(self, project: Project):
        super().__init__()
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
        self.preview_text = ""
        self.file_mode = False
        self.match_index = -1
        self.catalog: dict[str, Any] = {}
        self.primary_operation: str | None = None
        self.page_size = 50
        self.service_lock = asyncio.Lock()
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
            yield Button("Field guide [?]", id="help-button")
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
                yield DataTable(
                    id="files",
                    cursor_type="row",
                    zebra_stripes=True,
                    show_row_labels=False,
                    cell_padding=1,
                )
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
        await self.action_refresh()
        self.query_one("#timeline", DataTable).focus()
        self.call_after_refresh(self.fit_tables)

    def fit_tables(self) -> None:
        timeline = self.query_one("#timeline", DataTable)
        files = self.query_one("#files", DataTable)
        if timeline.columns:
            timeline.columns[
                next(k for k in timeline.columns if k.value == "description")
            ].width = max(8, timeline.size.width - 24)
        if files.columns:
            files.columns[next(k for k in files.columns if k.value == "path")].width = max(
                8, files.size.width - 23
            )
        timeline.refresh(layout=True)
        files.refresh(layout=True)

    def layout_width(self, width: int) -> None:
        self.set_class(width < 120, "compact")
        self.set_class(width < 90, "narrow")
        self.set_class(self.size.height <= 30, "short")
        self.set_class(width >= 150, "wide")

    def on_resize(self, event: events.Resize) -> None:
        self.layout_width(event.size.width)
        if self.query("#timeline"):
            self.call_after_refresh(self.fit_tables)

    def notify_state(self, message: str, state: str = "") -> None:
        widget = self.query_one("#notice", Static)
        widget.set_classes(state)
        widget.update(Text(safe(message)))

    def show_result(self, value: Any) -> None:
        self.preview_text = ""
        log = self.query_one("#preview", RichLog)
        log.clear()
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
            context = (
                f"NEXT / {kind.upper()} session {short(run['id'])} / "
                "checks current files before consent"
            )
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
            self.workspace.reset()
            self.events = await self.service(lambda: self.workspace.timeline(self.page_size))
            self.render_timeline()
            data = await self.service(self.dashboard)
            self.catalog = data
            self.recovery_controls()
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
                "Saved snapshots are not a live backup. Preview undo checks conflicts."
            )
            self.query_one("#brand", Static).update(
                Text("TIME / MACHINE\nSAVE-STATE CONSOLE / " + safe(self.project.root.name))
            )
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
                    "  timemachine run -- codex\n\nOr save a manual checkpoint:\n"
                    "  timemachine checkpoint -m 'Before my changes'\n\n"
                    "Initialization alone does not back up your project."
                )
        except Exception as exc:
            self.failure(exc)

    def render_timeline(self) -> None:
        table = self.query_one("#timeline", DataTable)
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
            stamp, body = archive_record(item, self.palette)
            table.add_row(stamp, body, key=key, height=2)
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
            self.show_result("No matching history. Clear the filter or load older entries.")

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        key = str(event.row_key.value)
        try:
            if event.data_table.id == "timeline" and key in self.visible_events:
                item = self.visible_events[key]
                self.selected_event = item
                self.recovery_controls()
                self.selected_id = None
                self.selection = None
                self.file_items.clear()
                self.query_one("#files", DataTable).clear()
                self.query_one("#preview-title", Static).update("Reading saved selection…")
                selected = await self.service(lambda: self.workspace.selection(item, self.anchor))
                if self.selected_event is not item:
                    return
                self.selection = selected
                self.selected_id = selected["target"]
                self.recovery_controls()
                self.file_items = {f["path"]: f for f in selected["files"]}
                files = self.query_one("#files", DataTable)
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
                        f"{len(selected['files'])} entries · {short(selected['target'])}\n"
                        + (
                            "Compared with " + short(selected["base"])
                            if selected["base"]
                            else "Saved baseline"
                        )
                    )
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
                for path, change in self.file_items.items():
                    label = change["change"]
                    name = PurePosixPath(path)
                    location = str(name.parent) if str(name.parent) != "." else "/ project root"
                    entry = change["after"] or change["before"]
                    files.add_row(
                        Text(labels[label], style=self.palette.get(label, "")),
                        Text(
                            safe(name.name) + "\n" + safe(location),
                            overflow="ellipsis",
                            no_wrap=True,
                        ),
                        Text(
                            "dir" if entry.kind == "directory" else size(entry.size),
                            style=self.palette["muted"],
                        ),
                        key=path,
                        height=2,
                    )
                self.call_after_refresh(self.fit_tables)
                if not self.file_items:
                    self.query_one("#preview-title", Static).update("No filesystem differences")
                    self.show_result("No filesystem differences in this selection.")
            elif event.data_table.id == "files" and key in self.file_items:
                await self.preview_file(key)
        except Exception as exc:
            self.failure(exc)

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

    async def preview_file(self, path: str) -> None:
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
                    f"Mode: {oct(entry.mode)} · SHA-256: {entry.digest or 'not a regular file'}\n"
                    f"Link target: {safe(entry.target) if entry.target else '—'}"
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
        if path not in self.file_items or self.file_items[path] is not change:
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
                + ("Saved file" if self.file_mode else "Unified diff / metadata")
                + " · v toggle\n"
                + metadata
            )
        )
        log = self.query_one("#preview", RichLog)
        log.clear()
        lexer = (
            Syntax.guess_lexer(path, code=self.preview_text)
            if (self.file_mode or not self.selection or not self.selection["base"])
            else "diff"
        )
        log.write(
            Syntax(
                self.preview_text or "Empty file",
                lexer,
                line_numbers=True,
                word_wrap=False,
                theme=SaveStateSyntax(self.palette),
            )
        )
        log.scroll_home(animate=False)

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter":
            self.render_timeline()
        elif event.input.id == "find":
            self.match_index = -1
            self.action_find_next()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "kind":
            self.render_timeline()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "find":
            self.action_find_next()
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

    def action_search(self) -> None:
        self.query_one("#filter", Input).focus()

    def action_next_row(self) -> None:
        if isinstance(self.focused, DataTable):
            self.focused.action_cursor_down()

    def action_previous_row(self) -> None:
        if isinstance(self.focused, DataTable):
            self.focused.action_cursor_up()

    async def action_diff(self) -> None:
        self.remove_class("pane-files")
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
        self.remove_class("detail-mode")
        self.add_class("pane-files")
        self.update_tabs("files")
        self.query_one("#files", DataTable).focus()
        self.call_after_refresh(self.fit_tables)

    async def action_inspect(self) -> None:
        await self.action_diff()
        self.query_one("#preview", RichLog).focus()

    def action_history(self) -> None:
        self.remove_class("detail-mode", "pane-files")
        self.update_tabs("archive")
        self.query_one("#timeline", DataTable).focus()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    @property
    def palette(self) -> dict[str, str]:
        return LIGHT if self.theme == "timemachine-light" else DARK

    async def action_theme(self) -> None:
        self.theme = "timemachine-light" if self.theme == "timemachine" else "timemachine"
        await self.action_refresh()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(self.screen, ModalScreen):
            return
        if event.button.id == "tab-archive":
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
        elif event.button.id == "more":
            more = await self.service(
                lambda: self.workspace.timeline(self.page_size, len(self.events))
            )
            self.events.extend(more)
            self.render_timeline()
            if not more:
                self.notify_state("All history loaded.")

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
                    "SAVE "
                    + short(identifier)
                    + " / "
                    + (safe(selector) if selector else "FULL CHECKPOINT"),
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
                    "SESSION "
                    + short(run_record["id"])
                    + " / PRE "
                    + short(run_record["pre"])
                    + " / POST "
                    + short(run_record["post"]),
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
                self.show_result(result)
                self.notify_state(
                    f"Verified {result['change_count']} changes. Recovery data retained.",
                    "success",
                )
            except Exception as exc:
                self.failure(exc)
