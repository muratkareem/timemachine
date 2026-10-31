# Measured local benchmark

## Production scale gate · 2026-10-31

Measured after deddd13 with the new journal/capture implementation. Every fixture
was disposable on local APFS, macOS 26.7.1 arm64, Python 3.12.14. One run per size,
possible warm caches; these are observations, not cross-platform guarantees.
Each contains unique 18-byte files, an 8 MiB binary and a 20-level empty-file tree.
The wrapper changes ten files; undo/redo validates the whole snapshot scope and
changes those ten. All byte checks, integrity verification and zero-reclaim GC
checks passed. Unchanged checkpoints added **zero object bytes** at every size;
catalog/manifests/recovery metadata still grow.

| Files | Fresh checkpoint | Unchanged | Diff | Undo | Redo | Verify | GC dry-run | Peak RSS |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.055 s | 0.035 s | 0.002 s | 0.109 s | 0.110 s | 0.010 s | 0.017 s | 36 MiB |
| 1,000 | 0.246 s | 0.096 s | 0.006 s | 0.276 s | 0.243 s | 0.036 s | 0.070 s | 43 MiB |
| 10,000 | 2.090 s | 0.818 s | 0.057 s | 1.630 s | 1.615 s | 0.335 s | 0.633 s | 75 MiB |
| 50,000 | 13.672 s | 5.359 s | 0.291 s | 9.100 s | 9.113 s | 1.911 s | 3.738 s | 164 MiB |

The 50,000-file history header page took 4.35 ms. Memory includes Python and
complete in-memory manifests; file contents stream, but metadata is O(files).
Small-file durability costs dominate fresh capture. No integrity hashing was
removed. This is not a 50,000-path restore benchmark.

A separate 1,000-file / **64 MiB binary** fixture changed all 1,000 files and
completed three undo/redo round trips. Undo took 1.92–1.98 s and redo 1.87–1.95 s;
peak RSS was 107 MiB. A separate 1,000-checkpoint one-file history returned fifty
headers in 0.51 ms with zero manifest loads; twenty repeated selections took
6.98 ms and loaded two cached manifests. Cache capacity remains eight.

Reproduce from an installed checkout (each command removes its own fixture):

```sh
python scripts/scale_benchmark.py --files 50000 --binary-mib 8
python scripts/scale_benchmark.py --files 1000 --binary-mib 64 --edits 1000 --roundtrips 3
python examples/ux_benchmark.py --checkpoints 1000
```

Raw measurements: [100](benchmarks/scale-100.json),
[1,000](benchmarks/scale-1000.json), [10,000](benchmarks/scale-10000.json),
[50,000](benchmarks/scale-50000.json), [repeated recovery](benchmarks/scale-repeated.json),
[1,000-checkpoint history](benchmarks/history-1000.json).
The script's session timing label was clarified after measurement; values are unchanged.

## Historical baseline

Re-executed against the final runtime implementation at 91a6caf:
`python examples/benchmark.py --files 200 --bytes 4096` on 2026-10-30.
Disposable project, 200 distinct 4 KiB files (819,200 protected bytes). Store and
project on the host local filesystem; one run, possible warm caches. This is a
small baseline, not a large-repository performance or cross-platform guarantee.

```json
{
  "platform": "macOS-26.7.1-arm64-arm-64bit",
  "machine": "arm64",
  "python": "3.12.14",
  "files": 200,
  "bytes_per_file": 4096,
  "checkpoint_seconds": 0.13340925000375137,
  "dedup_checkpoint_seconds": 0.051243667025119066,
  "selective_restore_seconds": 0.08193837502039969,
  "object_bytes_including_recovery": 819208,
  "note": "Single local run, warm caches possible; not a throughput guarantee"
}
```

Reproduce with an installed checkout. Increase file/byte counts deliberately;
all work occurs in TemporaryDirectory and the whole fixture is removed afterwards.
No benchmark files or snapshots from the developer project are used.

M11: benchmarking is implemented and measured. Watch mode, portable export/import,
compression and extension/plugin APIs are explicitly deferred. They would add
concurrency, extraction and format-compatibility risk without being required for
the verified snapshot/run/undo/redo/restore workflow. No placeholder commands ship.


# UX navigation measurement · 2026-10-31

Executed `python examples/ux_benchmark.py` against 120 real saved checkpoints
with one small file in an isolated temporary project. Measured the previous human
history service and the new UI metadata page, plus repeated cached selection.

```json
{
  "platform": "macOS-26.7.1-arm64-arm-64bit",
  "python": "3.12.14",
  "saved_checkpoints": 120,
  "page_size": 50,
  "previous_history_seconds": 0.017909875023178756,
  "previous_manifest_loads": 50,
  "new_header_seconds": 0.0005606660270132124,
  "new_header_manifest_loads": 0,
  "twenty_selections_seconds": 0.007293082948308438,
  "selection_manifest_loads": 2,
  "cache_limit": 8,
  "note": "Single small local run; not a large-project performance guarantee"
}
```

The result demonstrates bounded header work and cache reuse for this fixture.
It is not a UI startup, large-repository or general speed guarantee. Navigation
performs no project scan; regression tests prohibit scanner access. Snapshot
integrity and restore validation remain on the existing backend. This is not a
user study and no measured one-minute comprehension claim is made.
