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


def path_categories(root: Path, paths: set[str]) -> dict[str, list[str]]:
    """Label included entries without refreshing or modifying the Git index."""
    result: dict[str, list[str]] = {}
    known: set[str] = set()
    if not git_context(root)["available"]:
        return {"non_git": sorted(paths)}
    commands = {
        "tracked": ["--cached"],
        "untracked": ["--others", "--exclude-standard"],
        "ignored": ["--others", "--ignored", "--exclude-standard"],
    }
    for category, args in commands.items():
        command = ["git", "--no-optional-locks", "-C", str(root), "ls-files", "-z", *args]
        response = subprocess.run(
            command, capture_output=True, check=False, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
        )
        if response.returncode != 0:
            result[category] = []
            continue
        found = {os.fsdecode(p) for p in response.stdout.split(b"\0") if p} & paths
        result[category] = sorted(found)
        known |= found
    result["unclassified_or_directory"] = sorted(paths - known)
    return result
