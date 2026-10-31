"""Public, disposable acceptance checks; usable with an installed release wheel."""

import asyncio
import json
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path

from timemachine.checkpoint import checkpoint, manifest, verify
from timemachine.errors import IntegrityError
from timemachine.git_context import git_context
from timemachine.metadata import connect
from timemachine.operations import recover
from timemachine.project import Project
from timemachine.restore_engine import execute
from timemachine.restore_plan import make_plan


def cli(root, *args, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "timemachine", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == expected, (args, result.stdout, result.stderr)
    assert "Traceback" not in result.stderr
    return json.loads(result.stdout or result.stderr)


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


async def packaged_tui(project):
    from timemachine.tui.app import TimeMachineApp

    assert files("timemachine.tui").joinpath("theme.tcss").is_file()
    app = TimeMachineApp(project)
    async with app.run_test(size=(70, 30)) as pilot:
        await pilot.pause()
        await pilot.press("?", "escape")


def main():
    with tempfile.TemporaryDirectory(prefix="timemachine-acceptance-") as temporary:
        base = Path(temporary)
        for git_project in (False, True):
            root = base / ("git-project" if git_project else "plain-project")
            root.mkdir()
            (root / "x").write_bytes(b"before\n")
            (root / ".gitignore").write_text("ignored\n")
            (root / "ignored").write_bytes(b"valuable\n")
            if git_project:
                git(root, "init", "-b", "main")
                git(root, "add", "x", ".gitignore")
                git(
                    root,
                    "-c",
                    "user.name=Fixture",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-m",
                    "fixture",
                )
                (root / "x").write_bytes(b"staged\n")
                git(root, "add", "x")
                (root / "x").write_bytes(b"before\n")
            before_git = git_context(root)
            guide = cli(root, "quickstart", "--json")
            assert guide["workflow"] and not (root / ".timemachine.json").exists()
            cli(root, "init", "--storage", str(base / (root.name + "-store")), "--json")
            assert cli(root, "list", "--json") == []  # init is not a checkpoint
            assert "ignored" in cli(root, "status", "--json")["included"]
            agent = (
                "from pathlib import Path; Path('x').write_bytes(b'after\\n'); "
                "Path('ignored').unlink(); Path('new').write_bytes(b'created')"
            )
            result = cli(root, "run", "--", sys.executable, "-c", agent)
            assert result["pre"] and result["post"]
            assert cli(root, "history", "--json")["runs"][0]["id"] == result["run"]
            assert cli(root, "diff", "--json")["change_count"] == 3
            (root / "unrelated").write_bytes(b"mine")
            cli(root, "undo", "--preview", "--json")
            assert (root / "x").read_bytes() == b"after\n"
            cli(root, "undo", "--yes", "--json")
            assert (root / "x").read_bytes() == b"before\n"
            assert (root / "ignored").read_bytes() == b"valuable\n"
            assert not (root / "new").exists()
            assert (root / "unrelated").read_bytes() == b"mine"
            assert git_context(root) == before_git
            cli(root, "redo", "--yes", "--json")
            assert (root / "x").read_bytes() == b"after\n"
            assert (root / "new").read_bytes() == b"created"
            (root / "x").write_bytes(b"newer user edit")
            assert "error" in cli(root, "undo", "--yes", "--json", expected=1)
            assert (root / "x").read_bytes() == b"newer user edit"
            assert git_context(root) == before_git
            assert cli(root, "verify", "--json")["integrity"] == "verified"
        project = Project.discover(root)
        with project.lock():
            before = checkpoint(project)
            (root / "x").write_bytes(b"current")
            (root / "new").write_bytes(b"current new")
            after = checkpoint(project)
            calls = []

            def fail(path, action):
                calls.append(path)
                if len(calls) == 2:
                    raise OSError(28, "injected disk exhaustion")

            try:
                execute(
                    project,
                    make_plan(project, manifest(project, after), manifest(project, before)),
                    "acceptance",
                    hook=fail,
                )
            except IntegrityError:
                pass
            else:
                raise AssertionError("Fault injection did not run")
        with connect(project.store) as db:
            row = db.execute("SELECT * FROM transactions WHERE status='FAILED'").fetchone()
            assert row and row["recovery"]
        with project.lock(allow_pending=True):
            preview = recover(project, row["id"], preview=True)
            assert preview["change_count"] > 0
            recover(project, row["id"])
            assert (root / "x").read_bytes() == b"current"
            assert (root / "new").read_bytes() == b"current new"
            assert verify(project)["integrity"] == "verified"
        asyncio.run(packaged_tui(project))
    print(
        json.dumps(
            {
                "normal_session": "passed",
                "unrelated_edits": "passed",
                "conflicting_edits": "refused",
                "git_invariants": "passed",
                "interrupted_restore_recovery": "passed",
                "packaged_tui": "passed",
                "first_run_workflow": "passed",
                "large_project": "run scripts/scale_benchmark.py separately",
            }
        )
    )


if __name__ == "__main__":
    main()
