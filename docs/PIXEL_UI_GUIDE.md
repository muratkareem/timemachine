# Save-state console · v0.2.0 candidate

The pixel workspace is an original terminal interface built from characters,
square frames and coordinated semantic colors. It uses your normal terminal font,
not bundled art/fonts. There is no animation, sound, daemon or automatic recovery.

## First minute

From the root of a project, `timemachine init` creates an identity and private
external store. **It is setup, not a backup.** `timemachine run -- COMMAND` saves
PRE, launches your installed agent with its normal terminal/environment, then saves
POST. `timemachine checkpoint -m 'Before refactor'` captures a manual save instead.
Open `timemachine tui`, inspect an archive entry/file, then review Undo. Cancel is
focused first. A newer conflicting edit refuses recovery; preserve it and stop
writers before another review. Git history/index and excluded paths are outside
recovery. Ignored files can contain secrets. The wrapper is not a sandbox.

## Workspace

The header identifies the project. Slots distinguish saved checkpoint availability
from the live files (which have not been scanned), show the latest actual session
state, selected change counts and object bytes/quota. Catalog/journal bytes require
additional disk space. The quota meter describes object bytes, not a full disk quota.

The archive differentiates applied/undone/invalidated or interrupted sessions,
pinned saves, checkpoints and recovery operations. PRE/POST saves are grouped under
their session. The ledger identifies both snapshots. Selecting a recovery operation
shows the safeguard captured **before** the operation, not a claim about live files.
Search filters loaded entries; Load older fetches another fifty using a stable
cursor, so incoming checkpoints do not duplicate earlier pages.

The inventory shows change type, filename, parent path and size. Root filenames
are already relative paths and use one row; nested paths use two. It renders at
most 200 entries at a time. Previous/Next are keyboard reachable through Tab. Path
filtering searches all entries in the selected saved comparison, including later
pages, with Unicode case folding. A filtered inventory does not alter full-restore
scope; use `s` for the explicitly selected path.

The inspector shows saved bytes or a unified diff, numbered display lines, actual
mode/size changes, binary/link/directory metadata and visible truncation. Hunk
headers contain original source-line positions. Reading is no-follow and bounded:
1 MiB per text file, 2,000 displayed lines and 500 characters per displayed line.
Stored content remains intact. Find searches only the displayed preview; unmatched
text may be beyond that boundary. Use the CLI or an external editor for broader work.

## Keys

| Key | Action |
| --- | --- |
| 1 / Esc | Archive (Esc cancels a modal first) |
| 2 | File inventory |
| 3 / Enter / d | Inspector / open selected changes |
| Tab / Shift+Tab | Move focus; reach filters, page controls and buttons |
| Arrows / j k | Move in the focused list |
| / | Search loaded archive |
| f | Filter all selected file/directory paths |
| Find input + Enter / n | Find / cycle displayed-preview matches |
| v | Saved file / unified diff |
| b | Use selected save as comparison origin, then choose another entry |
| u / Ctrl+R | Review session-order Undo / Redo |
| r / s | Review full selected snapshot / selected file or directory |
| F5 | Refresh catalog and invalidate saved read cache |
| t / ? / q | Light-dark / field guide / quit |

Typing in an input does not execute these global letter shortcuts. Review dialogs
block underlying actions; Cancel is the default and Esc cancels. Large reviews
above 500 entries cannot apply from the TUI: use CLI --preview to review the full
plan and then explicitly apply there. This limit prevents a truncated authorization.

## Recovery controls

The primary action uses the same eligible-session query as the backend. Redo takes
priority for the selected undone session; older applied sessions do not override
it. A candidate is **reviewable**, not proof that current files are conflict-free.
Actual backend planning runs under the writer lock before a modal appears, and the
frozen plan/run is revalidated after consent. An older selected session that is not
next in stack order cannot silently invoke a different run. Unfinished operations,
pending catalog migration or unreadable state disable controls and explain doctor/
recovery steps. Refresh after resolving an error. No automatic override is provided.

## Terminal/accessibility

Verified fixture sizes: 60x24, 80x24, 100x30, 120x40, 160x45 and 200x55. Short
terminals replace the four slots with a compact summary. Narrow screens expose
one pane at a time through 1/2/3; wide screens show both upper panes and the lower
diff stage, with an optional factual ledger. Long diffs and reviews scroll.

Mint = navigation, lavender = saved state, amber = deliberate recovery, rose =
conflict, green = additions. Every state also has words/markers. Both palettes have
4.5:1 tested semantic text/surface contrast. Disabled controls are intentionally
muted. `NO_COLOR=1` uses Textual's monochrome filter; `TIMEMACHINE_ASCII=1` or
`TERM=dumb` selects ASCII chrome. User filenames/content retain their Unicode.
No custom font, wide emoji or color-only status is required. Navigation and
rendering use bounded saved data, not a live source scan. Theme switching reuses
current data; expensive reads run in cancellable workers, while mutations retain
explicit backend locks and confirmation.

## Trouble

- No archive: wrap a command or save a manual checkpoint; initialization is not capture.
- No matching file/event: clear the relevant filter and refresh/load older as needed.
- Undo/Redo differs from selection: select the indicated next eligible session.
- Conflict: preserve newer work, stop writers, review again; there is no force switch.
- Interrupted/corrupt store: preserve it and use `timemachine doctor`; see RECOVERY.md.
- Low-capability/small terminal: use ASCII/no-color or the `--plain` CLI.

v0.1.0 remains the published stable release. v0.2.0 is a review candidate, with no
new tag/release publication implied by screenshots or successful CI.
