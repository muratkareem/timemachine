import asyncio

from textual.widgets import Button, RichLog

from timemachine.models import Entry
from timemachine.restore_plan import Change, Plan
from timemachine.tui.app import ConfirmRestore, TimeMachineApp


def test_file_restore_cancel_and_apply_preserve_unrelated_edits(project):
    from timemachine.checkpoint import checkpoint

    (project.root / "x").write_text("saved")
    (project.root / "y").write_text("saved y")
    with project.lock():
        checkpoint(project)
    (project.root / "x").write_text("current")
    (project.root / "y").write_text("newer user y")

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("2", "s")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmRestore)
            assert [c.path for c in app.screen.plan.changes] == ["x"]
            await pilot.press("escape")
            assert (project.root / "x").read_text() == "current"
            await pilot.press("s")
            await pilot.pause()
            await pilot.click("#apply")
            await pilot.pause()
            assert (project.root / "x").read_text() == "saved"
            assert (project.root / "y").read_text() == "newer user y"

    asyncio.run(exercise())


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


def test_narrow_review_folds_exact_paths_instead_of_ellipsis(project):
    plan = Plan((Change("very-long-unbroken-path-" + "x" * 120, None, Entry("directory", 0o755)),))

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            app.push_screen(ConfirmRestore(plan))
            await pilot.pause()
            log = app.screen.query_one("#plan", RichLog)
            displayed = "".join(strip.text for strip in log.lines)
            assert "…" not in displayed
            assert displayed.count("x") >= 120
            assert not app.screen.query_one("#apply", Button).disabled
            await pilot.press("escape")

    asyncio.run(exercise())
