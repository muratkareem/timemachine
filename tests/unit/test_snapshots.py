import os

import pytest

from timemachine.checkpoint import checkpoint, manifest, verify
from timemachine.errors import IntegrityError, TimeMachineError
from timemachine.metadata import connect
from timemachine.scanner import scan


def test_snapshot_bytes_types_modes_and_dedup(project):
    for name, data in [
        ("empty", b""),
        ("binary", bytes(range(256))),
        ("\u0444\u0430\u0439\u043b\n", b"a"),
    ]:
        (project.root / name).write_bytes(data)
    (project.root / "copy").write_bytes(bytes(range(256)))
    (project.root / "emptydir").mkdir()
    (project.root / "link").symlink_to("/not/captured")
    (project.root / "empty").chmod(0o755)
    with project.lock():
        identifier = checkpoint(project)
        entries = manifest(project, identifier)
        assert entries["empty"].mode == 0o755
        assert entries["link"].target == "/not/captured"
        assert entries["emptydir"].kind == "directory"
        assert entries["binary"].digest == entries["copy"].digest
        assert verify(project)["objects_verified"] == 3


def test_ignored_included_optional_exclusions(project):
    (project.root / ".gitignore").write_text("valuable\n")
    (project.root / "valuable").write_text("secret")
    (project.root / "node_modules").mkdir()
    result = scan(project)
    assert "valuable" in result.entries
    assert "node_modules" in result.excluded


@pytest.mark.parametrize("kind", ["large", "hardlink", "fifo", "special_mode"])
def test_unsupported_fails_incomplete(project, kind):
    path = project.root / "file"
    path.write_bytes(b"data")
    if kind == "large":
        project.config["max_file_bytes"] = 1
    elif kind == "hardlink":
        os.link(path, project.root / "other")
    elif kind == "fifo":
        os.mkfifo(project.root / "pipe")
    else:
        path.chmod(0o4755)
        if not path.stat().st_mode & 0o4000:
            pytest.skip("Filesystem strips setuid; pure mode validation tested separately")
    with project.lock(), pytest.raises((IntegrityError, TimeMachineError)):
        checkpoint(project)
    with connect(project.store) as db:
        assert db.execute("SELECT status FROM checkpoints").fetchone()[0] == "INCOMPLETE"


def test_corruption(project):
    (project.root / "x").write_text("original")
    with project.lock():
        identifier = checkpoint(project)
    entry = manifest(project, identifier)["x"]
    (project.store / "objects" / entry.digest).write_text("corrupt")
    with pytest.raises(IntegrityError):
        verify(project)


def test_full_disk_incomplete(project, monkeypatch):
    (project.root / "x").write_text("data")

    def fail(*args):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("timemachine.objects.os.fsync", fail)
    with project.lock(), pytest.raises(OSError):
        checkpoint(project)
    with connect(project.store) as db:
        assert db.execute("SELECT status FROM checkpoints").fetchone()[0] == "INCOMPLETE"


def test_observed_race_incomplete(project, monkeypatch):
    from timemachine import checkpoint as module

    (project.root / "x").write_text("a")
    original = module.scan

    def racing(*args, **kwargs):
        result = original(*args, **kwargs)
        (project.root / "x").write_text("changed")
        return result

    monkeypatch.setattr(module, "scan", racing)
    with project.lock(), pytest.raises(IntegrityError, match="changed"):
        checkpoint(project)


def test_quota(project):
    project.config["quota_bytes"] = 1
    (project.root / "x").write_bytes(b"ab")
    with project.lock(), pytest.raises(TimeMachineError, match="quota"):
        checkpoint(project)


def test_special_mode_validation():
    from timemachine.models import mode_bits

    with pytest.raises(IntegrityError, match="Special permission"):
        mode_bits(0o104755)
