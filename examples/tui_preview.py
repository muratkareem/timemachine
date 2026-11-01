"""Export a real Textual screenshot using a disposable wrapped Python command."""

import argparse
import asyncio
import os
import sys
import tempfile
from pathlib import Path

from timemachine.checkpoint import checkpoint
from timemachine.project import Project
from timemachine.runner import run
from timemachine.tui.app import TimeMachineApp


async def render(
    output: Path, width: int = 140, height: int = 42, view: str = "dashboard", light: bool = False
) -> None:
    # Screenshot fixture explicitly chooses a capable color terminal. The shipped
    # application respects the user's NO_COLOR/terminal settings unchanged.
    os.environ.pop("NO_COLOR", None)
    os.environ["TERM"] = "xterm-256color"
    os.environ["COLORTERM"] = "truecolor"
    with tempfile.TemporaryDirectory(prefix="timemachine-tui-preview-") as temporary:
        base = Path(temporary)
        root = base / "atlas-api"
        root.mkdir()
        project = Project.init(root, base / "store")
        (root / "app.py").write_text(
            "\n".join(
                [
                    '"""Atlas API · request helpers."""',
                    "",
                    "def normalize_name(value: str) -> str:",
                    "    return value.strip()",
                    "",
                    "def greeting(name: str) -> dict[str, str]:",
                    '    return {"message": "Hello " + name}',
                    "",
                    "def health() -> dict[str, str]:",
                    '    return {"status": "ok"}',
                    "",
                ]
            )
        )
        (root / "legacy_config.py").write_text("DEBUG = True\n")
        with project.lock():
            checkpoint(project, "Before the request helper update")
            script = """from pathlib import Path
p = Path('app.py')
p.write_text(p.read_text().replace('return value.strip()',
    'return " ".join(value.split()).title()').replace('"Hello " + name',
    '"Hello " + normalize_name(name)'))
Path('legacy_config.py').unlink()
Path('tests').mkdir()
Path('tests/test_names.py').write_text(
    'from app import normalize_name\\n\\n'
    'def test_spaces():\\n'
    '    assert normalize_name("  ada  ") == "Ada"\\n')
"""
            run(project, [sys.executable, "-c", script], root)
        app = TimeMachineApp(project)
        async with app.run_test(size=(width, height)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            if light:
                await app.action_theme()
            if view == "diff":
                await pilot.press("enter")
            elif view == "restore":
                await pilot.press("u")
            await pilot.pause()
            await app.workers.wait_for_complete()
            output.parent.mkdir(parents=True, exist_ok=True)
            app.save_screenshot(filename=output.name, path=str(output.parent))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/timemachine-tui.svg"))
    parser.add_argument("--width", type=int, default=140)
    parser.add_argument("--height", type=int, default=42)
    parser.add_argument("--view", choices=["dashboard", "diff", "restore"], default="dashboard")
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    asyncio.run(render(args.output.resolve(), args.width, args.height, args.view, args.light))
