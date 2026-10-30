# UX/UI overhaul delivery · 2026-10-31

Baseline: 6d28695. Implemented directly in the existing Python/Textual product.
The checkpoint, scan, object, metadata, project, runner, restore, operation,
retention, journal and Git engine are unchanged. No storage-format migration,
background agent, package publication, release or tag was introduced.

## What changed

| Before | Now |
| --- | --- |
| JSON everywhere in human workflows | Rich terminal views, useful init scope/exclusions/next step; redirected JSON unchanged |
| Flat checkpoint tables | Session-aware timeline with PRE/POST relationship, state/exit result, saved baseline and recovery entries |
| Raw JSON diff and restoration data | File indicators, unified diff, line numbers, syntax/file toggle, modes/bytes, bounded preview/search |
| No project overview | Project identity, saved-state availability, last session, file counts, storage and Git/recovery warnings |
| One wide-only layout | Desktop workspace, narrow history/detail flow, visible shortcuts, help, dark/light palettes |
| Generic recovery confirmation | Human review, Cancel default, explicit empty-session history steps, conflict next steps, verified completion/recovery data |
| Expensive history reads on navigation | Bounded metadata pages, no manifest BLOBs in header queries, synchronized eight-manifest cache |
| Sparse developer presentation | Original SVG identity, practical README, reproducible real screenshots and measured navigation fixture |

## Compatibility and safety

- --json always selects the existing JSON schemas/full IDs for existing commands.
  Non-TTY output retains the original JSON behavior. --human/--plain are opt-in
  readable overrides; NO_COLOR is respected. Run preserves terminal I/O/exit codes.
- Init adds --json; quickstart is read-only and has one-document JSON output.
  No command initializes, launches or checkpoints automatically in the background.
- Unique checkpoint prefixes resolve only when unambiguous (minimum four hex digits).
  History search filters the requested page; TUI search filters loaded entries.
- Live undo eligibility is checked on explicit preview, not claimed by the dashboard.
  Modal previews freeze the plan/run identity and cannot dispatch nested recovery.
  All mutations still use backend locks, conflict checks, journals and verification.
- Controls, bidi and markup are escaped/literal; readable Unicode is preserved.
  Excluded bytes and unsupported metadata remain outside the original protection scope.

## Verification

```sh
.venv/bin/pytest --cov=timemachine --cov-report=term-missing --cov-report=xml
.venv/bin/ruff check src tests examples
.venv/bin/ruff format --check src tests examples
.venv/bin/mypy
.venv/bin/python -m build --no-isolation
.venv/bin/python examples/demo.py
.venv/bin/python examples/ux_benchmark.py
```

Local Python 3.12.14 / macOS arm64: **110 passed, 4 skipped**, 114 collected;
**84%** statement coverage. Ruff/format clean (44 files); strict mypy clean
(24 source files). Existing safety tests: **37 passed**. TUI pilots: **10 passed**.
Skips: three unavailable optional agents and sandbox-stripped setuid; the direct
mode validator passes. CLI subprocess execution is tested but not included in
the pytest-process coverage figure. Final exclusion-copy adjustment: 5 CLI tests pass.

The clean wheel, including the real packaged stylesheet, ran both the disposable
CLI undo/redo demo and headless TUI screenshot. CI now repeats isolated wheel/demo/
TUI verification across macOS/Linux with Python 3.12–3.14. Remote result is recorded
below once observed; local results alone do not establish remote success.

Tested UX cases include narrow/empty views, typing without triggering shortcuts,
help/theme/navigation, filtering/search, binary/long/Unicode/link previews,
corrupt snapshots, frozen confirmation across user edits/new sessions, nested
shortcut refusal, noninteractive JSON behavior, executable discovery and conflicts.

## Real visual artifacts

- [Dashboard and unified diff](assets/tui.svg) / [PNG preview](assets/tui.png)
- [Recovery review](assets/recovery.svg)
- [Narrow details](assets/narrow.svg)
- [Light palette](assets/light.svg)
- [Previous interface](assets/tui-before.svg)
- [Original SVG wordmark](assets/wordmark.svg)

Generated with examples/tui_preview.py in a disposable project using a real wrapped
synthetic Python command; inspected dashboard, narrow, review, monochrome and
corrected light views. The screenshot script explicitly chooses a color-capable
terminal for the fixture; the application respects user color settings.

## Measured navigation

`examples/ux_benchmark.py`: 120 real checkpoints, 50-row page, one small file.
Prior history service: 50 manifest loads, 17.91 ms. New headers: 0 manifest loads,
0.56 ms. Twenty selections: 2 total manifest loads, 7.29 ms. Exact run and hardware
are in BENCHMARKS.md. These are single-run fixture measurements, not a general
startup/large-project speed guarantee or a usability-study result.

## Installation / first session

```sh
git clone https://github.com/muratkareem/timemachine.git
cd timemachine
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[tui]'
cd /path/to/your/project
timemachine init
timemachine agents
timemachine run -- codex
timemachine tui
# CLI alternative:
timemachine diff
timemachine undo --preview
timemachine undo
```

Use an existing checkout with `git pull --ff-only` and reinstall the TUI extra.
Initialization is setup only. Generic commands also work; each agent keeps its own
credentials and billing. No new hook APIs or automatic agent execution are claimed.

## Limits

Suggested minimum 60 columns x 24 lines; CLI/plain/JSON alternatives remain.
Text previews cap at 1 MiB before display, 2,000 displayed lines and 500 characters
per line, with truncation labelled; snapshots retain complete protected bytes.
History filtering searches the loaded/requested page; Load older expands it.
Current files may differ from saved checkpoints. External writers still create
unavoidable races; Git metadata, exclusions, hardlinks, unsupported metadata and
other original limits remain in SAFETY.md. No user study of one-minute comprehension
was performed. Advanced watch/export/import/compression remains deferred.

## Overhaul commits

```text
2d22fc3 feat: establish safe presentation system and lazy UI read model
be35bec feat: redesign Textual workspace with session history and guided recovery
7bb1011 feat: add readable CLI onboarding while preserving automation output
87e26bf fix: improve recovery preview contrast and contextual terminal controls
1f94ccc fix: harden UX edge states and bound history navigation work
6799ea6 docs: introduce original identity and real product walkthrough
d035975 fix: keep recovery review exclusive and search input free of side effects
7ece889 test: verify onboarding automation and packaged TUI installation

```

The final QA/evidence and remote-verification documentation commits follow this
ledger and are available in git log. No artificial or empty commits were used.

## Push / CI

Verified local work is being pushed to authorized origin/main after an ancestry
check. The remote six-job result will be recorded here when actually observed.


Final interaction audit: no-change sessions can explicitly advance undo/redo
history through the backend, without file writes or fabricated transactions.
The new pilot verifies this. Full local suite: 110 passed/4 skipped, 84% coverage
(2094 statements, 330 missed), 18.59 s. Final formatter wrap correction applied;
Ruff/format/mypy/build/installed-wheel demo and TUI smoke all pass.
