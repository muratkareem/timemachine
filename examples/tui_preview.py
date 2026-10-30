"""Export a real Textual screenshot using a disposable wrapped Python command."""

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path

from timemachine.project import Project
from timemachine.runner import run
from timemachine.tui.app import TimeMachineApp


async def render(output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="timemachine-tui-preview-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        project = Project.init(root, base / "store")
        (root / "hello.py").write_text('print("before")\n')
        payload = 'print("after")\n'
        script = f"from pathlib import Path; Path('hello.py').write_text({payload!r})"
        with project.lock():
            run(
                project,
                [
                    sys.executable,
                    "-c",
                    script,
                ],
                root,
            )
        app = TimeMachineApp(project)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            output.parent.mkdir(parents=True, exist_ok=True)
            app.save_screenshot(filename=output.name, path=str(output.parent))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/timemachine-tui.svg"))
    asyncio.run(render(parser.parse_args().output.resolve()))
