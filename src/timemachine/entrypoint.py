"""Reject unsupported platforms before importing POSIX filesystem services."""

import sys


def main() -> None:
    if sys.platform not in {"darwin", "linux"}:
        print(
            "TimeMachine supports macOS and Linux local filesystems. "
            "Native Windows recovery has not been validated; use a Linux environment "
            "with its project and store on the Linux filesystem.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    from .cli import main as cli_main

    cli_main()
