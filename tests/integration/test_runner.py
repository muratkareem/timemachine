import json
import os
import subprocess
import sys

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


def test_signal_forwarding_finalizes_post(project):
    command = [
        sys.executable,
        "-m",
        "timemachine.cli",
        "run",
        "--",
        sys.executable,
        "-c",
        "import os,signal,time; os.kill(os.getppid(),signal.SIGTERM); time.sleep(10)",
    ]
    child = subprocess.run(command, cwd=project.root, capture_output=True, timeout=15)
    assert child.returncode == 143
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

    master, slave = pty.openpty()
    command = [
        sys.executable,
        "-m",
        "timemachine.cli",
        "run",
        "--",
        sys.executable,
        "-c",
        "import os; print('TTY',os.isatty(0),os.isatty(1),os.isatty(2))",
    ]
    try:
        child = subprocess.Popen(command, cwd=project.root, stdin=slave, stdout=slave, stderr=slave)
        child.wait(timeout=10)
        data = b""
        while select.select([master], [], [], 0.2)[0]:
            try:
                chunk = os.read(master, 8192)
                if not chunk:
                    break
                data += chunk
            except OSError:
                break
        assert child.returncode == 0
        assert b"TTY True True True" in data
    finally:
        os.close(master)
        if slave != -1:
            os.close(slave)
