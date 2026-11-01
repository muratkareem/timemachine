"""Capture actual disposable application states for v0.2.0 visual review."""

import argparse
import asyncio
from pathlib import Path

from tui_preview import render


async def main(output):
    for width, height in ((60, 24), (80, 24), (100, 30), (120, 40), (160, 45), (200, 55)):
        for light in (False, True):
            theme = "light" if light else "dark"
            await render(
                output / f"{theme}-{width}x{height}.svg",
                width,
                height,
                "diff" if width < 90 else "dashboard",
                light,
            )
    for view in ("undo", "redo", "restore", "conflict", "empty", "timeline"):
        await render(output / f"{view}.svg", 140, 42, view)
    await render(output / "narrow-review.svg", 60, 24, "undo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.output))
