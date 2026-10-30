# TimeMachine — Ctrl+Z for coding agents

A local-first Python CLI that checkpoints a project's files before a coding-agent
session, shows its changes, and safely undoes them. Git tracks commits and staging;
TimeMachine also captures selected untracked and ignored files. It preserves the
Git index and history rather than resetting them. No account, daemon or API key.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e .                 # from this repository
cd /path/to/your/project
timemachine init                 # one small identity marker; backups outside project
timemachine run -- codex         # any executable and argv, with terminal inherited
timemachine history --json
timemachine diff
timemachine undo --preview
timemachine undo --yes
```

Synthetic demo without an agent (inside a disposable directory):

```sh
printf 'before\n' > hello.txt
timemachine run -- python3 -c "from pathlib import Path; Path('hello.txt').write_text('after\n')"
timemachine diff
timemachine undo --yes
cat hello.txt                    # before
```

Checkpoints use SHA-256 objects, stable double scans and transactional metadata.
Undo touches only paths changed by the wrapped command, refusing conflicting
later edits. Every restore has a recovery checkpoint and journal. Git changes
made by the command are reported and are **not** automatically reversed.

The wrapper is not a sandbox or a universal backup. External files, Git metadata,
ACLs/xattrs, ownership and timestamps are not protected. Hardlinks/special files
are refused. Explicitly excluded dependency/cache directories are not recoverable.
Snapshots may contain local secrets. Concurrent external writers cannot be made
race-free; stop them before recovery. No global multi-file atomicity is claimed.

Python 3.12+, POSIX macOS/Linux target. See [safety](docs/SAFETY.md),
[architecture](docs/ARCHITECTURE.md), [CLI](docs/CLI.md), [installation](docs/INSTALL.md),
[recovery](docs/RECOVERY.md), [integrations](docs/INTEGRATIONS.md) and
[execution status](docs/STATUS.md). This is source software; no published package
or remote CI success is implied.
