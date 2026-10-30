"""Measure only disposable local projects; never touches a developer project."""

import argparse
import json
import platform
import tempfile
import time
from pathlib import Path

from timemachine.checkpoint import checkpoint
from timemachine.operations import restore
from timemachine.project import Project
from timemachine.retention import storage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", type=int, default=200)
    parser.add_argument("--bytes", type=int, default=4096)
    args = parser.parse_args()
    if args.files <= 0 or args.bytes < 0:
        parser.error("positive files and nonnegative bytes required")
    with tempfile.TemporaryDirectory(prefix="timemachine-benchmark-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        project = Project.init(root, base / "store")
        for index in range(args.files):
            payload = (str(index).encode() + b"x" * args.bytes)[: args.bytes]
            (root / f"file-{index:06d}").write_bytes(payload)
        with project.lock():
            start = time.perf_counter()
            before = checkpoint(project, "benchmark baseline")
            first = time.perf_counter() - start
            start = time.perf_counter()
            checkpoint(project, "benchmark dedup")
            second = time.perf_counter() - start
            (root / "file-000000").write_bytes(b"modified")
            start = time.perf_counter()
            restore(project, before, "file-000000")
            restored = time.perf_counter() - start
            stats = storage(project)
        print(
            json.dumps(
                {
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "python": platform.python_version(),
                    "files": args.files,
                    "bytes_per_file": args.bytes,
                    "checkpoint_seconds": first,
                    "dedup_checkpoint_seconds": second,
                    "selective_restore_seconds": restored,
                    "object_bytes_including_recovery": stats["object_bytes"],
                    "note": "Single local run, warm caches possible; not a throughput guarantee",
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
