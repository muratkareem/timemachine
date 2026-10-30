"""Real inherited-terminal subprocess execution with durable PRE/POST association."""

import os
import signal
import subprocess
import threading
import uuid
from pathlib import Path
from types import FrameType
from typing import Any

from .checkpoint import checkpoint, now
from .errors import TimeMachineError
from .metadata import connect
from .project import Project

KNOWN_AGENTS = {"codex", "claude", "gemini", "aider"}


def finalize(project: Project, identifier: str, exit_code: int | None, status: str) -> str:
    with connect(project.store) as db:
        db.execute("UPDATE runs SET status='FINALIZING' WHERE id=?", (identifier,))
    post = checkpoint(project, "After wrapped command", "post")
    with connect(project.store) as db:
        db.execute(
            "UPDATE runs SET post=?,status=?,exit_code=? WHERE id=?",
            (post, status, exit_code, identifier),
        )
        db.execute("UPDATE runs SET state='invalidated' WHERE state='undone'")
    return post


def run(project: Project, argv: list[str], cwd: Path | None = None) -> dict[str, Any]:
    """Caller holds lock across the entire session. Never persist raw argv/env."""
    if threading.current_thread() is not threading.main_thread():
        raise TimeMachineError("Runner must execute on the main thread for signal handling")
    if not argv:
        raise TimeMachineError("Missing command: use run -- COMMAND [ARGS...]")
    identifier = uuid.uuid4().hex
    pre = checkpoint(project, "Before wrapped command", "pre")
    basename = Path(argv[0]).name
    agent = basename if basename in KNOWN_AGENTS else "command"
    with connect(project.store) as db:
        sequence = db.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM runs").fetchone()[0]
        db.execute(
            "INSERT INTO runs(id,created,agent,pre,status,pid,sequence) VALUES(?,?,?,?,?,?,?)",
            (identifier, now(), agent, pre, "RUNNING", os.getpid(), sequence),
        )
    child: subprocess.Popen[bytes] | None = None
    received: list[int] = []
    previous: dict[int, Any] = {}

    def forward(signum: int, frame: FrameType | None) -> None:
        received.append(signum)
        if child is not None and child.poll() is None:
            try:
                child.send_signal(signum)
            except ProcessLookupError:
                pass

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, forward)
        try:
            # Inherit all terminal descriptors, cwd and environment. No shell.
            child = subprocess.Popen(argv, cwd=cwd or Path.cwd(), shell=False)
            code = child.wait()
            status = "INTERRUPTED" if received or code < 0 else "COMPLETE"
        except OSError:
            # Do not record exception text: it can contain secret-bearing argv.
            code, status = 127, "LAUNCH_FAILED"
    finally:
        for restore_signum, handler in previous.items():
            signal.signal(restore_signum, handler)
    propagated = 128 - code if code < 0 else code
    if received and propagated == 0:
        propagated = 128 + received[-1]
    try:
        post = finalize(project, identifier, propagated, status)
    except BaseException as exc:
        raise TimeMachineError(
            f"Run {identifier} has no verified POST. PRE {pre} retained; "
            "quiesce writers and use doctor/finish-run."
        ) from exc
    return {
        "run": identifier,
        "pre": pre,
        "post": post,
        "exit_code": propagated,
        "status": status,
        "limitations": "Not a sandbox; detached children may keep writing",
    }


def finish_run(project: Project, identifier: str) -> dict[str, Any]:
    """User-requested late POST, never misrepresented as original command completion."""
    with connect(project.store) as db:
        row = db.execute("SELECT * FROM runs WHERE id=?", (identifier,)).fetchone()
    if row is None or row["post"] is not None:
        raise TimeMachineError("No unfinished run with that ID")
    post = finalize(project, identifier, None, "LATE_POST")
    return {
        "run": identifier,
        "post": post,
        "warning": "Late POST captures current state, including edits after interruption",
    }
