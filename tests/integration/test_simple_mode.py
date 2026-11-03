"""Beginner behavior exercised through visible controls and real disposable files."""

import asyncio
import sys

import pytest
from textual.widgets import Button, DataTable, RichLog, Static

from timemachine.runner import run
from timemachine.tui.app import ConfirmRestore, TimeMachineApp


async def settle(app, pilot):
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


async def wait_for(pilot, predicate):
    # Preview/execute handlers await filesystem I/O outside Textual's worker manager.
    for _ in range(100):
        if predicate():
            return
        await pilot.pause(0.05)
    assert predicate(), "UI operation did not finish within the bounded wait"


@pytest.mark.parametrize(
    "width,height", [(60, 24), (80, 24), (100, 30), (120, 40), (160, 45), (207, 58)]
)
def test_default_simple_layout_and_read_only_mode_switch(project, width, height):
    (project.root / "hello.py").write_text("before")
    with project.lock():
        run(
            project,
            [
                sys.executable,
                "-c",
                "from pathlib import Path; Path('hello.py').write_text('after')",
            ],
            project.root,
        )
    before = {
        p.relative_to(project.store): p.read_bytes()
        for p in project.store.rglob("*")
        if p.is_file()
    }

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(width, height)) as pilot:
            await settle(app, pilot)
            assert app.has_class("simple")
            assert not app.query_one("#dashboard").display
            assert not app.query_one("#ledger").display
            for name in ("undo-button", "mode-button", "help-button"):
                widget = app.query_one("#" + name, Button)
                assert widget.region.right <= width
                assert widget.region.bottom <= height
            assert "Undo" in str(app.query_one("#undo-button", Button).label)
            assert "#" not in str(app.query_one("#selection", Static).render())
            await pilot.click("#mode-button")
            await settle(app, pilot)
            assert app.advanced
            await pilot.press("a")
            await settle(app, pilot)
            assert not app.advanced
            await pilot.click("#help-button")
            await pilot.press("escape")
            await settle(app, pilot)
            assert app.focused is not None
            await pilot.press("1")
            assert app.focused is app.query_one("#timeline", DataTable)
            await pilot.press("slash")
            assert app.has_class("pane-history")
            assert app.focused.id == "filter"
            await pilot.press("escape", "2")
            assert app.focused is app.query_one("#files", DataTable)

    asyncio.run(exercise())
    after = {
        p.relative_to(project.store): p.read_bytes()
        for p in project.store.rglob("*")
        if p.is_file()
    }
    assert before == after
    assert (project.root / "hello.py").read_text() == "after"


def test_simple_undo_redo_cancel_and_conflict_preserve_user_work(project):
    (project.root / "x").write_text("before")
    with project.lock():
        run(
            project,
            [sys.executable, "-c", "from pathlib import Path; Path('x').write_text('after')"],
            project.root,
        )
    (project.root / "mine").write_text("unrelated")

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(100, 30)) as pilot:
            await settle(app, pilot)
            await pilot.click("#undo-button")
            await wait_for(pilot, lambda: isinstance(app.screen, ConfirmRestore))
            assert isinstance(app.screen, ConfirmRestore)
            assert app.focused.id == "cancel"
            await pilot.press("a")
            assert not app.advanced
            await pilot.press("escape")
            assert (project.root / "x").read_text() == "after"
            await pilot.click("#undo-button")
            await wait_for(pilot, lambda: isinstance(app.screen, ConfirmRestore))
            await pilot.click("#apply")
            await wait_for(pilot, lambda: not isinstance(app.screen, ConfirmRestore))
            await settle(app, pilot)
            assert (project.root / "x").read_text() == "before"
            assert app.primary_operation == "redo"
            await pilot.click("#undo-button")
            await wait_for(pilot, lambda: isinstance(app.screen, ConfirmRestore))
            await pilot.click("#apply")
            await wait_for(pilot, lambda: not isinstance(app.screen, ConfirmRestore))
            await settle(app, pilot)
            assert (project.root / "x").read_text() == "after"
            (project.root / "x").write_text("my newer edit")
            await pilot.click("#undo-button")
            await settle(app, pilot)
            assert not isinstance(app.screen, ConfirmRestore)
            assert app.query_one("#undo-button", Button).disabled
            assert (project.root / "x").read_text() == "my newer edit"
            assert (project.root / "mine").read_text() == "unrelated"

    asyncio.run(exercise())


def test_simple_initialization_does_not_claim_backup(project):
    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(80, 24)) as pilot:
            await settle(app, pilot)
            assert "no files saved" in str(app.query_one("#overview", Static).render())
            assert "YOUR_COMMAND" in "\n".join(
                line.text for line in app.query_one("#preview", RichLog).lines
            )
            assert app.query_one("#undo-button", Button).disabled
            await pilot.click("#help-button")
            assert app.focused.id == "close-help"
            await pilot.press("escape")

    asyncio.run(exercise())


def test_simple_confirmation_rechecks_current_files(project):
    (project.root / "x").write_text("before")
    with project.lock():
        run(
            project,
            [sys.executable, "-c", "from pathlib import Path; Path('x').write_text('after')"],
            project.root,
        )

    async def exercise():
        app = TimeMachineApp(project)
        async with app.run_test(size=(80, 24)) as pilot:
            await settle(app, pilot)
            await pilot.click("#undo-button")
            await wait_for(pilot, lambda: isinstance(app.screen, ConfirmRestore))
            assert isinstance(app.screen, ConfirmRestore)
            (project.root / "x").write_text("changed after review")
            await pilot.click("#apply")
            await wait_for(pilot, lambda: not isinstance(app.screen, ConfirmRestore))
            await settle(app, pilot)
            assert (project.root / "x").read_text() == "changed after review"
            assert app.query_one("#undo-button", Button).disabled

    asyncio.run(exercise())
