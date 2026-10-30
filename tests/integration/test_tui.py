import asyncio

from textual.widgets import DataTable

from timemachine.checkpoint import checkpoint
from timemachine.tui.app import ConfirmRestore, TimeMachineApp


def test_tui_real_history_diff_preview_and_confirmation(project):
    (project.root / "file").write_text("before")
    with project.lock():
        checkpoint(project, "first")
        (project.root / "file").write_text("after")
        checkpoint(project, "second")

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            table = app.query_one("#timeline", DataTable)
            assert table.row_count == 2
            assert app.query_one("#files", DataTable).row_count == 1
            await pilot.press("b", "down", "d")
            await pilot.pause()
            assert app.anchor is not None
            await pilot.press("r")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmRestore)
            await pilot.click("#cancel")
            await pilot.pause()
            assert (project.root / "file").read_text() == "after"
            await pilot.press("r")
            await pilot.pause()
            await pilot.click("#apply")
            await pilot.pause()
            assert (project.root / "file").read_text() == "before"

    asyncio.run(exercise())
