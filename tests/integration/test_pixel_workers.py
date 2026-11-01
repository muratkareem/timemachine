import asyncio
import threading

from textual.widgets import DataTable, Input

from timemachine.checkpoint import checkpoint
from timemachine.tui.app import TimeMachineApp
from timemachine.ui_data import Workspace


def test_slow_selection_does_not_block_typing_or_repopulate_stale_files(project, monkeypatch):
    (project.root / "x").write_text("snapshot")
    with project.lock():
        checkpoint(project, "saved")
    entered, release = threading.Event(), threading.Event()
    original = Workspace.selection

    def slow(self, *args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Workspace, "selection", slow)

    async def exercise():
        app = TimeMachineApp(project)
        try:
            async with app.run_test(size=(120, 40)) as pilot:
                assert await asyncio.to_thread(entered.wait, 2)
                await pilot.press("slash", "z", "z", "z")
                assert app.query_one("#filter", Input).value == "zzz"
                assert app.query_one("#timeline", DataTable).row_count == 0
                release.set()
                await app.workers.wait_for_complete()
                await pilot.pause()
                assert app.selected_id is None and not app.file_items
                assert app.query_one("#files", DataTable).row_count == 0
        finally:
            release.set()

    asyncio.run(exercise())


def test_theme_switch_reuses_saved_data_and_preserves_selected_file(project, monkeypatch):
    (project.root / "a.py").write_text("first")
    (project.root / "z.py").write_text("last")
    with project.lock():
        checkpoint(project)

    def forbidden(*args, **kwargs):
        raise AssertionError("Theme switching must not read catalog, objects or live files")

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(160, 45)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            table = app.query_one("#files", DataTable)
            table.move_cursor(row=1)
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.preview_path == "z.py"
            monkeypatch.setattr(app, "dashboard", forbidden)
            monkeypatch.setattr(app.workspace, "timeline", forbidden)
            monkeypatch.setattr(app.workspace, "selection", forbidden)
            monkeypatch.setattr("timemachine.tui.app.text_content", forbidden)
            await app.action_theme()
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.theme == "timemachine-light"
            assert app.preview_path == "z.py" and app.preview_text == "last"
            assert table.cursor_row == 1

    asyncio.run(exercise())
