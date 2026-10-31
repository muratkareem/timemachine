import sqlite3

import pytest

from timemachine.checkpoint import checkpoint, manifest, verify
from timemachine.errors import TimeMachineError
from timemachine.journal import pack, read_transaction_progress
from timemachine.metadata import connect, migrate, migration_plan
from timemachine.restore_engine import execute
from timemachine.restore_plan import make_plan


def legacy_store(project):
    with connect(project.store) as db:
        for row in db.execute("SELECT * FROM transactions").fetchall():
            progress = read_transaction_progress(db, row)
            db.execute(
                "UPDATE transactions SET progress=? WHERE id=?",
                (pack("progress", progress), row["id"]),
            )
        db.execute("DROP TABLE journal_steps")
        db.execute("PRAGMA user_version=1")


def test_v1_is_readable_and_explicit_migration_preserves_bytes(project):
    (project.root / "x").write_bytes(b"original")
    with project.lock():
        first = checkpoint(project)
        (project.root / "x").write_bytes(b"changed")
        second = checkpoint(project)
        execute(
            project, make_plan(project, manifest(project, second), manifest(project, first)), "test"
        )
    before = {p.name: p.read_bytes() for p in (project.store / "objects").iterdir()}
    legacy_store(project)
    assert verify(project)["integrity"] == "verified"
    assert migration_plan(project.store)["needed"]
    with pytest.raises(TimeMachineError, match="upgrade"), project.lock():
        pass
    with project.lock(allow_pending=True):
        result = migrate(project.store)
    assert result["from_version"] == 1 and result["to_version"] == 2
    backup = project.store / result["backup"].split("/")[-1]
    with sqlite3.connect(backup) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
    assert before == {p.name: p.read_bytes() for p in (project.store / "objects").iterdir()}
    assert verify(project)["integrity"] == "verified"
    with project.lock():
        checkpoint(project)
    assert not migrate(project.store)["needed"]


def test_failed_upgrade_is_atomic(project, monkeypatch):
    from timemachine import metadata

    legacy_store(project)
    original = metadata.MIGRATION_2
    monkeypatch.setattr(metadata, "MIGRATION_2", original + ("NOT VALID SQL",))
    with project.lock(allow_pending=True), pytest.raises(TimeMachineError):
        migrate(project.store)
    with connect(project.store) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE name='journal_steps'").fetchone()
            is None
        )
    monkeypatch.setattr(metadata, "MIGRATION_2", original)
    with project.lock(allow_pending=True):
        migrate(project.store)


def test_journal_step_deletion_blocks_verify_and_gc(project):
    from timemachine.retention import gc

    (project.root / "x").write_text("before")
    with project.lock():
        first = checkpoint(project)
        (project.root / "x").write_text("after")
        second = checkpoint(project)
        execute(
            project, make_plan(project, manifest(project, second), manifest(project, first)), "test"
        )
    with connect(project.store) as db:
        assert db.execute("SELECT count(*) FROM journal_steps").fetchone()[0] == 2
        db.execute("DELETE FROM journal_steps WHERE sequence=1")
    before = list((project.store / "objects").iterdir())
    with pytest.raises(TimeMachineError, match="journal"):
        gc(project, dry_run=False)
    assert all(p.exists() for p in before)
