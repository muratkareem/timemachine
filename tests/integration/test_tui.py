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
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            table = app.query_one("#timeline", DataTable)
            assert table.row_count == 2
            assert app.query_one("#files", DataTable).row_count == 1
            await pilot.press("b", "down", "d")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.anchor is not None
            await pilot.press("r")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert isinstance(app.screen, ConfirmRestore)
            await pilot.click("#cancel")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert (project.root / "file").read_text() == "after"
            await pilot.press("r")
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.click("#apply")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert (project.root / "file").read_text() == "before"

    asyncio.run(exercise())


def test_tui_restore_keeps_frozen_expected_state(project):
    (project.root / "file").write_text("before")
    with project.lock():
        checkpoint(project)
    (project.root / "file").write_text("after")

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("r")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert isinstance(app.screen, ConfirmRestore)
            (project.root / "file").write_text("later user edit")
            await pilot.click("#apply")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert (project.root / "file").read_text() == "later user edit"

    asyncio.run(exercise())


def test_tui_undo_refuses_changed_run_history(project):
    import subprocess
    import sys

    (project.root / "x").write_text("zero")

    def new_run(value):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "timemachine.cli",
                "run",
                "--",
                sys.executable,
                "-c",
                f"from pathlib import Path; Path('x').write_text({value!r})",
            ],
            cwd=project.root,
            capture_output=True,
            check=True,
        )

    new_run("one")

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("u")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert isinstance(app.screen, ConfirmRestore)
            await asyncio.to_thread(new_run, "two")
            await pilot.click("#apply")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert (project.root / "x").read_text() == "two"

    asyncio.run(exercise())


def test_narrow_empty_help_theme_and_keyboard(project):
    from textual.widgets import Input, Static

    from timemachine.tui.app import HelpScreen

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.has_class("narrow")
            assert app.query_one("#timeline", DataTable).row_count == 0
            await pilot.press("question_mark")
            assert isinstance(app.screen, HelpScreen)
            await pilot.press("escape")
            await pilot.press("t")
            assert app.theme == "timemachine-light"
            await pilot.press("slash")
            assert app.focused is app.query_one("#filter", Input)
            assert app.query_one("#overview", Static).region.width <= 60

    asyncio.run(exercise())


def test_filter_unicode_search_and_narrow_details(project):
    from textual.widgets import Input

    (project.root / "файл[red].py").write_text("before\n")
    with project.lock():
        checkpoint(project, "Unicode checkpoint")
        (project.root / "файл[red].py").write_text("after\n")
        checkpoint(project, "Second checkpoint")

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(70, 26)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("enter")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.has_class("detail-mode")
            assert "+after" in app.preview_text
            app.query_one("#find", Input).value = "after"
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.match_index == 0
            await pilot.press("escape")
            assert not app.has_class("detail-mode")
            app.query_one("#filter", Input).value = "Unicode"
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.query_one("#timeline", DataTable).row_count == 1
            assert "файл[red].py" in app.file_items

    asyncio.run(exercise())


def test_corrupt_manifest_refuses_selected_restore(project):
    from timemachine.metadata import connect

    (project.root / "x").write_text("data")
    with project.lock():
        identifier = checkpoint(project)
    with connect(project.store) as db:
        db.execute("UPDATE checkpoints SET digest=? WHERE id=?", ("0" * 64, identifier))

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.selected_id is None
            await pilot.press("r")
            assert not isinstance(app.screen, ConfirmRestore)
            assert (project.root / "x").read_text() == "data"

    asyncio.run(exercise())


def test_conflicting_undo_explains_safe_next_step(project):
    import sys

    from textual.widgets import Static

    from timemachine.runner import run

    (project.root / "x").write_text("before")
    with project.lock():
        run(
            project,
            [sys.executable, "-c", "from pathlib import Path; Path('x').write_text('after')"],
            project.root,
        )
    (project.root / "x").write_text("my newer work")

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("u")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert not isinstance(app.screen, ConfirmRestore)
            message = str(app.query_one("#notice", Static).render())
            assert "conflict" in message.lower() and "newer edits" in message
            assert (project.root / "x").read_text() == "my newer work"

    asyncio.run(exercise())


def test_binary_long_file_and_no_follow_preview(project):
    from textual.widgets import Input

    name = "очень-длинное-имя-" + "x" * 120
    (project.root / name).write_bytes(b"\0\xff")
    (project.root / "large-lines.py").write_text("x" * 600 + "\n" + "line\n" * 2100)
    (project.root / "link").symlink_to("/never/read/this")
    with project.lock():
        checkpoint(project)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(100, 32)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await app.preview_file(name)
            assert "Binary" in app.preview_text
            await app.preview_file("large-lines.py")
            assert "Truncated" in app.preview_text
            assert len(app.preview_text.splitlines()) <= 2001
            await app.preview_file("link")
            assert "/never/read/this" in app.preview_text
            app.query_one("#find", Input).value = "not found"
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.match_index == -1

    asyncio.run(exercise())


def test_typing_does_not_trigger_actions_and_modal_is_exclusive(project):
    from textual.widgets import Input

    (project.root / "x").write_text("before")
    with project.lock():
        checkpoint(project)
    (project.root / "x").write_text("after")

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("slash", "r", "u", "q", "t")
            assert app.query_one("#filter", Input).value == "ruqt"
            assert app.theme == "timemachine"
            app.query_one("#filter", Input).value = ""
            await pilot.press("escape", "r")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert isinstance(app.screen, ConfirmRestore)
            screens = len(app.screen_stack)
            await pilot.press("u", "r")
            assert len(app.screen_stack) == screens
            await pilot.press("escape")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert (project.root / "x").read_text() == "after"

    asyncio.run(exercise())


def test_empty_session_can_advance_history_without_touching_files(project):
    import sys

    from textual.widgets import Button

    from timemachine.metadata import connect
    from timemachine.runner import run

    (project.root / "x").write_text("unchanged")
    with project.lock():
        result = run(project, [sys.executable, "-c", "pass"], project.root)

    async def exercise():
        app = TimeMachineApp(project, advanced=True)
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("u")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert isinstance(app.screen, ConfirmRestore)
            assert str(app.screen.query_one("#apply", Button).label) == "Confirm history step"
            await pilot.click("#apply")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert (project.root / "x").read_text() == "unchanged"

    asyncio.run(exercise())
    with connect(project.store) as db:
        assert (
            db.execute("SELECT state FROM runs WHERE id=?", (result["run"],)).fetchone()[0]
            == "undone"
        )
        assert db.execute("SELECT count(*) FROM transactions").fetchone()[0] == 0
