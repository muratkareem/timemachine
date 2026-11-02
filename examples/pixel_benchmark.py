"""Identical disposable UI workload for published v0.1.0 and candidate v0.2.0."""

import argparse
import asyncio
import json
import os
import platform
import resource
import statistics
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from textual.widgets import DataTable, Input

from timemachine import __version__
from timemachine.checkpoint import checkpoint
from timemachine.objects import ObjectStore
from timemachine.project import Project
from timemachine.runner import run
from timemachine.tui.app import TimeMachineApp
from timemachine.ui_data import Workspace


async def settle(app, pilot):
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    await app.workers.wait_for_complete()


async def measure(project, args):
    start = time.perf_counter()
    app = TimeMachineApp(project)
    async with app.run_test(size=(160, 45)) as pilot:
        await settle(app, pilot)
        startup = time.perf_counter() - start
        start = time.perf_counter()
        Workspace(project).timeline(50)
        headers = time.perf_counter() - start
        table = app.query_one("#timeline", DataTable)
        navigation = []
        for row in (1, 2, 3, 4, 5, 4, 3, 2, 1, 0):
            start = time.perf_counter()
            table.move_cursor(row=row)
            await settle(app, pilot)
            navigation.append(time.perf_counter() - start)
        start = time.perf_counter()
        files = app.query_one("#files", DataTable)
        files.move_cursor(row=list(app.file_items).index("large.py"))
        await settle(app, pilot)
        diff = time.perf_counter() - start
        assert "Truncated" in app.preview_text
        start = time.perf_counter()
        app.query_one("#find", Input).value = "value_"
        await settle(app, pilot)
        search = time.perf_counter() - start
        reads = 0
        original = ObjectStore.read

        def count(self, *arguments, **kwargs):
            nonlocal reads
            reads += 1
            return original(self, *arguments, **kwargs)

        start = time.perf_counter()
        with patch.object(ObjectStore, "read", count):
            await app.action_theme()
            await settle(app, pilot)
        theme = time.perf_counter() - start
        result = {
            "version": __version__,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "checkpoints": args.checkpoints,
            "files": args.files,
            "changed_source_lines": args.lines,
            "viewport": "160x45",
            "terminal_fixture": "xterm-256color / truecolor / no animation",
            "startup_settled_s": round(startup, 6),
            "timeline_50_headers_s": round(headers, 6),
            "navigation_median_settled_s": round(statistics.median(navigation), 6),
            "navigation_max_settled_s": round(max(navigation), 6),
            "large_diff_open_settled_s": round(diff, 6),
            "preview_search_settled_s": round(search, 6),
            "theme_switch_settled_s": round(theme, 6),
            "theme_object_reads": reads,
            "manifest_cache_entries": len(app.workspace.cache),
            "preview_display_lines": len(app.preview_text.splitlines()),
            "note": (
                "Single headless run; UI timings include frame/idle waits; "
                "RSS includes fixture construction"
            ),
        }
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["peak_process_rss_bytes"] = rss if sys.platform == "darwin" else rss * 1024
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoints", type=int, default=500)
    parser.add_argument("--files", type=int, default=1000)
    parser.add_argument("--lines", type=int, default=1800)
    args = parser.parse_args()
    os.environ.pop("NO_COLOR", None)
    os.environ["TERM"] = "xterm-256color"
    os.environ["COLORTERM"] = "truecolor"
    if (
        not 10 <= args.checkpoints <= 1000
        or not 10 <= args.files <= 10000
        or not 1100 <= args.lines <= 10000
    ):
        parser.error("checkpoints 10..1000, files 10..10000, lines 1100..10000")
    with tempfile.TemporaryDirectory(prefix="timemachine-pixel-benchmark-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        project = Project.init(root, base / "store")
        (root / "large.py").write_text("# initial history fixture\n")
        with project.lock():
            for i in range(args.checkpoints):
                checkpoint(project, f"Iteration {i:04d}")
            for i in range(args.files):
                (root / f"file-{i:05d}").write_text(f"original {i}\n")
            (root / "large.py").write_text("".join(f"value_{i} = {i}\n" for i in range(args.lines)))
            command = (
                "from pathlib import Path; p=Path('large.py'); "
                "p.write_text(p.read_text().replace(' = ', ' = -'))"
            )
            run(project, [sys.executable, "-c", command], root)
        print(json.dumps(asyncio.run(measure(project, args)), indent=2))


if __name__ == "__main__":
    main()
