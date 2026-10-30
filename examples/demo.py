"""Run the real CLI in an isolated project, verify undo/redo, clean up afterwards."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="timemachine-demo-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()

        def cli(*args: str) -> dict:
            result = subprocess.run(
                [sys.executable, "-m", "timemachine.cli", *args],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"timemachine {' '.join(args[:2])}")
            print(result.stdout or result.stderr)
            return json.loads(result.stdout or result.stderr)

        cli("init", "--storage", str(base / "store"))
        path = root / "hello.txt"
        path.write_text("before\n")
        cli(
            "run",
            "--",
            sys.executable,
            "-c",
            "from pathlib import Path; Path('hello.txt').write_text('after\\n')",
        )
        cli("diff", "--json")
        cli("undo", "--yes", "--json")
        assert path.read_text() == "before\n"
        cli("redo", "--yes", "--json")
        assert path.read_text() == "after\n"
        cli("verify", "--json")
        print("Verified undo/redo bytes in disposable project.")


if __name__ == "__main__":
    main()
