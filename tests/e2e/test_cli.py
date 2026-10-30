import json
import subprocess
import sys


def cli(project, *args, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "timemachine.cli", *args],
        cwd=project.root,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == expected, (args, result.stdout, result.stderr)
    assert "Traceback" not in result.stderr
    return json.loads(result.stdout) if result.stdout else None


def test_all_cli_workflows(project):
    (project.root / "x").write_text("before\n")
    first = cli(project, "checkpoint", "-m", "first", "--json")["id"]
    (project.root / "x").write_text("after\n")
    second = cli(project, "checkpoint", "--json")["id"]
    assert cli(project, "diff", first, second, "--json")["change_count"] == 1
    assert cli(project, "diff", first, second, "--name-only", "--json")["paths"] == ["x"]
    assert cli(project, "show", first, "--json")["id"] == first
    assert cli(project, "inspect", first, "--json")["id"] == first
    assert cli(project, "list", "--limit", "1", "--json")[0]["id"] == second
    cli(project, "restore", first, "--preview", "--json")
    assert (project.root / "x").read_text() == "after\n"
    cli(project, "restore", first, "--yes", "--json")
    assert (project.root / "x").read_text() == "before\n"
    cli(project, "tag", first, "keep")
    cli(project, "pin", second)
    extra = cli(project, "checkpoint", "--json")["id"]
    cli(project, "delete", extra, "--preview")
    cli(project, "delete", extra, "--yes")
    cli(project, "prune", "--preview")
    cli(project, "gc", "--dry-run")
    cli(project, "gc", "--yes")
    assert cli(project, "storage", "--json")["live_objects"] > 0
    assert cli(project, "verify", "--json")["integrity"] == "verified"
    assert cli(project, "doctor", "--json")["database"] == "ok"
    assert cli(project, "status", "--json")["included"] == ["x"]
    assert cli(project, "history", "--json")["restores"]
    assert "codex" in cli(project, "agents", "--json")


def test_machine_mutation_requires_yes_and_errors_are_actionable(project):
    result = subprocess.run(
        [sys.executable, "-m", "timemachine.cli", "undo", "--json"],
        cwd=project.root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "No applied" in json.loads(result.stderr)["error"]
    assert "Traceback" not in result.stderr


def test_rebind_moved_project(project, tmp_path):
    from timemachine.project import Project

    moved = tmp_path / "moved"
    project.root.rename(moved)
    result = subprocess.run(
        [sys.executable, "-m", "timemachine.cli", "rebind", "--yes"],
        cwd=moved,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert Project.discover(moved).root == moved
