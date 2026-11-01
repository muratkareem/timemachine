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
