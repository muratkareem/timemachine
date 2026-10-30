import subprocess
import sys

import pytest

from timemachine.git_context import git_context
from timemachine.operations import undo, undo_plan
from timemachine.runner import run


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.mark.parametrize("use_git", [False, True])
def test_synthetic_agent_mvp(project, use_git):
    root = project.root
    (root / "tracked").write_bytes(b"committed")
    (root / ".gitignore").write_text("valuable\n")
    if use_git:
        git(root, "init", "-b", "main")
        git(root, "add", "tracked", ".gitignore")
        git(
            root,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "base",
        )
        (root / "tracked").write_bytes(b"staged")
        git(root, "add", "tracked")
    (root / "tracked").write_bytes(b"unstaged")
    (root / "valuable").write_bytes(b"ignored")
    (root / "untracked").write_bytes(b"untracked")
    (root / "exec").write_bytes(b"#!/bin/sh\n")
    (root / "exec").chmod(0o755)
    expected_git = git_context(root)
    agent = """from pathlib import Path
Path('tracked').write_bytes(b'agent')
Path('valuable').unlink()
Path('untracked').rename('renamed')
Path('exec').chmod(0o644)
Path('new').mkdir()
Path('new/binary').write_bytes(bytes(range(256)))
"""
    with project.lock():
        result = run(project, [sys.executable, "-c", agent], root)
        assert result["exit_code"] == 0
        (root / "unrelated").write_bytes(b"user")
        undo(project)
    assert (root / "tracked").read_bytes() == b"unstaged"
    assert (root / "valuable").read_bytes() == b"ignored"
    assert (root / "untracked").read_bytes() == b"untracked"
    assert (root / "exec").stat().st_mode & 0o777 == 0o755
    assert not (root / "new").exists()
    assert not (root / "renamed").exists()
    assert (root / "unrelated").read_bytes() == b"user"
    assert git_context(root) == expected_git


def test_agent_git_changes_warn_and_are_not_undone(project):
    root = project.root
    git(root, "init", "-b", "main")
    (root / "x").write_text("before")
    git(root, "add", "x")
    git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "base",
    )
    agent = """from pathlib import Path
import subprocess
Path('x').write_text('agent')
subprocess.run(['git','add','x'],check=True)
subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','agent'],check=True)
"""
    with project.lock():
        run(project, [sys.executable, "-c", agent], root)
        _, plan = undo_plan(project)
        assert plan.warnings
        after = git_context(root)
        undo(project, acknowledge_git=True)
    assert (root / "x").read_text() == "before"
    assert git_context(root) == after


def test_status_distinguishes_git_categories_and_preserves_index(project):
    from timemachine.history import status

    root = project.root
    git(root, "init", "-b", "main")
    (root / ".gitignore").write_text("ignored\n")
    (root / "tracked").write_bytes(b"staged")
    git(root, "add", ".gitignore", "tracked")
    (root / "ignored").write_text("valuable")
    (root / "untracked").write_text("untracked")
    before = git_context(root)
    result = status(project)
    assert "tracked" in result["categories"]["tracked"]
    assert "ignored" in result["categories"]["ignored"]
    assert "untracked" in result["categories"]["untracked"]
    assert git_context(root) == before
