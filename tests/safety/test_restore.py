import json

import pytest

from timemachine.checkpoint import checkpoint, manifest
from timemachine.errors import ConflictError, IntegrityError, TimeMachineError
from timemachine.metadata import connect
from timemachine.restore_engine import execute
from timemachine.restore_plan import make_plan


def pair(project):
    (project.root / "a").write_bytes(b"before")
    (project.root / "deleted").write_bytes(b"recover")
    with project.lock():
        pre = checkpoint(project)
        (project.root / "a").write_bytes(b"after")
        (project.root / "deleted").unlink()
        (project.root / "added").write_bytes(b"new")
        post = checkpoint(project)
    return manifest(project, pre), manifest(project, post)


def test_restore_preserves_unrelated_edits(project):
    pre, post = pair(project)
    (project.root / "unrelated").write_text("mine")
    with project.lock():
        plan = make_plan(project, post, pre)
        tx = execute(project, plan, "test")
    assert (project.root / "a").read_bytes() == b"before"
    assert (project.root / "deleted").read_bytes() == b"recover"
    assert not (project.root / "added").exists()
    assert (project.root / "unrelated").read_text() == "mine"
    with connect(project.store) as db:
        assert (
            db.execute("SELECT status FROM transactions WHERE id=?", (tx,)).fetchone()[0]
            == "COMPLETE"
        )


@pytest.mark.parametrize("path", ["a", "added", "deleted"])
def test_conflicts_no_mutation(project, path):
    pre, post = pair(project)
    (project.root / path).write_bytes(b"user edit")
    with project.lock(), pytest.raises(ConflictError):
        make_plan(project, post, pre)
    assert (project.root / "a").read_bytes() != b"before"
    assert (project.root / path).read_bytes() == b"user edit"


def test_interrupted_restore_retains_journal_and_recovery(project):
    pre, post = pair(project)
    calls = []

    def fail(path, action):
        calls.append(path)
        if len(calls) == 2:
            raise OSError(28, "disk full")

    with project.lock(), pytest.raises(IntegrityError, match="recovery checkpoint"):
        execute(project, make_plan(project, post, pre), "test", hook=fail)
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM transactions").fetchone()
        assert row["status"] == "FAILED"
        assert manifest(project, row["recovery"])["a"] == post["a"]
        assert json.loads(row["progress"])
    with pytest.raises(TimeMachineError, match="Unfinished"), project.lock():
        pass


def test_symlink_parent_attack(project, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x").write_text("outside")
    d = project.root / "d"
    d.mkdir()
    (d / "x").write_text("before")
    with project.lock():
        a = checkpoint(project)
        (d / "x").write_text("after")
        b = checkpoint(project)
        plan = make_plan(project, manifest(project, b), manifest(project, a))

        def attack(path, action):
            d.rename(project.root / "moved")
            d.symlink_to(outside)

        with pytest.raises(IntegrityError):
            execute(project, plan, "test", hook=attack)
    assert (outside / "x").read_text() == "outside"


def test_new_child_prevents_directory_delete(project):
    with project.lock():
        a = checkpoint(project)
        (project.root / "d").mkdir()
        (project.root / "d/x").write_text("agent")
        b = checkpoint(project)
        (project.root / "d/user").write_text("user")
        with pytest.raises(ConflictError):
            make_plan(project, manifest(project, b), manifest(project, a))
    assert (project.root / "d/user").read_text() == "user"


def test_type_transition_and_modes(project):
    path = project.root / "d"
    path.mkdir()
    (path / "x").write_bytes(b"x")
    with project.lock():
        a = checkpoint(project)
        (path / "x").unlink()
        path.rmdir()
        path.write_bytes(b"now a file")
        path.chmod(0o755)
        b = checkpoint(project)
        execute(project, make_plan(project, manifest(project, b), manifest(project, a)), "test")
        assert (path / "x").read_bytes() == b"x"
        execute(project, make_plan(project, manifest(project, a), manifest(project, b)), "test")
        assert path.read_bytes() == b"now a file"
        assert path.stat().st_mode & 0o777 == 0o755


def test_explicit_recovery_and_conflict(project):
    from timemachine.operations import recover

    pre, post = pair(project)
    calls = []

    def fail(path, action):
        calls.append(path)
        if len(calls) == 2:
            raise KeyboardInterrupt()

    with project.lock(), pytest.raises(IntegrityError):
        execute(project, make_plan(project, post, pre), "test", hook=fail)
    with connect(project.store) as db:
        identifier = db.execute("SELECT id FROM transactions").fetchone()[0]
    with project.lock(allow_pending=True):
        recover(project, identifier)
    assert (project.root / "a").read_bytes() == b"after"
    assert (project.root / "added").read_bytes() == b"new"
    assert not (project.root / "deleted").exists()
    with project.lock():
        pass


def test_recovery_refuses_newer_edit(project):
    from timemachine.operations import recover

    pre, post = pair(project)

    def fail(path, action):
        raise OSError("interrupted")

    with project.lock(), pytest.raises(IntegrityError):
        execute(project, make_plan(project, post, pre), "test", hook=fail)
    with connect(project.store) as db:
        identifier = db.execute("SELECT id FROM transactions").fetchone()[0]
    (project.root / "a").write_text("user edit")
    with project.lock(allow_pending=True), pytest.raises(ConflictError):
        recover(project, identifier)
    assert (project.root / "a").read_text() == "user edit"
