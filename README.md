![TimeMachine — local recovery for coding agents](docs/assets/wordmark.svg)

**Checkpoint your project. Run your agent. Inspect every change. Undo safely.**

TimeMachine saves selected local files before and after a coding-agent session.
Review the diff and undo that session while preserving unrelated work. It captures
selected untracked and ignored files, and keeps your Git index and history intact.
No account, daemon or API key is required by TimeMachine.

## Try it in a minute

Python **3.12+** · macOS / Linux · source installation (no PyPI release claimed).

```sh
git clone https://github.com/muratkareem/timemachine.git
cd timemachine
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[tui]'

cd /path/to/your/project
timemachine init
timemachine run -- codex          # or claude, gemini, aider, or any command
timemachine tui                   # inspect the session and preview undo
```

Prefer the CLI? `timemachine diff`, then `timemachine undo --preview` and
`timemachine undo`. Every restore still uses conflict checks and confirmation.
`timemachine quickstart` explains the workflow and lists installed agents without
launching anything. The agents keep their own authentication and billing.

**Initialization is setup, not a backup.** Wrap each session or create a checkpoint.
If you leave the virtual environment, activate it again to use the installed CLI.

## See the session, understand the recovery

![Real TimeMachine dashboard and unified diff](docs/assets/tui.svg)

The dashboard distinguishes saved checkpoints from current files. The timeline
connects agent sessions to PRE/POST snapshots. Choose a file to read its diff,
search its contents, or inspect its saved bytes, type and permissions.

![Real undo review with explicit confirmation](docs/assets/recovery.svg)

Undo first checks affected current paths against the recorded result. A conflicting
newer edit is refused. A recovery checkpoint and journal are retained before writes;
success appears only after the backend verifies the selected result.

These are real screenshots from a disposable project and a wrapped synthetic
Python command. Reproduce them with `python examples/tui_preview.py`. No billed
agent or fake product data is used. [Narrow view](docs/assets/narrow.svg) ·
[Before the redesign](docs/assets/tui-before.svg) · [UX decisions](docs/UX_OVERHAUL.md).

## A small before / after

```sh
printf 'before\n' > hello.txt
timemachine run -- python3 -c "from pathlib import Path; Path('hello.txt').write_text('after\n')"
timemachine diff                  # shows before → after
timemachine undo --preview        # review first
timemachine undo                  # confirm; hello.txt becomes before again
```

For a fully disposable, self-checking demo, run `python examples/demo.py` from the
installed checkout. It asserts the bytes after undo and redo, then removes its fixture.

## The tools you need, in one place

| Task | Command |
| --- | --- |
| Save a manual checkpoint | `timemachine checkpoint -m 'Before refactor'` |
| Discover coding agents | `timemachine agents` |
| Inspect sessions | `timemachine history` or `timemachine tui` |
| Find a checkpoint | `timemachine history --search refactor` |
| See the agent's changes | `timemachine diff` |
| Preview / apply undo | `timemachine undo --preview` / `timemachine undo` |
| Replay undone work | `timemachine redo --preview` |
| Restore a file | `timemachine restore ID --path src/app.py --preview` |
| Check scope / integrity | `timemachine status` / `timemachine doctor` |
| Inspect storage | `timemachine storage` / `timemachine gc --dry-run` |

Short checkpoint IDs work when unambiguous. JSON always keeps full IDs. Interactive
terminals get readable views; redirected output retains the existing JSON format.
Use `--json` explicitly for automation, `--human` to force readable output in pipes,
or `--plain` for no-color output. `NO_COLOR` is respected.

In the TUI: arrows or **j/k** navigate, **Enter/d** opens changes, **/** filters
loaded history, **u** previews undo, **r** reviews restore, **?** opens help, and
**Esc** goes back. Find searches the selected preview. **t** switches light/dark.

## Recovery has a defined scope

- Selected file bytes, directories, link targets and POSIX modes are captured.
- Explicit dependency/cache exclusions are outside recovery. Git-ignored files
  are included unless excluded by TimeMachine's policy. Local snapshots may contain secrets.
- Git history/index, external files, ownership, timestamps, ACLs and xattrs are
  outside scope. Hardlinks and special files are refused.
- External writers can race with recovery. Stop them first; multi-file restore
  is not globally atomic. The wrapper is not a sandbox or universal backup.
- Corruption and interrupted recovery need explicit attention; nothing silently
  rolls back. Keep an independent backup of valuable work.

Read the [safety contract](docs/SAFETY.md) and [recovery guide](docs/RECOVERY.md).
Watch mode, export/import, compression and Windows support remain deferred.

## When something needs attention

| Situation | Safe next step |
| --- | --- |
| Project not initialized | Open its root and run `timemachine init` |
| Agent executable not found | Check `timemachine agents`, its PATH and permissions |
| Undo conflicts with newer work | Keep/copy the newer edits, stop writers, preview again |
| Interrupted run or restore | Run `timemachine doctor`; follow the explicit recovery IDs |
| Small terminal | Enter opens details; Esc returns to history; CLI remains available |
| Corrupt snapshot or store | Stop restore/GC and preserve the store; see the recovery guide |

## Develop and contribute

```sh
pip install -e '.[dev]'
pytest
ruff check src tests examples
mypy
python -m build --no-isolation
```

[Contributing](CONTRIBUTING.md) · [CLI reference](docs/CLI.md) ·
[Installation](docs/INSTALL.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Agent wrappers](docs/INTEGRATIONS.md) · [Security](SECURITY.md) ·
[Measured benchmarks](docs/BENCHMARKS.md) · [Status](docs/STATUS.md) · [MIT license](LICENSE)
