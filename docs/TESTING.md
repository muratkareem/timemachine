# Test strategy

Use pytest tmp_path only. Unit: schemas, hashes, inclusion, diffs. Integration:
PRE/POST undo/redo, selective restore, storage, CLI and process behavior. Safety:
path traversal, symlink attacks, permissions, hardlinks, corruption, full disk,
interruption, external edits, incomplete state and lock contention. E2E: synthetic
agent in Git/non-Git projects; compare bytes/modes and HEAD/branch/index.

Run focused tests for each slice. Final gate: full pytest with coverage, Ruff,
mypy, wheel/sdist build and isolated wheel install. CI matrix covers Python 3.12+
on macOS/Linux; a configured matrix is not evidence of successful remote runs.

Final audit also checks checksummed plan/progress journals and retained journal
objects; checksum corruption must block recovery and GC. The local coverage report
uses pytest-cov in the pytest process; CLI subprocess tests run but their statements
are not added to that coverage number. See EDGE_CASES.md and STATUS.md for actual
commands/results/skips rather than inferring platform support from workflow config.
