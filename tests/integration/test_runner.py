import json
import os
import subprocess
import sys

import pytest

from timemachine.history import history
from timemachine.metadata import connect
from timemachine.runner import run


def test_real_run_cwd_env_io_nonzero_and_redaction(project, monkeypatch, capfd):
    monkeypatch.setenv("TM_TEST_VALUE", "inherited")
    script = (
        "import os,sys,pathlib; "
        "pathlib.Path('file').write_text(os.environ['TM_TEST_VALUE']); "
        "print(os.getcwd()); print('stderr',file=sys.stderr); sys.exit(7)"
    )
    with project.lock():
        result = run(project, [sys.executable, "-c", script, "api_key=SECRET"], project.root)
    assert result["exit_code"] == 7
    assert result["status"] == "COMPLETE"
    out, err = capfd.readouterr()
    assert str(project.root) in out and "stderr" in err
    assert (project.root / "file").read_text() == "inherited"
    assert "SECRET" not in json.dumps(history(project))
    assert "api_key" not in json.dumps(history(project))


def test_missing_executable_still_has_post(project):
    with project.lock():
        result = run(project, ["/does/not/exist"], project.root)
    assert result["exit_code"] == 127
    assert result["status"] == "LAUNCH_FAILED"
    assert result["post"]


def test_no_shell_injection(project):
    with project.lock():
        result = run(
            project,
            [
                sys.executable,
                "-c",
                "import sys; assert sys.argv[1] == '; touch PWNED'",
                "; touch PWNED",
            ],
            project.root,
        )
    assert result["exit_code"] == 0
    assert not (project.root / "PWNED").exists()


@pytest.mark.parametrize("signal_name,expected", [("SIGTERM", 143), ("SIGINT", 130)])
def test_signal_forwarding_finalizes_post(project, signal_name, expected):
    command = [
        sys.executable,
        "-m",
        "timemachine.cli",
        "run",
        "--",
        sys.executable,
        "-c",
        f"import os,signal,time; os.kill(os.getppid(),signal.{signal_name}); time.sleep(10)",
    ]
    child = subprocess.run(command, cwd=project.root, capture_output=True, timeout=15)
    assert child.returncode == expected
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM runs").fetchone()
        assert row["status"] == "INTERRUPTED" and row["post"]


def test_pipe_stdin_stdout(project):
    command = [
        sys.executable,
        "-m",
        "timemachine.cli",
        "run",
        "--",
        sys.executable,
        "-c",
        "import sys; print('got:' + sys.stdin.readline().strip())",
    ]
    child = subprocess.run(command, cwd=project.root, input=b"hello\n", capture_output=True)
    assert child.returncode == 0 and b"got:hello" in child.stdout


def test_inherited_tty(project):
    import pty
    import select
    import time

    master, slave = pty.openpty()
    command = [
        sys.executable,
        "-m",
        "timemachine.cli",
        "run",
        "--",
        sys.executable,
        "-c",
        "import os; print('TTY',os.isatty(0),os.isatty(1),os.isatty(2)); print('x'*16384)",
    ]
    child = None
    try:
        child = subprocess.Popen(command, cwd=project.root, stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)
        slave = -1
        data = b""
        deadline = time.monotonic() + 20
        # A terminal emulator drains output while the child is running. Waiting
        # first can deadlock when the smaller macOS PTY buffer fills.
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(master, 8192)
                except OSError:
                    break
                if not chunk:
                    break
                data += chunk
        child.wait(timeout=max(0.1, deadline - time.monotonic()))
        assert child.returncode == 0
        assert b"TTY True True True" in data
        assert b"x" * 16384 in data
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        os.close(master)
        if slave != -1:
            os.close(slave)


def test_detached_child_late_write_is_a_conflict(project):
    import time

    from timemachine.errors import ConflictError
    from timemachine.operations import undo

    (project.root / "x").write_text("before")
    child_script = "import time,pathlib; time.sleep(0.6); pathlib.Path('x').write_text('late')"
    agent = (
        "import subprocess,sys,pathlib; pathlib.Path('x').write_text('post'); "
        f"subprocess.Popen([sys.executable,'-c',{child_script!r}],"
        "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,"
        "start_new_session=True)"
    )
    with project.lock():
        run(project, [sys.executable, "-c", agent], project.root)
    deadline = time.monotonic() + 5
    while (project.root / "x").read_text() != "late" and time.monotonic() < deadline:
        time.sleep(0.02)
    assert (project.root / "x").read_text() == "late"
    with project.lock(), pytest.raises(ConflictError):
        undo(project)


def test_sigkill_retains_pre_without_false_post(project):
    from timemachine.errors import TimeMachineError

    command = [
        sys.executable,
        "-m",
        "timemachine.cli",
        "run",
        "--",
        sys.executable,
        "-c",
        "import os,signal; os.kill(os.getppid(),signal.SIGKILL)",
    ]
    child = subprocess.run(command, cwd=project.root, capture_output=True, timeout=10)
    assert child.returncode == -9
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM runs").fetchone()
        assert row["pre"] and row["post"] is None and row["status"] == "RUNNING"
    with pytest.raises(TimeMachineError, match="Unfinished run"), project.lock():
        pass
