import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from timemachine.checkpoint import checkpoint, manifest
from timemachine.errors import IntegrityError, TimeMachineError
from timemachine.models import Entry, load_manifest
from timemachine.operations import restore
from timemachine.project import Project
from timemachine.restore_engine import execute
from timemachine.restore_plan import make_plan
from timemachine.scanner import scan


def load(value):
    raw = json.dumps(value).encode()
    return load_manifest(raw, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize(
    "path",
    ["../outside", "/absolute", "a//b", ".GIT/config", ".TimeMachine.json", "a/../b", "link/child"],
)
def test_untrusted_manifest_paths(path):
    value = {"version": 1, "entries": {path: asdict(Entry("directory", 0o755))}}
    with pytest.raises(TimeMachineError):
        load(value)


def test_duplicate_and_portable_collision_manifests():
    raw = b'{"version":1,"version":1,"entries":{}}'
    with pytest.raises(IntegrityError, match="Duplicate"):
        load_manifest(raw, hashlib.sha256(raw).hexdigest())
    with pytest.raises(IntegrityError, match="collision"):
        load({"version": 1, "entries": {p: asdict(Entry("directory", 0o755)) for p in ("A", "a")}})


def test_casefold_reserved_entries_are_excluded(project):
    (project.root / ".GIT").mkdir()
    (project.root / ".GIT/config").write_text("must not snapshot")
    assert ".GIT" in scan(project).excluded


def test_exclusion_policy_change_refuses_restore(project):
    (project.root / "valuable").write_text("before")
    with project.lock():
        old = checkpoint(project)
        project.config["exclude"].append("valuable")
        with pytest.raises(TimeMachineError, match="excluded"):
            restore(project, old)


def test_stale_run_requires_explicit_late_finalization(project, monkeypatch):
    from timemachine import runner
    from timemachine.metadata import connect

    original = runner.checkpoint

    def fail_post(project, message, kind):
        if kind == "post":
            raise OSError("interrupted POST")
        return original(project, message, kind)

    monkeypatch.setattr(runner, "checkpoint", fail_post)
    with project.lock(), pytest.raises(TimeMachineError, match="no verified POST"):
        runner.run(project, [sys.executable, "-c", "pass"], project.root)
    with connect(project.store) as db:
        identifier = db.execute("SELECT id FROM runs").fetchone()[0]
    with pytest.raises(TimeMachineError, match="Unfinished run"), project.lock():
        pass
    monkeypatch.setattr(runner, "checkpoint", original)
    with project.lock(allow_unfinished=True):
        result = runner.finish_run(project, identifier)
        assert result["post"]
    with project.lock():
        pass


def test_permission_denied_leaves_incomplete(project, monkeypatch):
    from timemachine import scanner

    (project.root / "private").write_text("data")
    original = scanner.os.open

    def denied(name, *args, **kwargs):
        if name == "private":
            raise PermissionError("read denied")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(scanner.os, "open", denied)
    with project.lock(), pytest.raises(PermissionError):
        checkpoint(project)


def test_nested_repo_and_submodule_git_metadata_excluded(project):
    nested = project.root / "nested"
    nested.mkdir()
    (nested / ".git").write_text("gitdir: /external/not-followed")
    (nested / "file").write_text("nested worktree")
    with project.lock():
        entries = manifest(project, checkpoint(project))
    assert "nested/file" in entries
    assert "nested/.git" not in entries


def test_symlinks_restored_opaque_and_external_target_untouched(project, tmp_path):
    external = tmp_path / "outside"
    external.write_bytes(b"outside")
    link = project.root / "link"
    link.symlink_to(external)
    with project.lock():
        before = checkpoint(project)
        link.unlink()
        link.symlink_to("/changed/missing")
        after = checkpoint(project)
        execute(
            project, make_plan(project, manifest(project, after), manifest(project, before)), "test"
        )
    assert os.readlink(link) == str(external)
    assert external.read_bytes() == b"outside"


def test_mode_race_fails_without_chmod_of_replacement(project, monkeypatch):
    import timemachine.restore_engine as engine

    d = project.root / "d"
    d.mkdir()
    d.chmod(0o755)
    with project.lock():
        before = checkpoint(project)
        d.chmod(0o700)
        after = checkpoint(project)
        plan = make_plan(project, manifest(project, after), manifest(project, before))
        original = engine.os.open
        fired = []

        def race(name, flags, *args, **kwargs):
            if name == "d" and flags == engine.DIR_FLAGS and not fired:
                fired.append(True)
                d.rename(project.root / "moved")
                d.mkdir(mode=0o700)
            return original(name, flags, *args, **kwargs)

        def install_race(path, action):
            if action == "mode":
                monkeypatch.setattr(engine.os, "open", race)

        with pytest.raises(IntegrityError):
            execute(project, plan, "test", hook=install_race)
    assert d.stat().st_mode & 0o777 == 0o700


def test_large_file_and_many_entries(project):
    data = bytes(range(256)) * 8192
    (project.root / "large").write_bytes(data)
    directory = project.root / "many"
    directory.mkdir()
    for i in range(150):
        (directory / f"file-{i}").write_bytes(str(i).encode())
    with project.lock():
        before = checkpoint(project)
        (project.root / "large").write_bytes(b"after")
        restore(project, before, "large")
    assert (project.root / "large").read_bytes() == data


@settings(max_examples=15, deadline=None)
@given(
    st.lists(
        st.tuples(st.binary(max_size=200), st.sampled_from([0o600, 0o644, 0o755])),
        min_size=1,
        max_size=5,
    )
)
def test_generated_bytes_modes_roundtrip(values):
    import tempfile

    with tempfile.TemporaryDirectory(prefix="timemachine-property-") as temp:
        base = Path(temp)
        root = base / "project"
        root.mkdir()
        project = Project.init(root, base / "store")
        for i, (data, mode) in enumerate(values):
            p = root / f"file-\u0444-{i}"
            p.write_bytes(data)
            p.chmod(mode)
        with project.lock():
            before = checkpoint(project)
            for p in root.glob("file-*"):
                p.unlink()
            (root / "new").write_bytes(b"new")
            after = checkpoint(project)
            execute(
                project,
                make_plan(project, manifest(project, after), manifest(project, before)),
                "property",
            )
        for i, (data, mode) in enumerate(values):
            p = root / f"file-\u0444-{i}"
            assert p.read_bytes() == data
            assert p.stat().st_mode & 0o777 == mode
        assert not (root / "new").exists()
