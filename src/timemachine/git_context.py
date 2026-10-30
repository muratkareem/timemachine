"""Read-only Git observations. Never invoke hooks, reset, clean or update-index."""

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any


def git_context(root: Path) -> dict[str, Any]:
    def git(*args: str) -> bytes | None:
        try:
            result = subprocess.run(
                ["git", "--no-optional-locks", "-C", str(root), *args],
                capture_output=True,
                check=False,
                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except FileNotFoundError:
            return None

    directory = git("rev-parse", "--absolute-git-dir")
    if directory is None:
        return {"available": False}
    index_path = git("rev-parse", "--path-format=absolute", "--git-path", "index")
    index = None
    if index_path:
        try:
            index = hashlib.sha256(Path(os.fsdecode(index_path)).read_bytes()).hexdigest()
        except FileNotFoundError:
            pass
    return {
        "available": True,
        "head": os.fsdecode(git("rev-parse", "HEAD") or b""),
        "branch": os.fsdecode(git("symbolic-ref", "-q", "HEAD") or b""),
        "refs": hashlib.sha256(git("show-ref") or b"").hexdigest(),
        "index": index,
    }
