# Measured local benchmark

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
