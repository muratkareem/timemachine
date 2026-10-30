# Execution status

M0 complete: architecture v1, scope, threat model, conflict/recovery state machine,
roadmap and test strategy written. Inspected clean main at c32d009 (MIT preserved).
Validation: repository inspection; documentation cross-check (no code tests yet).
Push: not attempted. Next: M1 foundations and isolated init/config/CLI tests.
Safety concerns: all behavior is currently specification, not implemented.

M1 complete: installable Python 3.12 package, Typer CLI, private external init,
strict configuration/discovery, moved-root detection, SQLite v1 and flock.
Validation: editable install succeeded; `pytest tests/unit/test_project.py -q`:
11 passed. Last commit before M1: 19b11d3. Push pending snapshot gate.
Next: M2 scanner/store/checkpoint acceptance. No destructive operations yet.

M2 complete: no-follow scanner; SHA-256 deduplicated durable objects; stable double
scan; v1 hash-validated manifests; INCOMPLETE-before-scan lifecycle; Git context;
quota/size failures; integrity verification. Last prior commit: 11c457b.
Validation: `pytest tests/unit/test_snapshots.py -q`: 10 passed, 1 skipped (the
sandbox filesystem strips setuid; direct special-mode validator test passes).
`mypy`: success, 11 source files. Ruff clean. Push not yet attempted.
Next: M3 history/diff, then M4 restore safety gate.

M3 complete: exact content/type/mode diff, safe JSON-escaped text previews,
binary/encoding/size summaries, list/show/inspect/history/status/doctor/verify CLI.
Validation: `pytest tests/unit -q`: 23 passed, 1 filesystem setuid skip;
Ruff clean; mypy success (13 files). Last prior commit: 6e5a8fb. Push pending MVP.
Next: M4 immutable plans, recovery snapshots, journals and conflict-safe undo.

M4 complete: immutable conflict plans, scoped undo service, no-follow staging and
atomic per-file replace, before/after step journal, recovery checkpoint, exact
post-verification, explicit interrupted recovery and later-edit refusal.
Validation: `pytest tests/safety tests/unit -q`: 33 passed, 1 filesystem skip;
mypy success (16 files). Last prior commit: 7947bb0. Push pending M7 gate.
Safety: multi-file restore is not atomic; external races remain documented.
Next: M6 generic subprocess wrapper, then M7 end-to-end Git/non-Git gate.
