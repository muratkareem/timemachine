# v0.2.0 pixel workspace delivery · 2026-11-01

**Verdict: RELEASE CANDIDATE · 89/100**, with verified local/package and remote gates below.
These scores are engineering/design judgments supported by the stated fixtures and
limits, not independent certification, a user study or measured perfection.

## What changed

An original pixel hourglass, save-state slots, double frames and coordinated dark/
light themes replace the previous fixed three-column dashboard. The archive and
inventory now have equal width above a separate bounded diff stage. Wide screens
add a factual ledger; 24-line screens use a compact project header, and 60/80-column
screens offer 1/2/3 pane navigation. Paths/sizes/state are readable, with Unicode
filtering and 200-row file pages. Manual saves, pinned saves, run PRE/POST,
applied/undone/interrupted/invalidated states and recovery safeguards are explicit.

Primary Undo/Redo follows the backend's eligible session, including Redo when an
older applied session still exists. A candidate is reviewable, not a safety verdict.
Live validation creates the frozen plan under the lock; consent retains that plan
and run identity. Selected-path recovery is available through s; r reviews the full
selected save. Cancel is focused by default. Recovery paths fold without ellipsis;
reviews above 500 entries disable Apply and refer to CLI --preview. Corruption and
failed refreshes clear stale controls. Modal guards protect keyboard and queued
background actions. No unsafe override or automatic restore was introduced.

Snapshot, restore, journal, retention, Git and runner engines/formats are preserved.
The sole core refactor shares the identical eligible-run SQL query with UI readers.
Manifest v1/catalog v2 and CLI JSON contracts remain. No migration is needed from
v0.1.0; legacy v1 catalog migration keeps its existing explicit gate. Version advances
to 0.2.0. v0.1.0 release/tag/assets are read-only throughout this work.

## Visual quality scores

| Area | /100 | Evidence / practical limit |
| --- | ---: | --- |
| Pixel-art identity | 91 | Original hourglass, square frames, inventory/mission-log language; no borrowed art/font |
| Layout | 88 | Wider upper panes and bounded inspector; very sparse histories still contain natural empty space |
| Typography/readability | 91 | Literal safe text, semantic labels, sizes/modes, readable two-line nested paths |
| Palette | 92 | Both palettes test 4.5:1 semantic text/surface contrast; disabled controls intentionally muted |
| Navigation | 90 | Keyboard panes, archive/path/find filters, stable pages and focus; no mouse required |
| Responsive behavior | 88 | Six requested sizes tested and captured in both themes; 60x24 still requires scrolling |
| Consistency | 90 | Shared theme/syntax tokens, recovery context, cancel-first field guide |
| Professional polish | 88 | Actual-state gallery, no fake loading/animation; no external user study yet |

## Functional scores

| Area | /100 | Evidence / practical limit |
| --- | ---: | --- |
| Checkpointing | 94 | Fresh baseline, complete regression and 10,000-file/deep/binary stress; native scope limits remain |
| Diff inspection | 90 | Numbered bounded text, binary/type/mode summaries, search; no side-by-side or hunk editing |
| Undo | 94 | Contextual state, exact reviewed plan, byte checks and unrelated-edit preservation |
| Redo | 94 | Actual stack ordering, state transition/cancel tests, frozen run checks |
| Selective restore | 89 | Path/directory UI review, cancel/apply preserves unrelated edits; no hunk restore |
| Conflict safety | 95 | Existing adversarial suite plus modal/refresh/concurrent UI checks; no global race immunity |
| Recovery reliability | 92 | Fault-injected journal/recovery acceptance, corruption/migration/GC tests; local POSIX only |
| Agent integration | 82 | Synthetic cwd/env/stdin/TTY/signals and installed Codex/Claude help; no billed/authenticated model session |
| CLI/TUI consistency | 91 | Same backend plans and eligible query, stable JSON, explicit UI bounds and CLI escape path |

