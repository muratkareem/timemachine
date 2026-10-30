import os
import sys

import pytest

from timemachine.checkpoint import checkpoint, manifest, verify
from timemachine.errors import IntegrityError, TimeMachineError
from timemachine.retention import delete, gc, pin, prune, storage, tag
from timemachine.runner import run


def test_shared_blobs_and_gc(project):
    path = project.root / "x"
    path.write_bytes(b"shared")
    with project.lock():
        a = checkpoint(project)
        b = checkpoint(project)
        digest = manifest(project, a)["x"].digest
        delete(project, a)
        assert gc(project)["objects"] == []
        delete(project, b)
        assert gc(project)["objects"] == [digest]
        assert (project.store / "objects" / digest).exists()
        result = gc(project, dry_run=False)
        assert result["reclaim_bytes"] == 6
        assert storage(project)["object_bytes"] == 0


def test_pin_tag_and_run_references(project):
    with project.lock():
        a = checkpoint(project)
        b = checkpoint(project)
        pin(project, a)
        tag(project, b, "important")
        result = run(project, [sys.executable, "-c", "pass"], project.root)
        for identifier in (a, b, result["pre"], result["post"]):
            with pytest.raises(TimeMachineError, match="retained"):
                delete(project, identifier)
        assert prune(project, 0)["delete"] == []


def test_gc_interrupted_is_repeatable(project, monkeypatch):
    (project.root / "x").write_text("a")
    with project.lock():
        a = checkpoint(project)
        (project.root / "x").write_text("b")
        b = checkpoint(project)
        delete(project, a)
        delete(project, b)
        original = os.unlink
        calls = []

        def fail(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("disk error")
            return original(path, *args, **kwargs)

        monkeypatch.setattr("timemachine.retention.os.unlink", fail)
        with pytest.raises(OSError):
            gc(project, dry_run=False)
        monkeypatch.setattr("timemachine.retention.os.unlink", original)
        assert len(gc(project)["objects"]) == 1
        gc(project, dry_run=False)
        assert verify(project)["complete_checkpoints"] == 0


def test_corrupt_manifest_blocks_gc(project):
    from timemachine.metadata import connect

    with project.lock():
        identifier = checkpoint(project)
        with connect(project.store) as db:
            db.execute("UPDATE checkpoints SET manifest=? WHERE id=?", (b"bad", identifier))
        with pytest.raises(IntegrityError):
            gc(project, dry_run=False)
