import asyncio

from textual.widgets import Button

from timemachine.models import Entry
from timemachine.restore_plan import Change, Plan
from timemachine.tui.app import ConfirmRestore, TimeMachineApp


def test_large_review_cannot_apply_unshown_entries_and_escape_cancels(project):
    plan = Plan(tuple(Change(f"entry-{i}", None, Entry("directory", 0o755)) for i in range(501)))

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            app.push_screen(ConfirmRestore(plan))
            await pilot.pause()
            assert app.screen.query_one("#apply", Button).disabled
            assert app.focused.id == "cancel"
            await pilot.press("escape")
            assert not isinstance(app.screen, ConfirmRestore)
            assert not (project.root / "entry-0").exists()

    asyncio.run(exercise())
