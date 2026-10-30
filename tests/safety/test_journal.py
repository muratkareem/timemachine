import json

import pytest

from timemachine.checkpoint import checkpoint, manifest, verify
from timemachine.errors import IntegrityError
from timemachine.journal import pack, read_plan, read_progress
from timemachine.metadata import connect
from timemachine.operations import recover
from timemachine.restore_engine import execute
from timemachine.restore_plan import make_plan


@pytest.mark.parametrize("field", ["plan", "progress"])
def test_corrupt_journal_blocks_recovery_and_verify(project, field):
    path = project.root / "x"
    path.write_bytes(b"before")
    with project.lock():
        before = checkpoint(project)
        path.write_bytes(b"after")
        after = checkpoint(project)

        def fail(path, action):
            raise OSError("interrupted")

        with pytest.raises(IntegrityError):
            execute(
                project,
                make_plan(project, manifest(project, after), manifest(project, before)),
                "test",
                hook=fail,
            )
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM transactions").fetchone()
        value = json.loads(row[field])
        value["digest"] = "0" * 64
        # field comes only from the fixed parameter list above, not project data.
        db.execute(f"UPDATE transactions SET {field}=? WHERE id=?", (json.dumps(value), row["id"]))
    with project.lock(allow_pending=True):
        with pytest.raises(IntegrityError, match="journal"):
            recover(project, row["id"])
        with pytest.raises(IntegrityError, match="journal"):
            verify(project)
    assert path.read_bytes() == b"after"


def test_unsupported_or_malformed_journal_refused():
    for raw in ("[]", "{}", "not json", pack("progress", [{"path": "../escape"}])):
        with pytest.raises(IntegrityError):
            read_progress(raw)
    with pytest.raises(IntegrityError):
        read_plan(pack("plan", {"changes": [], "warnings": [], "change_count": 99}))


def test_shared_digest_inconsistent_size_is_detected(project):
    import hashlib

    from timemachine.models import Entry, dump_manifest

    (project.root / "a").write_bytes(b"data")
    (project.root / "b").write_bytes(b"data")
    with project.lock():
        identifier = checkpoint(project)
    entries = manifest(project, identifier)
    entries["b"] = Entry("file", 0o644, 999, entries["a"].digest)
    raw = dump_manifest(entries)
    with connect(project.store) as db:
        db.execute(
            "UPDATE checkpoints SET manifest=?,digest=? WHERE id=?",
            (raw, hashlib.sha256(raw).hexdigest(), identifier),
        )
    with pytest.raises(IntegrityError, match="sizes"):
        verify(project)
