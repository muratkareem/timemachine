# Launch preparation — 2026-11-03

README quickstart, installed-wheel dashboard/conflict captures, a 54-second
actual CLI video, reproducible demo tooling, storyboard and English publication
drafts are prepared. The committed demo includes a live edit by the current Codex
agent during a coordinated wrapper command. Full pytest: 173 passed, 3 documented
skips; Ruff/format/mypy and installed-wheel recovery acceptance passed. No new
build was run (the user requested preserving the already published product).
Release tag and asset digests are preserved. Discoverability metadata configured;
social preview uploaded and verified in GitHub settings. Posts remain unpublished.
Details and commands: [launch verification](launch/VERIFICATION.md).

---

# v0.2.0 published — 2026-11-02

[GitHub Release v0.2.0](https://github.com/muratkareem/timemachine/releases/tag/v0.2.0)
is public. PR #1 merged with history preserved. Annotated tag v0.2.0 resolves to
5373901539c6d1748256263d76102f7b36f94fd3. All seven release-commit CI jobs pass
(run 41420598910). Fresh local suite: 173 passed, 3 documented skips, 86% coverage.
Clean double builds, Twine and isolated wheel/sdist recovery acceptance pass;
all four uploaded assets match verified originals. Public install: INSTALL.md.
The original v0.1.0 release is unchanged. No PyPI upload was performed.

Release resume verification confirmed both the tagged release and the subsequent
main documentation commit (8dbddd7); all seven jobs passed for each. A fresh tool
install from the public v0.2.0 wheel URL reports version 0.2.0 and passes disposable
init/session/diff/undo/redo, conflict, Git and recovery acceptance. Downloaded assets
match GitHub digests, SHA256SUMS and BUILD.json. Current user-facing changelog and
UI/release guides now consistently describe v0.2.0 as published. These documentation
corrections do not change the tagged commit or its assets.

## Historical preparation record

# Final product pass — 2026-11-02

Simple mode is now the default; Advanced preserves the existing workspace.
Nine additional automated cases cover six sizes, mode switching without writes,
keyboard/mouse/help, undo/redo/cancel/conflicts and changed files after confirmation.
No backend/CLI/formats/dependencies changed. Source acceptance and fresh 10,000-file
stress passed. Final local gate: 173 passed, 3 skips, 86% coverage; Ruff/format/mypy pass.
Package/CI handoff evidence is recorded in PR #1 and PRODUCT_DELIVERY.md. No merge/publication is authorized.

---

# Current status — v0.2.0 pixel release candidate delivered

Candidate **0.2.0** is prepared on **codex/pixel-tui-v0.2.0** with
[review PR #1](https://github.com/muratkareem/timemachine/pull/1), not merged/published.
30 cohesive implementation/evidence commits from ca9646f include the final installed
gallery and documentation closeout. main and the published v0.1.0 release remain unchanged.

Final local gate: **164 passed, 3 documented skips, 86% coverage** (2728 statements,
375 missed), 42.18 s. Ruff lint/format: 68 files; strict mypy: 29 source files; all
pass. Both seven-job branch/PR CI runs at 4c3eada pass (41328985700 / 41329081554).
Both branch/PR seven-job gates also pass at 5bc9dd8 (41329744412 / 41329748618).
The final gallery/docs closeout changes no runtime/tests/dependencies/CI; head checks are on PR #1.

Wheel/sdist clean double builds, Twine checks, isolated installs and installed
acceptance/gallery pass. Linux CI and macOS artifact hashes match. No-clone pinned
candidate source installation passes. Nineteen actual captures cover both palettes,
six sizes, undo/redo/full restore/conflict/empty and narrow review. The 60x24 inspector
has additional code space while retaining project identity and recovery controls.

Native Windows/hunk restore/vendor hooks remain deferred. UI previews, file pages
and reviews have explicit bounds; no unsafe fallback. Original restore/snapshot/
storage/Git engines are unchanged; the shared eligible-run query is identical.
Release ID/tag target and all four v0.1.0 asset IDs/sizes/digests are unchanged.
PyPI remains unpublished. No new tag/release approval is requested or assumed.

Verdict **RELEASE CANDIDATE · 89/100**. Full scores, test evidence, measured
performance, screenshots, installation and limitations: PIXEL_DELIVERY.md.

---

## Historical implementation record

# Current status — v0.2.0 pixel workspace in verification

Development branch: codex/pixel-tui-v0.2.0; baseline 7b3a548. v0.1.0 tag/asset
identities recorded; the published release is not modified. New candidate version
0.2.0 is local/unpublished. No v0.2.0 tag or release will be created without approval.

Implemented: original save-state palette/hourglass and pixel frames; broader archive
and file inventory; bounded diff stage/ledger; backend-derived Undo/Redo candidates;
file/path recovery; Cancel-first bounded reviews; six responsive layouts; Unicode
path search and 200-row file pages; stable archive cursors; nonblocking read workers;
no-I/O theme repaint; ASCII/no-color/reduced-motion support.

Fresh baseline 140 passed/3 skips. First full visual gate: 161 passed/3 skips,
86% coverage. Subsequent file-filter/layout focused gate: 19 passed. A no-I/O theme
regression exposed a queued selection race; cell repaint and worker handling were
corrected and the tests pass. Existing test assertions remain, with explicit waits
for the new asynchronous read workers. Core restore/storage/Git formats unchanged;
only the identical backend candidate query is shared with the read model.

Published v0.1.0 wheel reinstalled and disposable acceptance passes. Nineteen actual
Textual captures cover six sizes/two palettes plus recovery/conflict/empty states;
visual inspection found and corrected cached widths and overlarge dialogs. Final
captures and comprehensive gate are pending. No billable agent calls.

Next: measured UI comparison against published v0.1.0, final gallery/branding/docs,
full tests/build/clean install, branch push + review PR and remote seven-job CI.

---

## Previous release record

# Current status — v0.1.0 published

[GitHub Release v0.1.0](https://github.com/muratkareem/timemachine/releases/tag/v0.1.0) was published on 2026-10-31 at 10:55:45 UTC,
following explicit maintainer approval. Annotated tag `v0.1.0` resolves to the
approved commit **e10c054ec38eb129dc985d0b521b1214c4e65b19**. The four approved
artifacts (wheel, sdist, SHA256SUMS, BUILD.json) were verified in draft, then downloaded
again after publication and matched byte for byte. Their build provenance is unchanged.

Installation from the public release wheel with uv succeeds; installed disposable
acceptance including recovery, Git invariants and packaged TUI passes. The release
commit's [seven-job CI](https://github.com/muratkareem/timemachine/actions/runs/41193647489)
is green. Previously measured local suite: 139 passed, four skips, 85% coverage.
This post-publication documentation update changes no runtime/tests/dependencies/CI
and does not move the release tag or replace any asset. Existing push approval applies.

PyPI is **not published**: verified package ownership and authorized credentials are
still unavailable. Native Windows, hunk recovery and vendor-hook adapters stay deferred.
No further GitHub release approval is pending. See INSTALL.md and PRODUCTION_DELIVERY.md.

---

## Historical preparation record

# Current status — production release candidate prepared

Version **0.1.0**, supported Python **3.12–3.14** on **macOS/Linux local filesystems**.
Production runtime is committed through **9ae8c4d**; final acceptance/CI changes at
**685291c** passed all seven remote jobs in workflow **41192391040**. All six test
matrix jobs succeeded plus the reproducible candidate artifact job. Last local
full suite: **139 passed, 4 skipped**, **85% statement coverage** (2370/359 missed),
27.33 s. Ruff/format pass (56 files); strict mypy passes (26 source files).

Exact-reviewed recovery, catalog authority/GC checks, explicit v1→v2 catalog
migration and chained append-only journals are implemented and adversarially tested.
Objects/manifests stay compatible. Measured scale includes 50,000 files, deep trees,
64 MiB binaries, repeated 1,000-path undo/redo and 1,000 saved checkpoints.

No-clone public-archive and wheel installations pass uv/pipx isolation, actual CLI
acceptance and packaged TUI checks. Homebrew pinned formula build/test and installed
acceptance/TUI pass on macOS arm64. Dark/light/narrow screenshots were regenerated
and inspected; the current interface is preserved. A real scripted CLI recording
is committed. No snapshots or user secrets were uploaded.

Release candidates build twice with matching hashes. The complete delivery at **c95659a** passed the final seven-job CI gate
**41193462517**. Final wheel/sdist installs pass in separate clean environments;
the CLI-only wheel passes without Textual/development tools. Linux CI artifacts
and local macOS artifacts have identical hashes. Source/formula/notes are pushed;
the documentation closeout preserves runtime/tests/dependencies/CI. Push to origin/main is authorized. Publishing the tag/GitHub Release remains a separate
maintainer approval; PyPI also lacks verified ownership/credentials. No publication
is claimed. Native Windows, hunk recovery and vendor-hook adapters are deferred.
See PRODUCTION_DELIVERY.md, PRODUCTION_AUDIT.md, BENCHMARKS.md and RELEASE.md.

---

## Historical record (the summaries below describe earlier gates)

# Current status — UX/UI overhaul complete

All eight UX phases delivered. Final tested implementation: **8d1b479** on
**origin/main**. Local and six-job remote gate PASS: **110 passed, 4 skipped**,
**84% coverage**. CI workflow **41125851544** is successful on macOS/Linux with
Python 3.12/3.13/3.14. Ruff/format/mypy/build, real CLI demo and clean installed
wheel/TUI export pass. Ten TUI pilots and the original 37 safety tests pass.

Recovery/storage/Git engine files are unchanged from baseline **6d28695**.
Terminal/redirected JSON compatibility, recovery confirmation and frozen plans
remain enforced. Final formatter correction is included in the successful run.
No unresolved blocker or outstanding approval. No publication/release/tag.

Evidence, exact commands, commit ledger, before/after, real screenshots, workload
measurements, installation and limits: **UX_DELIVERY.md** and **UX_CI.md**.
Final closeout commit is docs-only; tested source/tests/dependencies/CI unchanged.
Push authorization persists; final documentation is pushed without force and the
working tree is verified clean. Next work is optional user research, broader
scale measurement and the already-deferred advanced features, not unfinished UX.

---

## Historical implementation record (superseded by the summary above)

# UX/UI overhaul — final local gate

All eight phases implemented. Current full suite: **110 passed, 4 skipped**,
114 collected, **84% coverage** (2094 statements/330 missed), 18.59 s. Ten TUI
pilots pass. Ruff/format clean (44 files), mypy clean (24 files), wheel/sdist
build, clean-wheel CLI demo and real packaged TUI smoke pass. Existing safety
suite: 37 passed. Core recovery/storage/Git engine matches baseline 6d28695.

Overhaul pushed through ece12c5. The final dialog copy required one formatter
wrap correction; corrected in the next verified commit. Earlier overhaul run
41125302957 completed successfully for e3b46b5. Final correction matrix pending;
do not infer its success from the earlier result. Next: push final formatting/
evidence update and verify all six jobs. No outstanding human approval request.
Details/screenshots/installation/limits: UX_DELIVERY.md.

---

# UX/UI overhaul — current status

All eight implementation phases delivered locally. Full gate: 109 passed,
4 documented skips, 84% coverage; Ruff/format/mypy/build and installed-wheel
CLI/TUI checks pass. Core recovery/storage/Git engine unchanged from 6d28695.
Nine TUI pilots cover narrow/empty/search/conflicts/frozen modal/corruption states.
Design, compatibility, screenshots, workload metrics, limits and installation:
UX_OVERHAUL.md and UX_DELIVERY.md.

Last prior code commit: 7ece889; final empty-selection/onboarding-copy polish and
this evidence are committed at the local QA boundary. Next: push verified work
without force using existing explicit origin/main authorization, inspect all six
CI matrix results, fix real failures, then record final SHA/result. No new
permission request is needed. No publication/tag is authorized or attempted.

---

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

UX edge gate: conflict guidance preserves newer edits, binary/long/Unicode/link
previews are bounded and no-follow, ambiguous prefixes refuse, metadata pagination
works and immutable cache access is synchronized. Latest incomplete checkpoints
and interrupted sessions are visibly distinguished. Focused tests: 12 passed;
Ruff/mypy clean. Optional TUI minimum pinned to the verified Textual 6.12 API.

Brand/docs gate: original SVG wordmark, concise practical README, real dark/narrow/
review screenshots, CLI compatibility/help/keys and troubleshooting documented.
Measured 120-checkpoint fixture: header page loads 0 manifests versus previous
history's 50; 20 selections load 2 cached manifests total. Exact timings/workload
in BENCHMARKS.md. Single local run, no general performance or user-study claim.
Before final light-palette correction: full suite 107 passed, 4 documented skips,
84% coverage. Corrected light contrast and refresh; focused UX tests 12 passed.
Next: final full regression/build/clean-install and verified GitHub push/CI.

Final interaction correction: keyboard input in search does not dispatch actions;
modal recovery blocks background recovery shortcuts, preserving one reviewed intent.
Display limits apply after control escaping. TUI pilots: 9 passed; Ruff/mypy clean.
Light palette has separate high-contrast semantic colors and re-renders previews.
Next: full final gate, package TUI smoke and remote CI.

Packaging/automation gate: clean installed wheel includes the TUI stylesheet and
runs the real CLI demo plus headless workspace. CI now exercises that isolated
wheel/TUI workflow on every platform. Quickstart --json emits one document and
never initializes or executes an agent. Focused CLI tests: 5 passed. Full prior
final gate: 108 passed/4 skips, 84% coverage, Ruff/format/mypy/build/demo clean.

UX final local gate: 109 passed, 4 skips, 84% statement coverage (2090 statements,
331 missed), 17.88 s. Ruff/format clean (44 files), mypy clean (24 files), wheel+
sdist builds and real CLI demo pass. Isolated wheel includes CSS, runs CLI demo
and headless TUI. All recovery/storage/Git engine files match 6d28695 exactly.
Final onboarding explicitly shows exclusion policy, including absent dependency
folders (not only exclusions currently found). Focused CLI regression: 5 passed.

CI-time interaction audit found a no-change session blocked TUI history advancement.
Corrected through the existing backend: explicit "Confirm history step" for empty
undo/redo, with no file writes or manufactured restore journal. Empty checkpoint
restore stays disabled. TUI pilots: 10 passed; Ruff/mypy clean. Next: verify this
last correction in the full platform matrix, then final documentation record.

Production completion audit at 34b487b: fresh baseline 110 passed/4 skips.
Confirmed three consent/context regressions with failing adversarial tests;
fixed frozen intent for CLI undo/redo/recover, already-target revalidation, Git
and path identity observations, and opened-parent validation. Focused safety:
18 passed; earlier expanded safety/redo/TUI gate 59 passed; Ruff/mypy clean.
Next: malformed metadata/configuration and GC integrity, then scale/distribution.

Production metadata gate: bounded/no-follow config reads, private store checks,
strict catalog/foreign-key/order health validation before GC; malformed metadata
fails with actionable errors. 26 focused tests passed; Ruff/mypy clean. PyPI public
API: timemachine exists (unrelated owner); timemachine-cli and timemachine-agent
return 404. That does not prove name ownership/reservation. No publishing-token
variables are present. Next: measured object-store scaling and snapshot reuse.

Object capture now hashes first and avoids temporary writes for verified duplicate
objects; new objects are rehashed while copying and validated after fsync. Blob
reads are nonblocking for special-entry refusal and UI reads have an explicit
byte bound. Focused snapshot/object/staging tests: 28 passed, 1 expected skip.
Next: append-only journal scaling with explicit compatible catalog migration,
then measured 100/1000/10000/50000-file workloads and release packaging.

Production journal gate: catalog v2 uses chained append-only step records and an
atomically updated head. Legacy catalog v1 remains readable; explicit migration
adds tables/indexes transactionally, preserves objects and takes a private catalog
backup. Failed DDL rolls back; missing/reordered steps block GC/recovery. Recovery
uses indexed path sets instead of quadratic progress scans. Focused migration +
safety: 56 passed. Ruff/mypy clean. Next: full scale measurements and distribution.

Agent opt-in gate: reviewable Bash/Zsh functions wrap explicitly resolved agent
executables; no shell/vendor startup configuration is edited. Synthetic transport
tests cover quoting, cwd, stdin/environment, nonzero exit and redaction. Human
sessions show verified PRE before launch; human status reports complete checkpoints
and unfinished sessions without changing status JSON. CLI --version/module entry
and an early unsupported-platform gate are added. Focused gate: 13 passed, plus
runner regression 9 passed in the preceding combined run. Windows is not validated.

Production scale/full regression gate: 139 passed, 4 documented skips, 85% statement
coverage (2370 statements/359 missed). MacOS local 100/1000/10000/50000-file captures,
unchanged dedup, wrapped edits, undo/redo, verify and GC passed. Separate 64 MiB
binary/1000-path/three-roundtrip restore and 1000-checkpoint navigation passed.
Exact workloads/raw JSON in BENCHMARKS.md. Next: reproducible builds, clean tool
installation, staged Homebrew validation, final acceptance and remote CI.

Distribution/acceptance gate: no-clone pinned public archive installs pass with uv
and pipx; isolated wheel installs pass both tools, CLI demo and packaged TUI. Twine
metadata checks pass wheel/sdist. The pinned Homebrew formula built from source;
brew test, installed acceptance and headless TUI pass on macOS arm64/Python 3.12.16.
Temporary validation formula/tap is removed after checks; Homebrew installed normal
Python/OpenSSL/SQLite dependency updates during the test. CI 685291c: all six test
matrix jobs plus double-build/release-artifact job passed, run 41192391040.
Native Windows and optional hunk/vendor-hook integrations remain explicitly deferred.

Final production gate: c95659a is clean and pushed; CI run 41193462517 succeeded
with all seven jobs. Final wheel and sdist acceptance pass; CLI-only wheel has no
Textual/test dependency and gives actionable missing-extra guidance. Reproduced
macOS artifacts match the downloaded Linux CI wheel/sdist hashes. Homebrew validation
tap/formula is removed. Publishing v0.1.0 remains the only pending authorization;
PyPI additionally requires verified ownership/credentials. No tag/release exists.
