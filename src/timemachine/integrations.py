"""Executable discovery only. No invented agent hooks or automatic agent launch."""

import os
import shlex
import shutil
import sys
from pathlib import Path

from .errors import TimeMachineError
from .runner import KNOWN_AGENTS


def capabilities() -> dict[str, dict[str, str | bool]]:
    return {
        agent: {
            "available": shutil.which(agent) is not None,
            "wrapper": f"timemachine run -- {agent}",
            "integration": "generic subprocess; no hooks",
        }
        for agent in sorted(KNOWN_AGENTS)
    }


def shell_integration(destination: Path) -> dict[str, object]:
    """Create, never activate, Bash/Zsh functions bound to explicit executables."""
    executables = {name: shutil.which(name) for name in sorted(KNOWN_AGENTS)}
    installed = {name: os.path.abspath(path) for name, path in executables.items() if path}
    if not installed:
        raise TimeMachineError(
            "No supported agent found on PATH; install one or use run -- COMMAND"
        )
    interpreter = shlex.quote(os.path.abspath(sys.executable))
    lines = [
        "# TimeMachine opt-in for Bash/Zsh. Review, then source this file.",
        "# Only this shell is affected. Disable with: unset -f " + " ".join(installed),
        "# Regenerate after moving/reinstalling TimeMachine or an agent.",
    ]
    for name, executable in installed.items():
        lines.append(
            f'{name}() {{ {interpreter} -m timemachine run -- {shlex.quote(executable)} "$@"; }}'
        )
    data = ("\n".join(lines) + "\n").encode()
    # Exclusive create prevents replacement of existing scripts or symlink targets.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {
        "file": str(destination.absolute()),
        "agents": sorted(installed),
        "activate": "Review the file, then source " + shlex.quote(str(destination.absolute())),
        "disable": "unset -f " + " ".join(installed),
        "scope": "Current Bash/Zsh shell only; no startup files or vendor settings changed",
    }
