"""Measure actual UI read-model behavior on disposable saved history."""

import argparse
import json
import platform
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from timemachine.checkpoint import checkpoint, get_checkpoint
from timemachine.history import history
from timemachine.project import Project
from timemachine.ui_data import Workspace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoints", type=int, default=120)
    args = parser.parse_args()
    if not 1 <= args.checkpoints <= 10000:
        parser.error("checkpoints must be 1..10000")
    with tempfile.TemporaryDirectory(prefix="timemachine-ux-benchmark-") as temp:
        base = Path(temp)
        root = base / "project"
        root.mkdir()
        project = Project.init(root, base / "store")
        (root / "file.py").write_text("print('checkpoint fixture')\n")
        with project.lock():
            for index in range(args.checkpoints):
                checkpoint(project, f"Saved iteration {index}")
        with patch("timemachine.history.get_checkpoint", wraps=get_checkpoint) as reads:
            start = time.perf_counter()
            history(project, 50)
            baseline = time.perf_counter() - start
            baseline_reads = reads.call_count
        workspace = Workspace(project)
        with patch("timemachine.ui_data.get_checkpoint", wraps=get_checkpoint) as reads:
            start = time.perf_counter()
            events = workspace.timeline(50)
            headers = time.perf_counter() - start
            header_reads = reads.call_count
            start = time.perf_counter()
            for _ in range(20):
                workspace.selection(events[0])
            selections = time.perf_counter() - start
            selected_reads = reads.call_count - header_reads
        print(
            json.dumps(
                {
                    "platform": platform.platform(),
                    "python": platform.python_version(),
                    "saved_checkpoints": args.checkpoints,
                    "page_size": len(events),
                    "previous_history_seconds": baseline,
                    "previous_manifest_loads": baseline_reads,
                    "new_header_seconds": headers,
                    "new_header_manifest_loads": header_reads,
                    "twenty_selections_seconds": selections,
                    "selection_manifest_loads": selected_reads,
                    "cache_limit": 8,
                    "note": "Single small local run; not a large-project performance guarantee",
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
