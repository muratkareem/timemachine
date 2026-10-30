import json
import subprocess
import sys

from typer.testing import CliRunner

from timemachine.cli import app


def test_onboarding_is_clear_and_json_init_compatible(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.chdir(root)
    runner = CliRunner()
    result = runner.invoke(app, ["--plain", "init", "--storage", str(tmp_path / "store")])
    assert result.exit_code == 0
    assert "Initialization does not" in result.stdout
    assert "timemachine run -- codex" in result.stdout
    assert "Snapshots:" in result.stdout
    assert "node_modules" in result.stdout
    assert "\x1b" not in result.stdout


def test_json_wins_and_redirected_schema_is_unchanged(project, monkeypatch):
    monkeypatch.chdir(project.root)
    runner = CliRunner()
    result = runner.invoke(app, ["--human", "checkpoint", "--json"])
    assert result.exit_code == 0
    value = json.loads(result.stdout)
    assert set(value) == {"id", "status"}
    result = runner.invoke(app, ["list", "--json"])
    assert json.loads(result.stdout)[0]["id"] == value["id"]
    human = runner.invoke(app, ["--plain", "show", value["id"][:8]])
    assert human.exit_code == 0 and "Checkpoint" in human.stdout


def test_human_history_search_quickstart_and_agents(project, monkeypatch):
    monkeypatch.chdir(project.root)
    runner = CliRunner()
    runner.invoke(app, ["checkpoint", "-m", "release candidate"])
    result = runner.invoke(app, ["history", "--search", "release", "--json"])
    assert len(json.loads(result.stdout)["checkpoints"]) == 1
    result = runner.invoke(app, ["--plain", "quickstart"])
    assert result.exit_code == 0 and "Your first minute" in result.stdout
    assert "Coding agents" in result.stdout


def test_human_error_has_actionable_guidance_and_no_controls(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "timemachine.cli", "--plain", "status"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "timemachine init" in result.stderr
    assert "Traceback" not in result.stderr
    assert "\x1b" not in result.stderr


def test_quickstart_json_is_one_document_without_mutation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["--human", "quickstart", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "agents" in data and "workflow" in data
    assert not list(tmp_path.iterdir())
