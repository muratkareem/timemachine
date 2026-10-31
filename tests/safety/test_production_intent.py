import sys

import pytest
from typer.testing import CliRunner

from timemachine.checkpoint import checkpoint, manifest
from timemachine.cli import app
from timemachine.errors import TimeMachineError
from timemachine.restore_engine import execute
from timemachine.restore_plan import make_plan
from timemachine.runner import run


def test_cli_confirmation_cannot_add_unreviewed_path(project, monkeypatch):
    (project.root / "x").write_text("before")
    with project.lock():
        run(
            project,
            [sys.executable, "-c", "from pathlib import Path; Path('x').write_text('after')"],
            project.root,
        )
    # The path already equals PRE at preview time, so the plan contains no writes.
    (project.root / "x").write_text("before")

    def consent(*args, **kwargs):
        (project.root / "x").write_text("after")
        return True

    monkeypatch.chdir(project.root)
    monkeypatch.setattr("timemachine.cli.confirm", consent)
    result = CliRunner().invoke(app, ["undo", "--yes"])
    assert result.exit_code != 0
    assert (project.root / "x").read_text() == "after"


def test_git_change_after_review_refuses_execution(project):
    import subprocess

    root = project.root
    subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
    (root / "x").write_text("before")
    with project.lock():
        before = checkpoint(project)
        (root / "x").write_text("after")
        after = checkpoint(project)
        plan = make_plan(project, manifest(project, after), manifest(project, before))
        subprocess.run(["git", "-C", str(root), "add", "x"], check=True)
        with pytest.raises(TimeMachineError, match="Git"):
            execute(project, plan, "test")
    assert (root / "x").read_text() == "after"


def test_already_target_entry_is_still_revalidated(project):
    (project.root / "x").write_text("before")
    with project.lock():
        before = checkpoint(project)
        (project.root / "x").write_text("after")
        after = checkpoint(project)
        (project.root / "x").write_text("before")
        plan = make_plan(project, manifest(project, after), manifest(project, before))
        assert not plan.changes
        (project.root / "x").write_text("after")
        with pytest.raises(TimeMachineError):
            execute(project, plan, "test")


def test_recovery_confirmation_uses_reviewed_noop_plan(project, monkeypatch):
    from timemachine.metadata import connect

    (project.root / "x").write_text("before")
    with project.lock():
        before = checkpoint(project)
        (project.root / "x").write_text("after")
        after = checkpoint(project)

        def interrupt(path, action):
            raise OSError("interrupt before writes")

        with pytest.raises(TimeMachineError):
            execute(
                project,
                make_plan(project, manifest(project, after), manifest(project, before)),
                "test",
                hook=interrupt,
            )
    with connect(project.store) as db:
        transaction = db.execute("SELECT id FROM transactions").fetchone()[0]

    def consent(*args, **kwargs):
        (project.root / "x").write_text("before")
        return True

    monkeypatch.chdir(project.root)
    monkeypatch.setattr("timemachine.cli.confirm", consent)
    result = CliRunner().invoke(app, ["recover", transaction, "--yes"])
    assert result.exit_code != 0
    assert (project.root / "x").read_text() == "before"
    with connect(project.store) as db:
        assert (
            db.execute("SELECT status FROM transactions WHERE id=?", (transaction,)).fetchone()[0]
            == "FAILED"
        )


def test_parent_swap_between_guard_and_open_refused(project, monkeypatch):
    from contextlib import contextmanager

    from timemachine import restore_engine

    parent = project.root / "d"
    parent.mkdir()
    (parent / "x").write_text("before")
    with project.lock():
        before = checkpoint(project)
        (parent / "x").write_text("after")
        after = checkpoint(project)
        plan = make_plan(project, manifest(project, after), manifest(project, before))
        original = restore_engine.parent_fd
        fired = []

        @contextmanager
        def swapped(root, path):
            if path == "d/x" and not fired:
                fired.append(True)
                parent.rename(project.root / "moved")
                parent.mkdir()
                (project.root / "moved/x").rename(parent / "x")
            with original(root, path) as result:
                yield result

        def arm(path, action):
            monkeypatch.setattr(restore_engine, "parent_fd", swapped)

        with pytest.raises(TimeMachineError):
            execute(project, plan, "test", hook=arm)
    assert (parent / "x").read_text() == "after"
