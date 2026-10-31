"""Record actual scripted CLI output as asciicast v2; no user project is accessed."""

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Refuse replacement; recordings contain only this synthetic fixture.
    with (
        args.output.open("x") as recording,
        tempfile.TemporaryDirectory(prefix="timemachine-recording-") as temporary,
    ):
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        (root / "hello.txt").write_text("before\n")
        recording.write(
            json.dumps(
                {
                    "version": 2,
                    "width": 100,
                    "height": 30,
                    "title": "TimeMachine · actual disposable CLI workflow",
                }
            )
            + "\n"
        )
        start = time.monotonic()

        def event(text):
            recording.write(json.dumps([round(time.monotonic() - start, 3), "o", text]) + "\n")

        commands = [
            ["init", "--storage", str(base / "store")],
            [
                "run",
                "--",
                sys.executable,
                "-c",
                "from pathlib import Path; Path('hello.txt').write_text('after\\n')",
            ],
            ["diff"],
            ["undo", "--preview"],
            ["undo", "--yes"],
            ["redo", "--yes"],
            ["verify"],
        ]
        for arguments in commands:
            command = [sys.executable, "-m", "timemachine", "--plain", *arguments]
            event("$ timemachine --plain " + shlex.join(arguments) + "\r\n")
            result = subprocess.run(
                command,
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30,
            )
            event(result.stdout.replace("\n", "\r\n"))
            assert result.returncode == 0, result.stdout
            if arguments[0] == "undo" and "--yes" in arguments:
                assert (root / "hello.txt").read_text() == "before\n"
            if arguments[0] == "redo":
                assert (root / "hello.txt").read_text() == "after\n"
            time.sleep(1)
        event("Verified undo/redo bytes. Disposable fixture removed on exit.\r\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
