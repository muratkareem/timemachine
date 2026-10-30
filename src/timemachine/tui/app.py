"""A real local-recovery workspace. Mutations always use the core safety engine."""

import asyncio
import difflib
from collections.abc import Callable
from typing import Any

from rich.syntax import Syntax
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Button, DataTable, Footer, Input, RichLog, Select, Static

from ..diff import text_content
from ..git_context import git_context
from ..metadata import connect
from ..objects import ObjectStore
from ..operations import redo, redo_plan, restore, restore_plan, undo, undo_plan
from ..presentation import COLORS, LIGHT_COLORS, guidance, human, safe, short, size
from ..project import Project
from ..restore_plan import Plan
from ..ui_data import Workspace


class HelpScreen(ModalScreen[None]):
    CSS = """
    HelpScreen { align: center middle; }
    #help { width: 90%; max-width: 86; height: 85%; padding: 1 2;
            border: round $primary; background: $surface; }
    #help RichLog { height: 1fr; }
    """
    BINDINGS = [("escape", "close", "Close"), ("question_mark", "close", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="help"):
            yield Static("YOUR RECOVERY WORKSPACE", classes="heading")
            yield RichLog(id="help-text", wrap=True)
            yield Button("Back to project", id="close-help", variant="primary")

    def on_mount(self) -> None:
        self.query_one(RichLog).write(
            Text(
                "1  Wrap your agent: timemachine run -- COMMAND\n"
                "2  Select its session to inspect the changed files.\n"
                "3  Press u to preview undo and check conflicts. Confirm before writes.\n\n"
                "Arrows / j k    Navigate the focused list\n"
                "Enter / d       Open changes (also opens details on narrow screens)\n"
                "/              Filter timeline; Tab moves between panes\n"
                "Find text       Search this file or diff; Enter / n finds the next match\n"
                "b              Set a checkpoint as the comparison origin\n"
                "v              Toggle unified diff / saved file\n"
                "u / r / Ctrl+R Preview undo / checkpoint restore / redo\n"
                "Esc            Back to timeline or close dialog\n"
                "F5 / t / q     Refresh / switch light-dark theme / quit\n\n"
                "Saved does not mean current. Navigation reads snapshots, not live files.\n"
                "Undo preview checks current files. Newer conflicting edits are never forced.\n"
                "Git history and index are not restored. Excluded files are not protected.\n"
                "CLI alternative: timemachine --plain history; timemachine undo --preview --json"
            )
        )

    def action_close(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self) -> None:
        self.action_close()


class ConfirmRestore(ModalScreen[bool]):
    CSS = """
    ConfirmRestore { align: center middle; }
    #dialog { width: 92%; max-width: 100; height: 88%; border: round $warning;
              padding: 1 2; background: $surface; }
    #plan { height: 1fr; }
    #dialog Horizontal { height: 3; }
    #dialog Button { margin-right: 1; }
    """
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, plan: Plan, operation: str = "restore"):
        super().__init__()
        self.plan = plan
        self.operation = operation

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(f"REVIEW {self.operation.upper()} · no files changed yet")
            yield RichLog(id="plan", markup=False, wrap=True)
            yield Static(
                "A recovery checkpoint is saved before writes. Files are revalidated.\n"
                "Git history/index stay unchanged. Multi-file recovery is not atomic."
            )
            with Horizontal():
                yield Button("Apply changes", id="apply", variant="warning")
                yield Button("Cancel", id="cancel", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#plan", RichLog).write(human(self.plan.data()))
        self.query_one("#apply", Button).disabled = not self.plan.changes
        self.query_one("#cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "apply")

    def action_cancel(self) -> None:
        self.dismiss(False)


class TimeMachineApp(App[None]):
    TITLE = "TimeMachine"
    CSS_PATH = "theme.tcss"
    BINDINGS = [
        Binding("u", "undo", "Undo preview"),
        Binding("r", "restore", "Restore"),
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
        self.page_size = 50
        self.service_lock = asyncio.Lock()
        self.register_theme(
            Theme(
                name="timemachine",
                primary="#82D9C4",
                secondary="#C4B5FD",
                background="#0D1117",
                surface="#151C27",
                panel="#263142",
                foreground="#E4EBF5",
                success="#8ED6A4",
                warning="#F2CA82",
                error="#F397A4",
                accent="#C4B5FD",
                dark=True,
            )
        )
        self.register_theme(
            Theme(
                name="timemachine-light",
                primary="#166B58",
                secondary="#6944A0",
                background="#F4F6F9",
                surface="#FFFFFF",
                panel="#DAE1EB",
                foreground="#162535",
                success="#22663E",
                warning="#825A00",
                error="#AD2942",
                accent="#6944A0",
                dark=False,
            )
        )
        self.theme = "timemachine"
        self.animation_level = "none"

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
        }:
            return False
        return True

    def compose(self) -> ComposeResult:
        with Horizontal(id="brandbar"):
            yield Static(Text("TIME / MACHINE", style="bold"), id="brand")
            yield Static("LOCAL RECOVERY  /  ? HELP", id="tagline")
        with Grid(id="dashboard"):
            for name in ("protection", "session", "changes", "storage"):
                yield Static("Loading…", id=f"card-{name}", classes="card")
        yield Static("Loading project…", id="overview")
        with Horizontal(id="actions"):
            yield Button("Preview undo", id="undo-button", variant="primary")
            yield Button("Restore", id="restore-button")
            yield Button("Refresh", id="refresh-button")
            yield Button("Help ?", id="help-button")
        yield Static(
            "Saved snapshots are not a live backup. Select a session to inspect its files.",
            id="notice",
        )
        with Horizontal(id="workarea"):
            with Vertical(id="history-pane"):
                with Horizontal(id="filterbar"):
                    yield Input(placeholder="Filter timeline /", id="filter")
                    yield Select(
                        [
                            ("All", "all"),
                            ("Sessions", "run"),
                            ("Checkpoints", "checkpoint"),
                            ("Recovery", "restore"),
                        ],
                        value="all",
                        allow_blank=False,
                        id="kind",
                    )
                yield DataTable(id="timeline", cursor_type="row")
                yield Button("Load older history", id="more")
            with Vertical(id="files-pane"):
                yield Static("Select a session or checkpoint", id="selection")
                yield DataTable(id="files", cursor_type="row")
            with Vertical(id="preview-pane"):
                yield Static("A clearer view of every change", id="preview-title")
                yield Input(placeholder="Find in this file · Enter for next", id="find")
                yield RichLog(
                    id="preview", markup=False, highlight=False, wrap=False, auto_scroll=False
                )
        yield Static("Ready · navigation reads saved snapshots", id="activity")
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#history-pane").border_title = "TIMELINE · UTC"
        self.query_one("#files-pane").border_title = "FILES"
        self.query_one("#preview-pane").border_title = "INSPECT"
        self.query_one("#timeline", DataTable).add_columns("UTC / event", "Description / state")
        self.query_one("#files", DataTable).add_columns("Change", "Path")
        self.layout_width(self.size.width)
        await self.action_refresh()
        self.query_one("#timeline", DataTable).focus()

    def layout_width(self, width: int) -> None:
        self.set_class(width < 116, "compact")
        self.set_class(width < 88, "narrow")

    def on_resize(self, event: events.Resize) -> None:
        self.layout_width(event.size.width)

    def notify_state(self, message: str, state: str = "") -> None:
        widget = self.query_one("#notice", Static)
        widget.set_classes(state)
        widget.update(Text(safe(message)))

    def show_result(self, value: Any) -> None:
        log = self.query_one("#preview", RichLog)
        log.clear()
        log.write(human(value))

    def failure(self, exc: Exception) -> None:
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
        with connect(self.project.store) as db:
            cp = db.execute(
                "SELECT id,status,created FROM checkpoints ORDER BY created DESC LIMIT 1"
            ).fetchone()
            run = db.execute("SELECT * FROM runs ORDER BY sequence DESC LIMIT 1").fetchone()
            pending = db.execute(
                "SELECT count(*) FROM transactions WHERE status NOT IN ('COMPLETE','RECOVERED')"
            ).fetchone()[0]
        objects = list((self.project.store / "objects").iterdir())
        return {
            "checkpoint": dict(cp) if cp else None,
            "run": dict(run) if run else None,
            "pending": pending,
            "bytes": sum(p.lstat().st_size for p in objects),
            "git": git_context(self.project.root),
        }

    async def action_refresh(self) -> None:
        try:
            self.workspace.reset()
            self.events = await self.service(lambda: self.workspace.timeline(self.page_size))
            self.render_timeline()
            data = await self.service(self.dashboard)
            cp, run = data["checkpoint"], data["run"]
            needs_attention = data["pending"] or (
                run and run["status"] in ("RUNNING", "FINALIZING")
            )
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
                Text("TIME / MACHINE  /  " + safe(self.project.root.name))
            )
            self.query_one("#card-protection", Static).update(
                Text(
                    "PROTECTION\n" + state + "\nCurrent files not scanned",
                    style=self.palette["protected"],
                )
            )
            session = (
                f"{run['agent']} · {run['status']}\nExit {run['exit_code']} · {run['state']}"
                if run
                else "No sessions yet\nrun -- COMMAND to begin"
            )
            self.query_one("#card-session", Static).update(
                Text("LATEST SESSION\n" + safe(session, multiline=True))
            )
            self.query_one("#card-storage", Static).update(
                Text(
                    "SNAPSHOT STORAGE\n"
                    + size(data["bytes"])
                    + "\n"
                    + ("Latest " + short(cp["id"]) if cp else "No saved checkpoints")
                )
            )
            self.query_one("#card-changes", Static).update(
                "SELECTED CHANGES\nSelect a session\nUndo preview checks conflicts"
            )
            self.query_one("#overview", Static).update(
                Text(state + " · " + size(data["bytes"]) + " saved")
            )
            if run and run["post"]:
                pre, post = (
                    self.workspace.checkpoint(run["pre"]),
                    self.workspace.checkpoint(run["post"]),
                )
                if pre["git"] != post["git"] or post["git"] != data["git"]:
                    self.notify_state(
                        "Git metadata differs. File recovery never reverses commits or the index.",
                        "error",
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
            description = (
                item.get("message") or item.get("agent") or item.get("kind") or "Checkpoint"
            )
            status = item["status"]
            if item["category"] == "run":
                status += f" · {item['state']} · exit {item['exit_code']}"
            available = (
                "PRE/POST"
                if item.get("post")
                else "PRE only"
                if item["category"] == "run"
                else "saved"
            )
            table.add_row(
                Text(
                    item["created"][5:16].replace("T", " ")
                    + "\n"
                    + item["category"].upper()
                    + " "
                    + short(item["id"])
                ),
                Text(safe(description) + "\n" + safe(status) + " · " + available),
                key=key,
                height=2,
            )
        if table.row_count:
            table.move_cursor(row=selected_row)
        else:
            self.selected_id = None
            self.selected_event = None
            self.query_one("#files", DataTable).clear()
            self.show_result("No matching history. Clear the filter or load older entries.")

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        key = str(event.row_key.value)
        try:
            if event.data_table.id == "timeline" and key in self.visible_events:
                item = self.visible_events[key]
                self.selected_event = item
                self.selected_id = None
                self.selection = None
                self.file_items.clear()
                self.query_one("#files", DataTable).clear()
                selected = await self.service(lambda: self.workspace.selection(item, self.anchor))
                if self.selected_event is not item:
                    return
                self.selection = selected
                self.selected_id = selected["target"]
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
                for path, change in self.file_items.items():
                    label = change["change"]
                    files.add_row(
                        Text(label.upper(), style=self.palette.get(label, "")),
                        Text(safe(path)),
                        key=path,
                    )
                if not self.file_items:
                    self.show_result("No filesystem differences in this selection.")
            elif event.data_table.id == "files" and key in self.file_items:
                await self.preview_file(key)
        except Exception as exc:
            self.failure(exc)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "timeline":
            await self.action_diff()
        elif event.data_table.id == "files":
            self.query_one("#preview", RichLog).focus()

    async def preview_file(self, path: str) -> None:
        change = self.file_items[path]

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
                background_color="#F5F5F5" if self.theme == "timemachine-light" else "#151C27",
                theme="friendly" if self.theme == "timemachine-light" else "monokai",
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
        self.add_class("detail-mode")
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

    def action_history(self) -> None:
        self.remove_class("detail-mode")
        self.query_one("#timeline", DataTable).focus()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    @property
    def palette(self) -> dict[str, str]:
        return LIGHT_COLORS if self.theme == "timemachine-light" else COLORS

    async def action_theme(self) -> None:
        self.theme = "timemachine-light" if self.theme == "timemachine" else "timemachine"
        await self.action_refresh()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "undo-button":
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

    def plan_restore(self, identifier: str) -> Plan:
        with self.project.lock():
            return restore_plan(self.project, identifier)

    async def action_restore(self) -> None:
        if not self.selected_id:
            self.notify_state("Select a saved checkpoint or session first.")
            return
        identifier = self.selected_id
        try:
            plan = await self.service(lambda: self.plan_restore(identifier))

            def apply() -> dict[str, Any]:
                with self.project.lock():
                    return restore(self.project, identifier, plan=plan)

            self.pending = apply
            self.push_screen(ConfirmRestore(plan, "restore"), self.confirmed)
        except Exception as exc:
            self.failure(exc)

    async def stack_action(self, redo_action: bool) -> None:
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
                ConfirmRestore(plan, "redo" if redo_action else "undo"), self.confirmed
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
