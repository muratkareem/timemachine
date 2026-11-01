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
