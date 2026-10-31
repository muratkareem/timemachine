# Production completion delivery · 2026-10-31

Starting point: clean main at **34b487b**, independently rerun as 110 passes / four
skips. Version remains **0.1.0**. MIT license/history preserved; no force push.
This report distinguishes implemented/verified capabilities from publication gates.


## Publication addendum · 2026-10-31

The maintainer explicitly authorized GitHub publication after reviewing the verified
commit/artifacts. [v0.1.0](https://github.com/muratkareem/timemachine/releases/tag/v0.1.0) is now published at
`e10c054ec38eb129dc985d0b521b1214c4e65b19` (2026-10-31 10:55:45 UTC).
The annotated tag was checked against that exact commit. All four approved files
were downloaded from the draft and again from the published release and matched
byte for byte. Installation from the public wheel URL and installed disposable
acceptance/TUI checks pass. No release asset or approved tag was replaced.

The preparation-time publication gate described below is resolved for GitHub.
PyPI remains unpublished pending verified ownership and credentials. Repository
metadata settings were not changed. The post-publication commit updates documentation
only; the released runtime and artifact provenance remain at the approved commit.

## Product delivered

SHA-256 deduplicated snapshots, PRE/POST inherited-terminal subprocess sessions,
conflict-safe undo/linear redo, full or file/directory-selective restore, retained
recovery checkpoints and explicit interrupted recovery. Git history/index are
observed, never repaired or rewritten. Binary content and POSIX metadata/link
targets are handled within the documented safety contract.

CLI: init, checkpoint, status, agents, integrate, run, history/list/show, diff,
undo/redo/restore, recover, doctor/verify, storage/gc/prune/delete/tag/pin, migrate,
quickstart, tui and --version. Existing redirected/explicit JSON contracts remain
stable. Human status counts actual complete checkpoints and unfinished sessions;
human run announces verified PRE before launch. Init is explicitly not a backup.

The Textual UI retains the completed design: saved-state dashboard, paged timeline,
file filtering, searchable numbered unified/file previews, syntax colors, metadata/
type changes, binary/large-file summaries, narrow details, keyboard help, dark/light
palettes, cancel-first reviews and backend-revalidated intent. Real screenshots
were regenerated and visually inspected in dark/light/70-column layouts. Tests
exercise narrow/empty/Unicode/search, conflicts, corrupt selections and modal races.
No new redesign, fake production data or background service was introduced.

Supported agents: ordinary installed Codex, Claude Code, Gemini CLI, Aider, or any
custom argv command through `run -- COMMAND`. Opt-in Bash/Zsh functions preserve
the same process wrapper with absolute executable paths. Both shells are tested
with synthetic agents, quotes, cwd, stdin/environment, nonzero exit and redaction.
Local Codex --help transport is tested; no authenticated/billed model session is
claimed. Claude/Gemini/Aider were absent locally. Official lifecycle APIs were
investigated; vendor-hook adapters are deferred for precise shutdown/durability
semantics. Sources and limits are in INTEGRATIONS.md.

## Architecture, audit and fixes

- Freeze the exact CLI undo/redo/recover plan and selected run through confirmation;
  retain observations for already-target paths and revalidate even no-op intent.
  Three adversarial cases failed before the fix. Git/root/ancestor/parent descriptor
  context changes now fail safely without adding unreviewed writes.
- Bounded no-follow configuration/identity reads reject bad shapes/duplicate keys.
  Private real store directories and non-hardlinked catalog entries are required.
  SQLite integrity, foreign keys, checkpoint states, references, tags/pins and run
  ordering are validated before interpreting garbage-collection authority.
- Capture inventories quota once per locked store, verifies duplicate blobs without
  rewriting, rehashes new bytes while copying and bounds/nonblocks preview reads.
  A 1,000-object profile reduced inventory walks from 1,000 to one (2.054→0.206 s).
- Catalog **v2** uses indexed append-only checksummed/chained journal steps with an
  atomically updated small head. Legacy v1 manifests/journals stay readable. Explicit
  transactional migration saves a private catalog-only backup and refuses writes
  until applied; injected migration failure rolls back. Missing/reordered progress
  blocks verify/recovery/GC. Catalog-only backups do not independently retain blobs.
- Unsupported platforms fail before POSIX services import. Native Windows remains
  unvalidated; no POSIX checks were weakened. Hunk-level recovery is deferred rather
  than using ambiguous/blind patches.

The core stays independent of CLI/TUI; no new service/framework/storage technology.
Same-user malicious processes and uncooperative external writers remain outside
absolute guarantees. No global multi-file atomicity, ACL/xattr/time/ownership backup,
network-filesystem durability, sandbox or independent certification is claimed.
Full findings and threat limits: PRODUCTION_AUDIT.md, SAFETY.md, RECOVERY.md.

## Verification

Final runtime/test local gate: **139 passed, four skipped, zero failed**, 27.33 s;
**85% statement coverage** (2,370 statements / 359 missed). Critical restore engine
coverage 93%, restore planning 98%, object store 93%, scanner 92%, journal 89%.
The four local skips are three unavailable vendor executables and host-stripped
setuid bits (pure validation is tested). 29 tests were added beyond the baseline.
All mutation/fault experiments use disposable projects and external temporary stores.

Ruff/check/format: 56 files. Strict mypy: 26 source files. Both pass. Wheel/sdist,
Twine metadata checks, clean tool installs, packaged stylesheet and headless TUI
pass. Double builds from independent clean git archives have matching hashes.
Release scripts create a build manifest/checksums and never publish.

Remote [CI at 685291c](https://github.com/muratkareem/timemachine/actions/runs/41192391040)
passed **all seven jobs**: macOS/Linux × Python 3.12/3.13/3.14 plus reproducible
release candidate build/upload. The macOS 3.12 job reports 139 passes/four skips;
Ubuntu 3.12 reports 138/five (Zsh and four vendor executables absent).
The first production run exposed a PTY test harness wait-before-drain deadlock on
macOS. It was corrected and strengthened with 16 KiB of output; all jobs then passed.
No runtime timeout or security checks were relaxed. The complete delivery at c95659a also passed all seven jobs in
[final CI 41193462517](https://github.com/muratkareem/timemachine/actions/runs/41193462517).
Its independently built Linux CI wheel/sdist hashes match the local macOS artifacts.
Both final wheel and sdist pass clean installed acceptance; a CLI-only wheel runs
without Textual/test dependencies and gives actionable optional-extra guidance.

## Acceptance scenarios

| Scenario | Executed evidence |
| --- | --- |
| 1 Normal session | Actual CLI init/run/history/diff/preview/undo/redo with original/changed byte assertions |
| 2 Unrelated user edits | Manual unrelated file survives Undo in plain and Git fixtures |
| 3 Conflicting edits | Newer edit to touched file refuses Undo and remains byte-identical |
| 4 Git project | Committed/staged/unstaged/ignored/untracked content; Git context/index invariants unchanged |
| 5 Interrupted restore | Injected disk exhaustion after a write; FAILED journal/recovery retained; explicit recover and integrity pass |
| 6 Installation | Wheel + archive installs via isolated uv/pipx; installed CLI/TUI/resources; native Homebrew build/test |
| 7 Large project | 100/1,000/10,000/50,000 files, binary/deep trees, unchanged capture, diff/undo/redo/verify/GC; repeated recovery/history |
| 8 First-time workflow | Quickstart does not initialize, init creates no checkpoint, README synthetic session/inspection/recovery executes |

Reproduce 1–5/8 and installed TUI with `python scripts/acceptance.py`. Run it with
the installed tool interpreter, not a source-path override. Scale is a separate
bounded opt-in script. Automated workflow verification is not a measured user study
or proof that all users understand the tool in one minute.

## Performance observations

Local APFS / macOS 26.7.1 arm64 / Python 3.12.14, one run per size, warm caches
possible. At 50,000 files plus an 8 MiB binary/depth-20 tree: fresh 13.672 s,
unchanged 5.359 s, diff 0.291 s, ten-path Undo 9.100 s, Redo 9.113 s, verify 1.911 s,
GC dry-run 3.738 s, history headers 4.35 ms, process peak RSS 164 MiB. Unchanged
checkpoints add zero object bytes; catalog/history metadata still grows.
A 64 MiB binary/1,000-changed-path fixture completes three Undo/Redo round trips
in 1.87–1.98 s each direction; peak RSS 107 MiB includes fixture generation.
A 1,000-checkpoint one-file history returns fifty headers in 0.51 ms without
manifest loads. Workload boundaries, raw JSON and reproduction: BENCHMARKS.md.

## Distribution, release and remaining gates

No clone required: verified uv tool and pipx installs from pinned public runtime
commit **9ae8c4d07ef4acbdbe2c87220a0d562276810b16**. See INSTALL.md. The complete
documentation/test/formula delivery uses later commits; production Python sources
and dependencies are unchanged from that installed runtime commit.

Homebrew: pinned formula and 20 wheel resources, native macOS arm64 build,
`brew test`, installed acceptance and TUI pass. Validation used a uniquely named
temporary tap/formula, subsequently removed; public explicit tap instructions use
this pushed repository. Homebrew installed ordinary Python/OpenSSL/SQLite
dependency updates while validating. No Intel/Linux brew or bottle claim.

Release artifacts: version 0.1.0 wheel, sdist, SHA256SUMS and BUILD.json, rebuilt
from the final clean commit. Build tools are pinned; dependencies/licenses are
inventoried in DEPENDENCIES.md. Notes: releases/v0.1.0.md; procedure: RELEASE.md.
No known unresolved critical data-loss defect remains within the stated contract.

**GitHub tag/Release:** prepared, not published; requires explicit maintainer
authorization in addition to the existing origin/main push permission.
**PyPI:** not published. `timemachine` is unrelated; `timemachine-cli` lookup was
404, not proof of ownership. Upload credentials/verified ownership are unavailable.
**Repository settings:** proposed description/topics are prepared in RELEASE.md;
no separate settings authorization or change is claimed. Templates are committed.

Optional future work: native Windows with real runner validation, strongly
conflict-checked hunk recovery, vendor lifecycle adapters, watch/export/compression,
broader platform/performance measurements and user studies. None is represented as
implemented. Source push/CI/build status and final commit are verified at closeout.

## Screenshots and demonstration

Real [dashboard](assets/tui.svg), [light](assets/light.svg),
[narrow](assets/narrow.svg), [review](assets/recovery.svg).
Regenerate with `python examples/tui_preview.py --output /tmp/timemachine.svg`.
The production rendering was inspected again with the new backend. Real scripted
CLI output: `asciinema play docs/assets/demo.cast`; regenerate using
`python scripts/record_demo.py --output /tmp/timemachine-demo.cast`. It runs only
a public synthetic temporary fixture and asserts Undo/Redo bytes.

## Historical continuation prompt (GitHub publication now completed)

“Continue TimeMachine at the clean pushed final production commit. Verify origin/main
and all seven CI jobs. Rebuild with pinned release tools using scripts/build_release.py,
verify checksums/Twine and installed acceptance. I authorize publishing the v0.1.0
tag and GitHub Release at that verified commit using those exact artifacts and
docs/releases/v0.1.0.md. Do not replace an existing tag/release or force-push. Confirm
downloaded asset hashes after publication. PyPI remains blocked until I establish
timemachine-cli ownership and provide an authorized trusted publisher or scoped
credential; do not print secrets or guess ownership. Preserve the existing safety
contract and do not add deferred features.”
