# Delivery and verification

Repository: https://github.com/muratkareem/timemachine
Branch: main. Preserved initial commit c32d009 and unchanged MIT LICENSE.
User explicitly authorized direct verified pushes; implementation pushed through
91a6caf (runtime), with final staging tests at 8d1f50f. Final documentation commits may follow without changing tested code.
No version tag, public release or PyPI publication was created.

## Milestones

- M0: architecture, scope, threat model, format, conflict/journal/recovery contract.
- M1: installable Python 3.12+ package, Typer/Rich CLI, config, init/discovery/lock.
- M2: no-follow scanner, SHA-256 objects, dedup, stable double-scan checkpoints,
  INCOMPLETE lifecycle, limits/quota, integrity verification and Git observations.
- M3: list/show/inspect/history/status/doctor, exact content/type/mode diffs,
  binary/non-UTF-8 summaries and terminal-safe text/JSON output.
- M4: immutable restore plans, recovery snapshots, checksummed durable journals,
  atomic per-file staging, revalidation, verification and explicit partial recovery.
- M6 then M7: real subprocess wrapper with terminal/env/cwd/signal/exit behavior,
  durable PRE/POST, crash detection/late POST; Git/non-Git MVP gate passed.
- M5: linear redo/invalidation, selective/full restore, path boundaries and rebind.
- M8: storage stats, verify, pin/tag/delete, conservative prune and reference-safe GC.
- M9: real optional Textual history/file browser, diff/preview, progress, keyboard
  controls and confirmed frozen-intent restore/undo/redo; visual inspection done.
- M10: generic wrappers and capability detection; installed Codex --help verified;
  absent Claude/Gemini/Aider explicitly untested locally, no invented hooks.
- M11: disposable measured benchmark, CLI demo and reproducible real TUI screenshot.
  Optional watch/export/import/compression/plugin APIs deliberately deferred.
- M12: local full suite, coverage, lint/type/format checks, wheel/sdist build,
  clean install/demo, security/edge-case/docs audit and configured six-job CI.

## Exact local checks on final implementation

Environment: macOS 26.7.1 arm64; CPython 3.12.14. Commands run from repository:

```sh
.venv/bin/pytest --cov=timemachine --cov-report=term-missing --cov-report=xml
.venv/bin/ruff check src tests examples
.venv/bin/ruff format --check src tests examples
.venv/bin/mypy
.venv/bin/python -m build --no-isolation
.venv/bin/python examples/demo.py
.venv/bin/python examples/benchmark.py --files 200 --bytes 4096
.venv/bin/python examples/tui_preview.py --output /private/tmp/timemachine-tui.svg
```

- pytest: **94 passed, 4 skipped**, 98 collected, no failures, 11.50 seconds in
  the final coverage run. Coverage: **83%** (1,606 statements, 277 missed).
- Skips: Claude/Gemini/Aider executables absent; sandbox filesystem strips setuid.
  Direct special-mode rejection validator passes. Hypothesis exercises 15 generated
  byte/mode roundtrips in addition to the parametrized cases.
- CLI subprocess E2E tests run but their statements are not included in the
  pytest-process coverage figure. Coverage is not a claim of exhaustive safety.
- Ruff: clean; format: 39 files formatted; mypy: success, 22 source files.
- Build: wheel and source distribution succeeded. Inspected wheel module/license
  inclusion and source archive safety tests/security policy. Initial no-isolation
  build exposed missing build backend; hatchling was added to dev dependencies.
- Fresh `/private/tmp/timemachine-wheel-final` virtualenv installed the final wheel
  offline from the local dependency cache. Its Python ran examples/demo.py,
  exercising installed CLI PRE/POST/diff/undo/redo/verify with byte assertions.
- LICENSE diff from initial commit empty; Git working tree clean after commits.
- Benchmark results and workload/hardware details: BENCHMARKS.md.
- Real Textual screenshot: assets/tui.svg; generated entirely in a temp project.

## Remote CI

[Latest runtime audit run](https://github.com/muratkareem/timemachine/actions/runs/41103060048)
for 91a6caf is **queued**, with all six jobs awaiting runner assignment when last
checked. [Previous run](https://github.com/muratkareem/timemachine/actions/runs/41102164521)
for 5da4e1b likewise had no started jobs after several minutes. No remote pass or
cross-platform verification is claimed. The matrix is macOS/Linux x Python
3.12/3.13/3.14. GitHub runner assignment is an external verification dependency;
there is no repository test failure to diagnose yet. Final test/documentation
pushes may create additional queued runs. The exact latest state is visible in
[GitHub Actions](https://github.com/muratkareem/timemachine/actions).

## Commit ledger

```text
19b11d3 docs: define storage architecture and recovery safety contract
11c457b feat: add installable CLI and private project storage foundations
6e5a8fb feat: capture durable verified filesystem checkpoints
7947bb0 feat: expose checkpoint history and terminal-safe exact diffs
2d868eb feat: implement journaled conflict-safe undo and explicit recovery
9969904 feat: wrap real agent processes with durable pre and post checkpoints
7c007dc test: verify full MVP recovery and Git preservation end to end
837e01c feat: add linear redo and selective checkpoint restore
6171305 feat: add conservative retention and reference-safe garbage collection
e32f5f6 feat: add real Textual history browser and confirmed recovery actions
363c16f feat: detect agent capabilities and document verified generic wrappers
21679f7 fix: harden recovery boundaries and cover interrupted session edge cases
aefd165 test: add reproducible recovery demo and measured local benchmark
1e7b883 fix: verify checksummed recovery journals before trusting recorded states
4a1e0e3 fix: preserve confirmed TUI intent when files or run history change
5da4e1b ci: audit supported Python platforms and verify build and clean installation
91a6caf feat: expose exact protection categories and configurable symlink policy
8d1f50f test: exercise partial writes and disk exhaustion during restore staging

```

Later audit/documentation commits are discoverable with `git log`; this ledger
identifies the implementation history through CI configuration.

## Installation and use

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[tui]'
cd /path/to/project
timemachine init
timemachine run -- codex
timemachine diff
timemachine undo --preview
timemachine undo --yes
timemachine redo --yes
timemachine tui
```

## Limits and next priorities

See SAFETY.md, RECOVERY.md and EDGE_CASES.md. No universal backup or sandbox;
no Git history/index repair; no ACL/xattr/ownership/timestamp/sparse/hardlink
relationship restoration; hardlinks/special files rejected. Exclusions are explicit
and not recoverable. External concurrent writes retain unavoidable TOCTOU windows;
no global multi-file atomicity. Corrupt data requires a whole-store backup/manual
repair. Uncatchable kills may leave stage files that must be inspected manually.
Legacy unchecked development journals fail closed. Network filesystem/Windows
support is not claimed. Journal/run references are retained conservatively and
may require additional storage rather than automatic destructive pruning.

Next priorities: observe and resolve the queued CI matrix first, then independent adversarial filesystem review, explicit future format
migration tooling, broader scale benchmarks, then separately tested optional
watch/export/import and additional real-agent/platform coverage. No hidden stub
features or published-package claims. No remaining human approval or credentials are required for local use. Remote
verification is pending external runner availability; its underlying cause is not
established, and no account/billing diagnosis is asserted.
