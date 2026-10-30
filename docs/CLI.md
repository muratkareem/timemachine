# CLI

All commands support `--help`, grouped into everyday, recovery and diagnostics.
Interactive terminals get human-readable views. Redirected output keeps its
previous JSON structures; `--json` always explicitly selects the stable JSON
contract. `--human` forces readable views in pipes; `--plain` also disables color
and animation. NO_COLOR is respected. Untrusted markup/controls are never executed.

Checkpoint commands accept a full UUID hex ID or an unambiguous prefix of at least
four digits. JSON always returns full IDs. Run and transaction IDs remain full IDs.
`history --search TEXT` filters the returned page (increase --limit for older rows).
`quickstart` teaches the workflow and lists executable availability, without
initializing or launching an agent. Init's optional --json keeps the same result
fields as earlier redirected init output. Initialization is never called a backup.

- `init [--storage PATH]`: initialize current directory, external empty store.
- `status [--json]`: actual included/excluded paths, bytes, policy and Git context.
- `checkpoint [-m MESSAGE] [--json]`: durable COMPLETE checkpoint or failure.
- `list [--limit N]`, `history [--limit N]`: checkpoint/run/restore relationships.
- `show ID`, `inspect ID`: exact entry types, sizes, modes, hashes and Git context.
- `diff [A B] [--stat] [--name-only] [--path PATH] [--json]`: latest run by default;
  without a completed run requires two IDs. UTF-8 previews limited to 1 MiB;
  binary/non-UTF-8 data has a metadata summary. Mode/type differences are explicit.
- `run -- COMMAND [ARGS...]`: preserve terminal, current subdirectory and env;
  captures PRE and POST even for ordinary nonzero exits; returns command status.
- `undo [--preview] [--yes] [--json]`: reverse most recent applied completed run.
  Newer conflicting edits refuse. Unrelated edits survive. Git warnings require
  acknowledgment; `--yes` is explicit acknowledgment. No Git repair.
- `doctor [--json]`, `verify [--json]`: inspect unfinished work and verify integrity.
- `recover TRANSACTION_ID [--preview] [--yes] [--json]`: explicit partial-restore
  recovery, only when all affected current entries match journal-allowed states.
- `finish-run RUN_ID --yes`: capture an explicitly late POST after a crash. It
  includes any intervening edits and never claims the original command finished.

Mutations prompt unless `--yes`; machine-readable mutations require `--yes` or
`--preview`. Preview is read-only. Exit 0 success; 1 actionable I/O/integrity/safety
failure; 2 usage error (confirmation cancellation returns 1); wrapped command status is propagated
(128+signal for signal termination; 127 launch failure). No force-conflict flag.

- `redo [--preview] [--yes] [--json]`: linear replay after undo. New successful
  run/restore invalidates redo; checkpoint-only activity does not.
- `restore ID [--path PATH] [--preview] [--yes] [--json]`: all protected scope or
  file/directory subset. Current differences are explicitly authorized, including
  deletion of later files. Revalidation still refuses edits after preview/consent.
- `rebind --yes`: explicitly update a moved project's canonical root identity.

- `storage [--json]`: deduplicated object bytes, quota and reclaimable names.
- `tag ID LABEL`, `pin ID`: protect checkpoints from deletion/pruning.
- `delete ID [--preview] [--yes]`: only unreferenced, untagged, unpinned snapshots.
- `gc [--dry-run] [--yes]`: verify live data then collect unreferenced objects.
- `prune [--keep N] [--preview] [--yes]`: retain newest N checkpoints plus every
  protected reference; delete eligible older metadata only. GC remains separate.
  Run/recovery/journal history is retained indefinitely; quota exhaustion requires
  deliberate storage management. Compression and automatic schedules are absent.

- `tui`: optional Textual workspace (`pip install -e '.[tui]'` in the checkout).
  Dashboard shows saved-state availability, latest session, selected file counts,
  snapshot bytes and relevant Git/recovery warnings. Navigation never scans live
  project files. Undo preview performs the real current-state conflict check.
  Arrows/j/k navigate; Enter/d opens details; Esc returns to history on narrow
  terminals; / filters loaded history; Load older fetches another 50 events.
  Find searches the selected preview; Enter/n finds the next match; v toggles
  saved file/unified diff; b sets comparison origin. u/r/Ctrl+R preview undo/full
  checkpoint restore/redo; ? opens help; t switches dark/light; F5 refreshes.
  Review defaults to Cancel; empty plans cannot be applied. Frozen plans and run
  IDs are revalidated through the existing backend after confirmation.
  Suggested minimum: 60 columns x 24 rows. CLI remains the accessible alternative.
  File text is limited to 1 MiB before preview; displayed text is bounded to 2000
  lines and 500 characters per line, with explicit truncation. Stored data is intact.
