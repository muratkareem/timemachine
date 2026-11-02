import asyncio
import sys

from textual.widgets import Button

from timemachine.operations import undo
from timemachine.runner import run
from timemachine.tui.app import ConfirmRestore, TimeMachineApp


def session(project):
    (project.root / "x").write_text("before")
    with project.lock():
        return run(
            project,
            [sys.executable, "-c", "from pathlib import Path; Path('x').write_text('after')"],
            project.root,
        )


def test_primary_action_changes_to_redo_after_undo_and_cancel_is_default(project):
    session(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.primary_operation == "undo"
            await pilot.click("#undo-button")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmRestore)
            assert app.focused.id == "cancel"
            await pilot.click("#apply")
            await pilot.pause()
            assert app.primary_operation == "redo"
            assert "redo" in str(app.query_one("#undo-button", Button).label)
            assert (project.root / "x").read_text() == "before"
            await pilot.click("#undo-button")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmRestore) and app.screen.operation == "redo"
            await pilot.press("escape")
            assert (project.root / "x").read_text() == "before"

    asyncio.run(exercise())


def test_latest_undone_session_prioritizes_redo_over_older_applied_session(project):
    session(project)
    with project.lock():
        run(project, [sys.executable, "-c", "pass"], project.root)
        undo(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.catalog["undo"] and app.catalog["redo"]
            assert app.primary_operation == "redo"

    asyncio.run(exercise())


def test_empty_archive_disables_recovery_buttons(project):
    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.query_one("#undo-button", Button).disabled
            assert app.query_one("#restore-button", Button).disabled
            assert app.primary_operation is None

    asyncio.run(exercise())


def test_corrupt_refresh_clears_previous_recovery_availability(project):
    from timemachine.metadata import connect

    result = session(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.primary_operation == "undo"
            with connect(project.store) as db:
                db.execute("UPDATE checkpoints SET digest=? WHERE id=?", ("0" * 64, result["post"]))
            await pilot.press("f5")
            await pilot.pause()
            assert app.primary_operation is None
            assert app.query_one("#undo-button", Button).disabled
            assert app.query_one("#restore-button", Button).disabled
            assert (project.root / "x").read_text() == "after"

    asyncio.run(exercise())


def test_direct_background_actions_cannot_replace_pending_modal(project):
    session(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_undo()
            await pilot.pause()
            screen, pending = app.screen, app.pending
            await app.action_restore()
            await app.action_redo()
            assert app.screen is screen and app.pending is pending
            await pilot.press("escape")
            assert (project.root / "x").read_text() == "after"

    asyncio.run(exercise())
