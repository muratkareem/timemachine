import asyncio

from textual.widgets import DataTable, Input

from timemachine.checkpoint import checkpoint
from timemachine.tui.app import TimeMachineApp


def test_file_pages_are_bounded_and_unicode_path_filter_can_find_hidden_entry(project):
    for i in range(405):
        (project.root / f"item-{i:03d}").write_text("saved")
    (project.root / "ПЛАН.md").write_text("unicode saved")
    with project.lock():
        checkpoint(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            table = app.query_one("#files", DataTable)
            assert table.row_count == 200
            await pilot.click("#next-files")
            await pilot.pause()
            assert table.row_count == 200 and app.file_offset == 200
            await pilot.press("f")
            app.query_one("#path-filter", Input).value = "план"
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.file_offset == 0 and table.row_count == 1
            assert table.get_cell("ПЛАН.md", "path").plain == "ПЛАН.md"
            await pilot.press("enter", "3")
            await app.workers.wait_for_complete()
            assert app.preview_text == "unicode saved"

    asyncio.run(exercise())


def test_ascii_no_color_chrome_and_reduced_motion(project, monkeypatch):
    monkeypatch.setenv("TIMEMACHINE_ASCII", "1")
    monkeypatch.setenv("NO_COLOR", "1")

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(160, 45)) as pilot:
            await pilot.pause()
            assert app.ascii and app.no_color and app.animation_level == "none"
            assert "[]==[]" in str(app.query_one("#pixel-mark").render())
            assert app.query_one("#history-pane").styles.border_top[0] == "ascii"

    asyncio.run(exercise())
