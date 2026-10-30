# UX overhaul

## Audit and implementation order

Baseline: 6d28695. Human output is mostly escaped JSON; the TUI has no dashboard,
session navigation, search or readable recovery explanation. History loading reads
many manifests repeatedly. Confirmation is safe but difficult to review.

1. Shared semantic palette, safe Unicode text, units and reusable presentation.
2. Metadata-only paged timeline/read cache; dashboard and lazy file previews.
3. Textual workspace: session/checkpoint history, search, diff, responsive panes,
   help and guided recovery. Preserve frozen plans and run identity.
4. Human CLI views/onboarding/errors, stable JSON/redirected output, optional
   quickstart and agent discovery. No automatic command execution.
5. Original SVG wordmark, real screenshots and concise README.
6. Pilot tests, safety regression suite, format/type/build checks, measured UI
   data-load behavior and macOS/Linux CI. Commit coherent verified slices.

## Design language

Ink backgrounds, mint primary action, lavender protected state, green additions,
amber modifications, rose deletions/conflicts. Every state also has a text label.
Use terminal typography, compact separators, visible focus and quiet surfaces.
Dark by default; light theme switch; NO_COLOR and plain CLI alternatives.
C0/C1/control/bidi characters are escaped; ordinary Unicode remains readable.
All untrusted text is literal Rich Text, never interpreted as markup.

## Compatibility and safety

Automatic human CLI output is limited to interactive terminals. Redirected output
retains its previous JSON structure. --json always wins; --human and --plain are
explicit presentation overrides. IDs in JSON remain full IDs. Short unique IDs
may resolve only if unambiguous. No core storage format changes are needed.

Navigation never scans the working tree. Live undo eligibility is checked only
when explicitly previewed; the dashboard never calls an old snapshot current.
Recovery dialogs keep immutable plans/run IDs through confirmation. Backend
locking, revalidation, recovery checkpoints and journals remain authoritative.
