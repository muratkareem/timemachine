import json

import pytest
from typer.testing import CliRunner

from timemachine.cli import app
from timemachine.errors import TimeMachineError
from timemachine.project import Project
from timemachine.security import safe_path


def test_init_discover(project):
    assert Project.discover(project.root) == project
    assert (project.store.stat().st_mode & 0o777) == 0o700
    assert list(project.root.iterdir()) == [project.root / ".timemachine.json"]
    with pytest.raises(TimeMachineError, match="already initialized"):
        Project.init(project.root)


@pytest.mark.parametrize("path", ["../escape", "/abs", "a/../x", "a//b", ".git/config", ""])
def test_unsafe_paths(path):
    with pytest.raises(TimeMachineError):
        safe_path(path)


def test_internal_store_refused(tmp_path):
    with pytest.raises(TimeMachineError, match="outside"):
        Project.init(tmp_path, tmp_path / "store")


def test_moved(project, tmp_path):
    new = tmp_path / "moved"
    project.root.rename(new)
    with pytest.raises(TimeMachineError, match="moved"):
        Project.discover(new)


def test_lock(project):
    with project.lock(), pytest.raises(TimeMachineError, match="busy"), project.lock():
        pass


def test_cli_help_and_status(project, monkeypatch):
    monkeypatch.chdir(project.root)
    runner = CliRunner()
    assert runner.invoke(app, ["--help"]).exit_code == 0
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["project"]["id"] == project.config["id"]