## Engineering and QA

Baseline at 7b3a548 was re-executed: **140 passed, three skips**, 85% coverage.
Full local visual gate: **164 passed, three skipped, zero failed**, **86% coverage**
(2,728 statements / 375 missed), 42.18 s, with RuntimeWarning treated as an error.
The final compact header is included in that full gate; focused layout/worker checks also pass.
All original assertions remain; asynchronous pilots explicitly await read workers.
The local skips are unavailable Gemini/Aider executables and a host-stripped setuid
bit, with pure mode validation still tested. No test is disabled or weakened.

Ruff lint/format: 68 files; strict mypy: 29 source files. All pass. A no-I/O theme
test exposed a queued row-selection race; repainting existing cells and lazy worker
factories corrected it. A visual review found stale cached column widths, tall small
reviews and ellipsized recovery paths; those are corrected and regression-tested.
Package and remote verification are recorded in the closeout below.

Actual Textual gallery: nineteen states, including all six sizes in dark/light,
archive, inspector, Undo/Redo/full restore, conflict, empty and narrow review.
The 60x24 header was refined to preserve more code lines and project identity.
Captures are generated from real disposable snapshots and a wrapped Python agent.
The final gallery was refreshed from the installed candidate wheel and inspected;
source captures were not fabricated. README assets pin that exact gallery revision.
See assets/pixel, PIXEL_UI_GUIDE.md and `examples/pixel_gallery.py`.

| Requested real-world scenario | Verification |
| --- | --- |
| Basic Undo / Redo | CLI acceptance and TUI confirmation tests assert original/changed bytes |
| Unrelated edits | Preserved through run-based undo and selected-path recovery |
| Conflicts | Newer touched-file edits refuse mutation; UI explains preservation |
| New / deleted / multiple files | Actual synthetic sessions create/delete/modify combined paths |
| Interrupted operation | Injected disk exhaustion leaves failed journal/recovery; explicit recovery verified |
| Git project | Staged/unstaged/untracked/ignored fixtures preserve index/history context |
| Actual agent transport | Codex/Claude --help exit/PRE/POST tested; Gemini/Aider unavailable; no billable work |
| Corruption/storage/migration | Complete original safety/retention/migration suite and v0.1.0 installed acceptance |
| UI behavior | State transitions, cancel, modal exclusivity, file search/pages, six sizes, resize, theme, slow/stale reads |

## Performance

See PIXEL_OVERHAUL.md and raw benchmarks/pixel-before.json/pixel-after.json for
three sequential alternating runs against the **published** v0.1.0 wheel. Workload:
500 checkpoints, 1,000 files, 1,800 changed source lines, 160x45; macOS 27.2 arm64,
Python 3.12.16, Textual 6.12, truecolor fixture. These are bounded headless timings
including frame/idle waits, not universal interactive latency guarantees.

| Median | Published | Candidate |
| --- | ---: | ---: |
| Settled startup | 267 ms | 278 ms |
| Fifty headers | 1.22 ms | 1.49 ms |
| Settled navigation | 116 ms | 101 ms |
| Large diff opening | 46.9 ms | 47.4 ms |
| Search | 57.3 ms | 55.6 ms |
| Theme switch | 187 ms | 138 ms |
| Theme object reads in each run | 2 | 0 |
| Peak process RSS, fixture included | 65 MiB | 64 MiB |

Fresh 10,000-file / 8 MiB binary / depth-20 fixture: capture 2.137 s, unchanged
0.826 s with zero object-byte growth, diff 0.057 s, Undo 1.673 s, Redo 1.671 s,
verify 0.343 s, GC dry-run 0.649 s, peak process RSS 76 MiB. Saved metadata remains
O(files); previews are bounded and the manifest cache is eight entries. Inventory
rendering stays at 200 rows. Original larger historical benchmarks remain in the
repository; no new 50,000-file throughput claim is made by this UI iteration.

## Compatibility, candidate and limits

