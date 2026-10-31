import pytest

from timemachine.checkpoint import checkpoint, verify
from timemachine.errors import TimeMachineError
from timemachine.metadata import connect
from timemachine.project import Project
from timemachine.retention import deletion_plan, gc


@pytest.mark.parametrize(
    "raw", ["[]", "null", '{"version":1,"version":1}', '{"version":true}', '"string"']
)
def test_bad_config_has_actionable_error(project, raw):
    (project.root / ".timemachine.json").write_text(raw)
    with pytest.raises(TimeMachineError):
        Project.discover(project.root)


def test_private_storage_permissions_enforced(project):
    project.store.chmod(0o755)
    with pytest.raises(TimeMachineError, match="owner-only"):
        Project.discover(project.root)


@pytest.mark.parametrize(
    "field,value",
    [("status", "UNKNOWN"), ("tags", "null"), ("pinned", 3), ("status", "INCOMPLETE")],
)
def test_bad_catalog_blocks_gc_before_unlink(project, field, value):
    (project.root / "x").write_text("saved")
    with project.lock():
        identifier = checkpoint(project)
    objects = list((project.store / "objects").iterdir())
    with connect(project.store) as db:
        db.execute(f"UPDATE checkpoints SET {field}=? WHERE id=?", (value, identifier))
    with pytest.raises(TimeMachineError):
        gc(project, dry_run=False)
    assert all(p.exists() for p in objects)
    with pytest.raises(TimeMachineError):
        deletion_plan(project, identifier)


def test_missing_reference_blocks_verify_and_gc(project):
    with connect(project.store) as db:
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute(
            "INSERT INTO runs(id,created,agent,pre,status,pid,sequence) "
            "VALUES('bad','now','command','missing','RUNNING',1,1)"
        )
    with pytest.raises(TimeMachineError, match="references"):
        verify(project)
