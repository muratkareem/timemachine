# Current delivery status

Runtime implementation complete at **91a6caf**; final staging fault tests at
**8d1f50f**. All specified CLI commands and the optional real Textual TUI are
implemented. M0–M10 gates passed in MVP-first order. M11 benchmark/demo delivered;
watch/export/import/compression intentionally deferred. M12 local audit and the full six-job remote matrix passed.

Final local checks: `pytest --cov=timemachine --cov-report=term-missing
--cov-report=xml`: **94 passed, 4 skipped**, 98 collected, **83% coverage**
(1606 statements/277 missed), 11.50 s. Ruff/format clean (39 files), strict mypy
clean (22 files), wheel/sdist build and clean-wheel CLI recovery demo pass.
Four skips: three absent optional agents and sandbox-stripped setuid bit; direct
mode rejection validator passes. No known critical restore defect found by the
executed tests. Concurrency/hardware/metadata limitations remain in SAFETY.md.

Push: user explicitly authorized origin/main. Runtime through 91a6caf pushed;
final test/docs through 639548a are pushed; this verification record is pushed
during closeout without force. MIT
and original history preserved. No package publication, release or version tag.
Working tree is clean after the final documentation commit. Full commit ledger,
commands, milestone evidence, installation, limits and priorities: DELIVERY.md.

Remote verification PASS: workflow 41103386128 completed successfully for
639548a; six individually verified job conclusions, macOS/Linux x Python
3.12/3.13/3.14. Every job: 94 passed, 4 skipped, 83% coverage; lint/type/build/
demo/clean-install checks passed. See CI.md for exact Python versions and links.
Earlier queued snapshots in the milestone record are historical and superseded.
The final verification-record commit is documentation-only; tested code is unchanged.
Next concrete task: optional independent adversarial review and explicit future
migration tooling. No unresolved blocker or outstanding permission/credential request.

---

## Milestone record

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

M6 complete: real argv subprocess without shell; inherited cwd/env/stdin/out/err
and TTY; durable PRE/POST on nonzero/launch-failure/signals; signal forwarding;
redacted metadata; late POST command for crashes, no automatic rollback.
Initial M6 validation: 5 passed, 1 failed (missing os import in PTY test);
Ruff caught the same missing import. The premature completion entry was
corrected at M7; runner behavior itself was not the failing path.
Mypy success (17 files).
Last prior commit: 2d868eb. Push pending M7. Next: complete MVP acceptance gate.

M7 MVP gate PASS: corrected PTY test import and drained PTY before closing its
last slave (macOS discards pending data on last-slave close). Full `pytest -q`:
42 passed, 1 filesystem setuid skip. Ruff clean; mypy success (17 source files).
Synthetic agent creates/edits/deletes/renames files and changes modes; undo
preserves unrelated edits in Git and non-Git projects. Dirty/staged/untracked/
ignored bytes and executable modes restored; HEAD/branch/refs/index unchanged.
Agent-created Git commit test emits mismatch and leaves Git metadata untouched.
README, install/CLI/recovery docs describe actual MVP behavior and limitations.
Last prior commit: 9969904. Push pending remote/auth check. Next: M5 redo and
selective restore, then storage/TUI/integrations/final audit.

M5 complete: linear multi-run redo, conflict checks/invalidation, full or selective
file/directory restore, missing ancestor creation, confirmed immutable plans,
explicit moved-root rebind. Last prior commit: 7c007dc. Push blocked: automatic
approval review requires explicit user authorization for origin/main; question
pending. Validation: `pytest tests/integration/test_redo_restore.py tests/safety -q`:
19 passed; Ruff clean; mypy success (17 files). Next: M8 storage/retention.