macOS/Linux, Python 3.12+ (CI 3.12/3.13/3.14), optional Textual 6.12. Native Windows,
network filesystems, hunk recovery and automatic vendor hooks remain unsupported/
deferred. TimeMachine is not a sandbox. Stop external writers; recovery is not
multi-file atomic and ignored files may contain secrets. Git history/index, external
files, ACLs/xattrs, ownership and timestamps are outside recovery. NO_COLOR,
TIMEMACHINE_ASCII and reduced-motion behavior are tested/documented.

The candidate version is **0.2.0**, prepared as wheel, sdist, checksums and build
manifest in release-artifacts/v0.2.0. Its verified source is identified by BUILD.json;
clean double builds and isolated installs are required before final handoff. No
v0.2.0 tag, release or PyPI upload is authorized by this assignment. The Homebrew
formula remains pinned to stable v0.1.0. PyPI ownership/credentials are still absent.

No known critical data-loss defect remains within the stated safety contract.
Important future work: external user testing, more terminal emulators, native Windows
on real runners. Optional: hunk recovery, automatic hooks, watch/export/compression.
No hosted service or image-generation/runtime dependency was added.

## GitHub and release closeout

[Review PR #1](https://github.com/muratkareem/timemachine/pull/1) targets main from
codex/pixel-tui-v0.2.0. The implementation/evidence range starts at ca9646f after
7b3a548, with 30 cohesive commits including the final installed-gallery and documentation closeout. The final
source SHA is recorded by the candidate BUILD.json and PR head. main remains at
7b3a548; the PR is open, not merged. No history was rewritten or force-pushed.

Both [branch CI 41328985700](https://github.com/muratkareem/timemachine/actions/runs/41328985700)
and [PR CI 41329081554](https://github.com/muratkareem/timemachine/actions/runs/41329081554)
passed all seven jobs for 4c3eada: macOS/Linux × Python 3.12/3.13/3.14, plus clean
reproducible artifact validation. MacOS 3.12 reports 163 passes/four skips; Ubuntu
3.12 reports 162/five (four vendor tools absent; Zsh also absent on Ubuntu). Local
164/three reflects installed Codex and Claude help and host-stripped setuid bits.
[Runtime-identical head CI 41329744412](https://github.com/muratkareem/timemachine/actions/runs/41329744412)
and [PR CI 41329748618](https://github.com/muratkareem/timemachine/actions/runs/41329748618)
also passed all seven jobs at 5bc9dd8. The final installed-gallery/documentation
closeout changes no runtime/tests/dependencies/workflow;
its head checks remain visible on the PR and are verified at handoff.

Wheel/sdist double builds match; Twine checks pass. Isolated wheel and sdist installs
both pass disposable acceptance. The installed wheel generates the nineteen-state
pixel gallery. Candidate source installation from the pinned public commit archive
also passes version/acceptance without cloning. Wheel resources include theme.tcss,
design.py, components.py and dialogs.py; source/archive contents were checked for
project markers, stores and credential files. No snapshots or user secrets upload.
The independent Linux CI wheel/sdist hashes match the local macOS build hashes.

v0.1.0 verification after delivery: release ID 429878043, tag target e10c054, and all
four original asset IDs, byte sizes and SHA-256 digests match the initial record.
No v0.2.0 tag/release or PyPI upload was created. The prepared candidate files in
release-artifacts/v0.2.0 have checksums and exact provenance in BUILD.json; CI also
retains candidate artifacts/gallery for fourteen days. The GitHub connector's PR
write integration returned 403, so the authorized GitHub CLI created the requested
PR. Repository metadata/settings and the stable Homebrew source pin are unchanged.

Known limits are the explicit preview/page/review bounds and unvalidated external
vendor/terminal/platform cases above. There is no unresolved critical defect in
the tested scope. Merge/release publication is a later maintainer decision; this
assignment prepares the candidate and review evidence without publishing it.
