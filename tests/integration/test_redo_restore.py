import sys

import pytest

from timemachine.checkpoint import checkpoint
from timemachine.errors import ConflictError, TimeMachineError
from timemachine.operations import redo, restore, restore_plan, undo
from timemachine.runner import run


def command(project, text):
    return run(
        project,
        [sys.executable, "-c", f"from pathlib import Path; Path('x').write_text({text!r})"],
        project.root,
    )


def test_linear_undo_redo_multiple_runs(project):
    (project.root / "x").write_text("zero")
    with project.lock():
        command(project, "one")
        command(project, "two")
        undo(project)
        assert (project.root / "x").read_text() == "one"
        undo(project)
        assert (project.root / "x").read_text() == "zero"
        redo(project)
        assert (project.root / "x").read_text() == "one"
        redo(project)
        assert (project.root / "x").read_text() == "two"


def test_redo_conflict_and_invalidation(project):
    (project.root / "x").write_text("zero")
    with project.lock():
        command(project, "one")
        undo(project)
        (project.root / "x").write_text("user")
        with pytest.raises(ConflictError):
            redo(project)
        command(project, "new")
        with pytest.raises(TimeMachineError, match="No run"):
            redo(project)


def test_selective_restore_and_stale_plan(project):
    (project.root / "d").mkdir()
    (project.root / "d/x").write_text("original")
    (project.root / "other").write_text("original")
    with project.lock():
        old = checkpoint(project)
        (project.root / "d/x").write_text("new")
        (project.root / "other").write_text("user")
        plan = restore_plan(project, old, "d")
        (project.root / "d/x").write_text("later user edit")
        with pytest.raises(ConflictError):
            restore(project, old, "d", plan=plan)
        restore(project, old, "d")
    assert (project.root / "other").read_text() == "user"
    assert (project.root / "d/x").read_text() == "original"


def test_restore_deletes_later_paths_and_adds_missing_parent(project):
    (project.root / "d").mkdir()
    (project.root / "d/x").write_text("original")
    with project.lock():
        old = checkpoint(project)
        (project.root / "d/x").unlink()
        (project.root / "d").rmdir()
        restore(project, old, "d/x")
        assert (project.root / "d/x").read_text() == "original"
        (project.root / "later").write_text("later")
        restore(project, old)
        assert not (project.root / "later").exists()


def test_restore_invalidates_redo(project):
    (project.root / "x").write_text("zero")
    with project.lock():
        old = checkpoint(project)
        command(project, "one")
        undo(project)
        (project.root / "later").write_text("new")
        restore(project, old)
        with pytest.raises(TimeMachineError, match="No run"):
            redo(project)


@pytest.mark.parametrize("selector", ["..", "../outside", "/abs", ".git/config"])
def test_unsafe_selector(project, selector):
    with project.lock():
        old = checkpoint(project)
        (project.root / "x").write_text("new")
        with pytest.raises(TimeMachineError):
            restore(project, old, selector)