M8 complete: storage statistics, quotas, verify, tag/pin/delete, reference-aware
pruning and GC. All journal-described object references retained conservatively.
GC is idempotent after interrupted unlink; corruption blocks collection.
Validation: `pytest tests/integration/test_retention.py -q`: 4 passed; Ruff clean;
mypy success (18 files). Last prior commit: 837e01c. Push still awaiting explicit
authorization after automatic-review rejection. Next: M9 real Textual browser.
Compression/automatic scheduled retention deliberately not implemented.

M9 complete: optional Textual live checkpoint timeline/file table, safely escaped
text/binary preview, checkpoint comparison, progress indicator, keyboard controls,
confirmed restore/undo/redo using frozen plans. Headless pilot exercises real
history, diff, cancel and successful restore. No mock data.
Validation: `pytest tests/integration/test_tui.py tests/integration/test_redo_restore.py -q`:
10 passed; Ruff clean; mypy success (20 source files).
Last prior commit: 6171305. Push awaiting user authorization. Next: M10 integrations,
M11 justified advanced work/defer decision, M12 safety/quality/release audit.

M10 complete: executable capability discovery and documented generic wrappers for
Codex/Claude/Gemini/Aider, verified vendor sources and truthful capability limits.
Codex wrapped --help smoke passed; no account/API invocation. Other three absent.
Validation: `pytest tests/integration/test_integrations.py tests/integration/test_tui.py -q`:
3 passed, 3 absent-executable skips; Ruff clean; mypy success (21 files).
TUI undo/redo confirmation now freezes both run ID and immutable plan.
Last prior commit: e32f5f6. User explicitly authorized origin/main push; pending
remote-state check. Next: M11 benchmark/defer decision and M12 full safety audit.

M12 safety-audit slice: strengthened reserved paths on case-insensitive systems,
strict/duplicate/collision manifest validation, object readback after writes,
mode-update inode check, stale-run mutation blocking and explicit late finalization.
Fixed optional diff positional IDs and single-document JSON warning behavior.
Tests include permission faults, nested Git marker, outside symlink, 2 MiB/150-file
workload, generated byte/mode roundtrips, SIGINT/SIGKILL, lingering-child conflict,
and actual CLI command coverage. Full `pytest -q`: 81 passed, 4 expected skips.
Ruff clean; mypy success (21 files). Last pushed SHA: 363c16f.
Next: M11 measured benchmark record and M12 CI/package/coverage/edge-matrix audit.

M11 complete within optional scope: real CLI demo, disposable measured benchmark
(200 x 4096-byte files on macOS arm64 / Python 3.12.14), reproducible actual Textual
screenshot from a wrapped synthetic Python command. Watch/export/import/compression
and extension APIs explicitly deferred with safety rationale in BENCHMARKS/DECISIONS.
Validation: demo asserts byte-correct undo/redo; benchmark measured successfully;
TUI headless tests: 3 passed, including edits/history changes during confirmation.
Visual screenshot inspected. `python -m build --no-isolation` builds wheel+sdist.
Last code commit: 21679f7; last pushed: 363c16f. Next: final CI/coverage/install audit.

M12 journal-integrity gate: versioned SHA-256 envelopes validate plan/progress
before recovery, verify and GC. Retained journal bytes are verified too; shared
object size contradictions are refused. Malformed legacy journals fail closed.
Validation: full `pytest -q`: 87 passed, 4 expected skips; Ruff/format clean;
mypy success (22 files); wheel/sdist build and content/license inspection pass;
real CLI demo passes. Current source still awaiting final CI commit/push.
Last prior commit: aefd165; last pushed: 363c16f. Next: CI matrix and clean-wheel
workflow, then remote verification and final delivery audit.

M9/M6 final audit follow-up: shorter readable UTC timeline cells, frozen modal
expectations and selected run identity tested across external edits/new runs.
Runner rejects non-main-thread use before creating metadata (signals need main).
Validation included in 87-pass full suite; headless TUI: 3 passed. Prior commit:
see journal-integrity commit. No destructive operation is enabled after stale
confirmation. Next: final packaging and remote CI.

