"""Bounded real-backend benchmark. Every project and snapshot store is temporary."""

import argparse
import json
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path

from timemachine.checkpoint import checkpoint, verify
from timemachine.diff import compare
from timemachine.operations import redo, undo
from timemachine.project import Project
from timemachine.retention import gc, storage
from timemachine.runner import run
from timemachine.ui_data import Workspace


def measure(operation):
    start = time.perf_counter()
    value = operation()
    return value, round(time.perf_counter() - start, 6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", type=int, required=True)
    parser.add_argument("--binary-mib", type=int, default=8)
    parser.add_argument("--edits", type=int, default=10)
    parser.add_argument("--roundtrips", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.files <= 50000 or not 0 <= args.binary_mib <= 128:
        parser.error("files must be 1..50000 and binary-mib 0..128")
    if not 1 <= args.edits <= 50000 or not 1 <= args.roundtrips <= 10:
        parser.error("edits must be 1..50000 and roundtrips 1..10")
    with tempfile.TemporaryDirectory(prefix="timemachine-scale-") as temporary:
        base = Path(temporary)
        root = base / "project"
        root.mkdir()
        project = Project.init(root, base / "store")
        deep = root.joinpath(*("deep" + str(i) for i in range(20)))
        deep.mkdir(parents=True)
        (deep / "empty").write_bytes(b"")
        for i in range(args.files):
            folder = root / f"group-{i // 500:03d}"
            folder.mkdir(exist_ok=True)
            (folder / f"file-{i:06d}").write_bytes(f"original {i:08d}\n".encode())
        if args.binary_mib:
            (root / "binary").write_bytes(bytes(range(256)) * (args.binary_mib * 4096))
        with project.lock():
            first, fresh = measure(lambda: checkpoint(project, "scale baseline"))
            first_stats = storage(project)
            second, unchanged = measure(lambda: checkpoint(project, "scale unchanged"))
            unchanged_stats = storage(project)
            assert first_stats["object_bytes"] == unchanged_stats["object_bytes"]
            count = min(args.edits, args.files)
            agent = (
                "from pathlib import Path\n"
                + f"for i in range({count}):\n"
                + " p=Path(f'group-{i//500:03d}/file-{i:06d}')\n"
                + " p.write_bytes(b'agent change\\n')\n"
            )
            result, wrapped = measure(lambda: run(project, [sys.executable, "-c", agent], root))
            difference, diff_time = measure(lambda: compare(project, result["pre"], result["post"]))
            assert difference["change_count"] == count
            _, undo_time = measure(lambda: undo(project))
            assert (root / "group-000/file-000000").read_bytes() == b"original 00000000\n"
            _, redo_time = measure(lambda: redo(project))
            assert (root / "group-000/file-000000").read_bytes() == b"agent change\n"
            repeated = []
            for _ in range(args.roundtrips - 1):
                _, elapsed_undo = measure(lambda: undo(project))
                _, elapsed_redo = measure(lambda: redo(project))
                repeated.append({"undo_s": elapsed_undo, "redo_s": elapsed_redo})
            _, verified = measure(lambda: verify(project))
            collection, collected = measure(lambda: gc(project, dry_run=True))
            assert collection["reclaim_bytes"] == 0
            _, history_time = measure(lambda: Workspace(project).timeline(50))
            stats = storage(project)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform != "darwin":
            peak *= 1024
        print(
            json.dumps(
                {
                    "platform": platform.platform(),
                    "python": platform.python_version(),
                    "files": args.files,
                    "binary_mib": args.binary_mib,
                    "directory_depth": 20,
                    "edited_files": count,
                    "roundtrips": args.roundtrips,
                    "fresh_checkpoint_s": fresh,
                    "unchanged_checkpoint_s": unchanged,
                    "wrapped_session_s": wrapped,
                    "diff_s": diff_time,
                    "undo_s": undo_time,
                    "redo_s": redo_time,
                    "additional_roundtrips": repeated,
                    "verify_s": verified,
                    "gc_dry_run_s": collected,
                    "history_headers_s": history_time,
                    "initial_object_bytes": first_stats["object_bytes"],
                    "unchanged_object_bytes": unchanged_stats["object_bytes"],
                    "final_object_bytes": stats["object_bytes"],
                    "peak_rss_bytes": peak,
                    "note": "Disposable run; edited_files bounds undo/redo; warm cache possible",
                },
                indent=2,
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
