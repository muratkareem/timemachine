import asyncio

import pytest
from textual.widgets import DataTable

from timemachine.checkpoint import checkpoint
from timemachine.tui.app import TimeMachineApp


@pytest.mark.parametrize(
    "width,height", [(60, 24), (80, 24), (100, 30), (120, 40), (160, 45), (200, 55)]
)
def test_six_layouts_keep_work_and_navigation_inside_viewport(project, width, height):
    (project.root / "file.py").write_text("print('saved')\n")
    with project.lock():
        checkpoint(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(width, height)) as pilot:
            await pilot.pause()
            work = app.query_one("#workarea").region
            assert work.height >= 8
            assert work.bottom <= app.query_one("#activity").region.y
            assert work.right <= width
            timeline = app.query_one("#timeline", DataTable)
            assert abs(timeline.virtual_size.width - (timeline.size.width - 2)) <= 2
            for key, name in (("1", "timeline"), ("2", "files"), ("3", "preview")):
                await pilot.press(key)
                await pilot.pause()
                widget = app.query_one("#" + name)
                assert widget.display and widget.region.height >= 2
                assert widget.region.right <= width and widget.region.bottom < height
            await pilot.press("escape")
            assert app.focused is app.query_one("#timeline", DataTable)

    asyncio.run(exercise())


def test_resize_keeps_file_selection_and_returns_to_archive(project):
    (project.root / "файл.py").write_text("before")
    with project.lock():
        checkpoint(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(160, 45)) as pilot:
            await pilot.pause()
            selected = app.selected_id
            await pilot.resize_terminal(60, 24)
            await pilot.press("2", "enter")
            await pilot.pause()
            assert app.has_class("detail-mode")
            assert "before" in app.preview_text
            await pilot.resize_terminal(200, 55)
            await pilot.pause()
            assert app.selected_id == selected
            assert app.query_one("#files-pane").region.width > 60
            await pilot.press("1")
            assert not app.has_class("detail-mode")

    asyncio.run(exercise())
