# TimeMachine v0.2.0 pixel workspace

## Audit and constraints · 2026-11-01

Start: clean 7b3a548 on main; development branch codex/pixel-tui-v0.2.0.
Fresh local baseline: 140 passed / three documented skips, 85% statement coverage.
Codex and Claude --help transports are installed; Gemini/Aider absent; no billed
agent calls are authorized or required. v0.1.0's tag and four asset identities/hashes
are recorded before work and must remain unchanged.

Observed design/behavior gaps:

- Constant Undo button ignores the actual redo stack and can refer to an older run.
- Fixed 38/29-column sidebars truncate event descriptions and paths on wide screens.
- A wide third inspector column wastes space while history and file context compete.
- The four tall status cards consume too much of a 24–30-line terminal.
- Theme switching performs a full refresh rather than recoloring current selection.
- Restore confirmation lacks file-scoped interaction from the explorer.
- Default widget borders, selectors and footer lack an original coherent identity.

## Design direction

An original save-state console: pixel hourglass, square double frames, inset slots,
numbered archive entries, mint navigation, lavender saved state, amber deliberate
recovery and rose conflict signals. Status always carries words, not color alone.
Terminal fonts remain user-controlled; no raster assets or custom fonts are needed.
ASCII fallback and reduced motion are first-class. Light theme uses ink/paper
counterparts instead of inverting dark colors.

Use a broad upper archive/files workspace above a bounded-height diff stage. This
keeps the mission log and inventory readable and gives small diffs a comfortable
line length. A contextual ledger beside the diff on wide screens shows actual
saved IDs, entry kinds/modes/sizes and scope. At small sizes, one pane at a time
retains keyboard access to archive, files and inspector. No decorative fillers.

Action labels distinguish session order from selection. Catalog-based candidates
are reviewable, not a claim of conflict-free live recovery. The existing backend
must produce and then revalidate every frozen plan; Cancel remains default.
No automatic checkpoint, restore, agent launch or project initialization.

## Verification plan

Preserve CLI JSON, engine formats and v0.1.0 artifacts. Add UI behavior tests and
exercise the existing safety/migration/process suite on disposable projects.
Render actual fixtures at 60x24, 80x24, 100x30, 120x40, 160x45, 200x55 in both
palettes and inspect recovery/conflict/empty views. Measure startup/navigation/
preview/search/theme with saved histories; keep the eight-manifest cache and
bounded preview. Prepare v0.2.0 artifacts and a review PR; publication needs a
new explicit approval. Record final evidence and honest limitations here.

## Measured interaction comparison

Three sequential alternating process runs used the published v0.1.0 wheel and the
candidate with the identical `examples/pixel_benchmark.py` workload: 500 saved
checkpoints, 1,000 project files and an 1,800-line changed source file, 160x45,
macOS 27.2 arm64 / Python 3.12.16 / Textual 6.12. Truecolor fixture, no animation.
All fixtures were disposable. Medians below include headless frame/idle settling,
not a direct estimate of keystroke-to-screen latency in every terminal. Imports
precede the startup timer; peak RSS includes fixture construction. Warm caches are
possible and three runs do not establish statistical throughput guarantees.

| Measurement | Published v0.1.0 | Candidate v0.2.0 |
| --- | ---: | ---: |
| Settled startup | 267 ms | 278 ms |
| Fifty archive headers | 1.22 ms | 1.49 ms |
| Median settled navigation | 116 ms | 101 ms |
| Settled large diff opening | 46.9 ms | 47.4 ms |
| Settled preview search | 57.3 ms | 55.6 ms |
| Settled theme switch | 187 ms | 138 ms |
| Objects reread during theme switch | 2 / 2 / 2 | 0 / 0 / 0 |
| Median process peak RSS | 65 MiB | 64 MiB |

These observations show comparable responsiveness in this bounded workload and
eliminated theme I/O. The candidate retains eight cached manifests and at most
200 inventory rows; the preview visibly clips at 2,001 lines including its warning.
Raw per-run results: benchmarks/pixel-before.json and pixel-after.json. Source
reads remain outside navigation, except deliberate live recovery validation.
The old wheel is unchanged and its own acceptance suite passed on fresh install.
