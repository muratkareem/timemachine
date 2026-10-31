import json
import os
import shlex
import shutil
import subprocess
import sys

import pytest

from timemachine.integrations import shell_integration
from timemachine.metadata import connect


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_opt_in_preserves_argv_cwd_env_stdin_exit_and_records_session(
    project, tmp_path, monkeypatch, shell
):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} not installed")
    folder = tmp_path / "agent bin ' quoted"
    folder.mkdir()
    agent = folder / "codex"
    agent.write_text(
        f"#!{sys.executable}\n"
        "import os,sys\nfrom pathlib import Path\n"
        "assert sys.argv[1:] == ['spaces ; $not_shell', 'SECRET_ARGUMENT']\n"
        "assert os.environ['TM_TEST_ENV'] == 'inherited'\n"
        "Path('changed').write_bytes(sys.stdin.buffer.readline())\n"
        "print('agent stdout'); print('agent stderr',file=sys.stderr)\nsys.exit(7)\n"
    )
    agent.chmod(0o700)
    monkeypatch.setenv("PATH", str(folder))
    monkeypatch.setenv("TM_TEST_ENV", "inherited")
    output = tmp_path / "activate ' tm.sh"
    result = shell_integration(output)
    assert result["agents"] == ["codex"]
    assert output.stat().st_mode & 0o777 == 0o600
    command = f"source {shlex.quote(str(output))}\ncodex 'spaces ; $not_shell' SECRET_ARGUMENT"
    run = subprocess.run(
        [executable, "-c", command],
        cwd=project.root,
        input=b"inherited stdin\n",
        capture_output=True,
        timeout=20,
    )
    assert run.returncode == 7, run.stderr
    assert run.stdout == b"agent stdout\n"
    assert b"agent stderr" in run.stderr
    assert (project.root / "changed").read_bytes() == b"inherited stdin\n"
    with connect(project.store) as db:
        row = dict(db.execute("SELECT * FROM runs").fetchone())
    assert row["pre"] and row["post"] and row["agent"] == "codex"
    assert row["exit_code"] == 7
    assert "SECRET_ARGUMENT" not in json.dumps(row)
    assert os.environ["PATH"] == str(folder)


def test_integration_never_replaces_existing_file_or_link(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/codex")
    target = tmp_path / "keep"
    target.write_text("keep")
    link = tmp_path / "link"
    link.symlink_to(target)
    for destination in (target, link):
        with pytest.raises(FileExistsError):
            shell_integration(destination)
        assert target.read_text() == "keep"
