# Recovery

Stop agents, editors and detached children first. Keep the external store intact.
Run `timemachine doctor --json` to identify incomplete checkpoints/runs/restores.
INCOMPLETE checkpoints cannot be selected; their orphan objects can later be GC'd.

For a partial restore, inspect its recovery ID and journal in history, then:

```sh
timemachine recover TRANSACTION_ID --preview --json
timemachine recover TRANSACTION_ID --yes --json
```

Recovery is a new journaled operation restoring the prior transaction's selected
pre-state. It refuses later edits; back them up and resolve manually rather than
forcing overwrites. Other mutation commands are blocked until unfinished restores
are recovered. Completed and recovered journals remain for audit/references.
Temporary stage files from an uncatchable process kill may remain; preserve them,
inspect their contents and move them outside the project before retrying recovery.
The tool does not silently delete uncertain files.

For a crashed wrapper, PRE remains. `finish-run RUN_ID --yes` captures a *late*
POST after external processes stop; undo then encompasses all PRE/late-POST
changes, including intervening edits. Never claim SIGKILL/power-loss POST is exact.

If a manifest/blob is corrupted, do not mutate the store or run GC. Restore a
known-good whole-store backup. TimeMachine detects corruption; it cannot recreate
missing bytes. Permission or read-only filesystem failures may require manual
repair. No Git index/history recovery, external-file recovery, or hardware-level
backup is provided. Move detection requires explicit `rebind` (when available);
never edit canonical roots casually.


## Pre-release catalog upgrade

If writes report an upgrade is required, run `timemachine migrate --preview --json`,
then `timemachine migrate --yes --json`. This upgrades v1 metadata to v2 append-only
journals, preserving snapshots/objects and readable old journals. It is allowed
with an unfinished restore; recover it after migration. Unknown schema versions
remain refused. Keep a whole-store backup before upgrading. The automatically
created `catalog-v1-*.sqlite3` copy is catalog-only; future GC does not retain
objects merely because an old catalog backup mentioned them. Never replace the
live database while writers or WAL sessions are active.
