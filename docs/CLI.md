# CLI

All commands support `--help`. Read-only JSON is available through `--json` on
status, doctor, checkpoint, list, history, show/inspect, diff, verify, undo and
recover. Text output is indented JSON with escaped terminal controls. No markup
interpretation of project filenames or contents. IDs are full UUID hex strings.

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
failure; 2 usage/confirmation cancellation; wrapped command status is propagated
(128+signal for signal termination; 127 launch failure). No force-conflict flag.