M12 packaging/CI configured: macOS/Linux x Python 3.12/3.13/3.14, Ruff/format,
mypy, pytest+coverage, build, real demo and isolated wheel CLI install. Security,
contributing, changelog and explicit edge-case matrix added. MIT preserved.
Build backend added to dev dependencies for reproducible no-isolation checks.
Remote CI has not yet run; configuration alone is not a pass claim.
Push user authorization is explicit; first verified push ended at 363c16f.
Next: push final verified code, inspect all six remote jobs, fix any failures,
record final coverage/install/remote outcomes and deliver clean main.

M12 scope-policy closeout: status/doctor label tracked/untracked/ignored and
unclassified directories; doctor preserves diagnostics on unsupported scope;
configurable opaque-record/reject symlink policy refuses targets before mutation.
History exposes run sizes/integrity and parsed verified journals. Object quotas
are explicitly documented separately from metadata/staging disk space.
Validation: final broad audit before last policy guard was 90 passed, 4 skipped,
83% coverage (1599 statements/277 missed); focused final scope/E2E checks pass.
Ruff/format/mypy clean; rebuilt wheel and reinstalled demo pass. CI run
41102164521 remains queued with zero assigned runners, no remote success claim.
Next: record updated final full results, push scope closeout and delivery report.

Final staging fault audit: injected actual short writes, zero-progress writes and
ENOSPC at staged-file fsync. Short writes produce exact bytes; failures preserve
the untouched destination, FAILED journal and verified recovery checkpoint, and
explicit recovery clears the block. `pytest tests/safety/test_restore.py -q`:
13 passed. Last pushed source: 91a6caf; no engine changes in this test-only slice.


M12 remote gate complete: workflow 41103386128 success at 639548a. Six jobs
individually confirmed success, 94 passed/4 skipped each, 83% coverage. Final
record commit changes docs only. All feasible core milestones delivered; optional
M11 advanced features remain explicitly deferred. No unresolved execution blocker.

UX overhaul started from clean 6d28695. Audit/design contract: UX_OVERHAUL.md.
Shared safe Unicode/units/palette and metadata-paged UI read model implemented.
Navigation uses lazy immutable manifest cache, no source scanning. Unique ID
prefix resolution is explicit and rejects ambiguity. Focused tests: 2 passed;
Ruff/mypy clean. Next: responsive workspace and guided backend recovery dialogs.

UX workspace gate: dashboard, paged session/checkpoint/recovery timeline, filters,
keyboard help, light-theme toggle, responsive history/detail navigation, bounded
file/diff previews, search and semantic change labels implemented. All actions
use real backend data and frozen plans/run IDs. Corrupt selections disable restore.
Tests: `pytest tests/integration/test_tui.py -q`: 6 passed, including narrow/empty,
Unicode/search, changed files/history during confirmation and corrupt manifests.
Ruff and mypy pass. Next: CLI onboarding/presentation, visual inspection and QA.

CLI/onboarding gate: interactive readable views, explicit --human/--plain,
NO_COLOR support, grouped help, useful init scope/next steps, non-launching
quickstart, agent discovery, history filtering and unique checkpoint prefixes.
Redirected and explicit JSON structures remain unchanged. Focused CLI/read-model
checks: 10 passed; Ruff/mypy clean. Timeline now fetches headers in bounded batches,
not manifest BLOBs or one query per row. Next: visual QA/docs and edge-case tests.

Visual QA follow-up: inspected real dark dashboard, 70-column detail view and
undo-review modal. Reduced footer noise, improved border/diff contrast, exposed
mode/byte metadata and filename-based syntax highlighting. Snapshot fixture uses
a real wrapped Python command and explicitly selects a color-capable demo terminal;
the application still respects NO_COLOR. Focused UX tests: 10 passed. Next: branding,
README, wider usability/safety regression and measured navigation benchmark.
