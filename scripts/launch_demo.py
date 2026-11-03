"""Capture a verified CLI demo; default is an explicitly labelled AI-authored edit replay."""

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coordinated-edit", action="store_true")
    parser.add_argument("--agent-command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    events = []
    stages = []
    timestamp = 0
    with tempfile.TemporaryDirectory(prefix="timemachine-launch-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        target = root / "hello.py"
        before = 'def greet(name):\n    return "Hello " + name\n'
        after = 'def greet(name):\n    return f"Hello {name.strip()}!"\n'
        target.write_text(before)

        def capture(title, command, expected=0):
            nonlocal timestamp
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=180)
            output = result.stdout + result.stderr
            assert result.returncode == expected, (command, result.returncode, output)
            # Presentation redacts only disposable absolute paths, never results.
            shown = ("$ " + shlex.join(command) + "\n" + output).replace(str(base), "<fixture>")
            shown = shown.replace(sys.executable, "python")
            events.append(
                [timestamp, "o", "\x1b[2J\x1b[H" + title + "\r\n\r\n" + shown.replace("\n", "\r\n")]
            )
            stages.append({"title": title, "text": shown, "exit_code": result.returncode})
            timestamp += 6
            return output

        def cli(title, *arguments, expected=0):
            return capture(
                title,
                [sys.executable, "-m", "timemachine", "--plain", "--human", *arguments],
                expected,
            )

        cli(
            "1 / Save a checkpoint (init alone is not a backup)",
            "init",
            "--storage",
            str(base / "store"),
        )
        cli("1 / Save a checkpoint", "checkpoint", "-m", "Before greeting change")
        agent = args.agent_command or [
            sys.executable,
            "-c",
            f'from pathlib import Path; Path("hello.py").write_text({after!r})',
        ]
        mode = (
            "Live agent command"
            if args.agent_command
            else "AI-authored edit replay (Python fixture; no live agent)"
        )
        if args.coordinated_edit:
            ready = args.output.resolve() / "READY"
            done = args.output.resolve() / "DONE"
            wait_script = (
                "from pathlib import Path; import time; "
                f"Path({str(ready)!r}).write_text(str(Path.cwd())); "
                f"done = Path({str(done)!r}); "
                "exec('while not done.exists(): time.sleep(0.1)'); "
                "print('Coordinated editor finished; capturing POST state.')"
            )
            agent = [sys.executable, "-c", wait_script]
            mode = "Live Codex tool edit; coordinated wait command"
        cli("2 / " + mode, "run", "--", *agent)
        assert target.read_text() != before, "Agent must change hello.py"
        actual_after = target.read_text()
        cli("3 / Review the recorded diff", "diff")
        cli("4 / Preview undo before writing", "undo", "--preview")
        cli("4 / Undo restores original bytes", "undo", "--yes")
        assert target.read_text() == before
        cli("5 / Redo reapplies recorded bytes", "redo", "--yes")
        assert target.read_text() == actual_after
        target.write_text("# newer user edit — keep this\n")
        cli("6 / Conflict refuses undo; newer work survives", "undo", "--yes", expected=1)
        assert target.read_text() == "# newer user edit — keep this\n"
        cli("7 / Verify stored integrity", "verify")
    (args.output / "evidence.json").write_text(
        json.dumps(
            {
                "mode": mode,
                "checks": (
                    "checkpoint, diff, undo bytes, redo bytes, "
                    "conflict preservation, integrity passed"
                ),
                "stages": stages,
            },
            indent=2,
        )
    )
    with (args.output / "demo.cast").open("x") as recording:
        recording.write(
            json.dumps(
                {"version": 2, "width": 120, "height": 36, "title": "TimeMachine v0.2.0 — " + mode}
            )
            + "\n"
        )
        for event in events:
            recording.write(json.dumps(event) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
