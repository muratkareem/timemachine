![TimeMachine — local recovery for coding agents](https://raw.githubusercontent.com/muratkareem/timemachine/main/docs/assets/wordmark.svg)

**Undo AI coding agent changes without losing your own work.**

TimeMachine saves selected local files before and after a coding-agent session.
Review the diff and undo that session while preserving unrelated work. It captures
selected untracked and ignored files, and keeps your Git index and history intact.
No account, daemon or API key is required by TimeMachine.

## Try it in a minute

Python **3.12+** · macOS / Linux · version [**0.1.0**](https://github.com/muratkareem/timemachine/releases/tag/v0.1.0).
Install the verified release wheel with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install --python 3.12 'https://github.com/muratkareem/timemachine/releases/download/v0.1.0/timemachine_cli-0.1.0-py3-none-any.whl[tui]'

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
The tool installation stays separate from your project dependencies.
[Other installation methods](https://github.com/muratkareem/timemachine/blob/main/docs/INSTALL.md) include pipx and the macOS Homebrew tap.
No PyPI publication is claimed; `timemachine` on PyPI is a different project.

## See the session, understand the recovery

![Real TimeMachine dashboard and unified diff](https://raw.githubusercontent.com/muratkareem/timemachine/main/docs/assets/tui.svg)

The dashboard distinguishes saved checkpoints from current files. The timeline
connects agent sessions to PRE/POST snapshots. Choose a file to read its diff,
search its contents, or inspect its saved bytes, type and permissions.

![Real undo review with explicit confirmation](https://raw.githubusercontent.com/muratkareem/timemachine/main/docs/assets/recovery.svg)

Undo first checks affected current paths against the recorded result. A conflicting
newer edit is refused. A recovery checkpoint and journal are retained before writes;
success appears only after the backend verifies the selected result.

These are real screenshots from a disposable project and a wrapped synthetic
Python command. Reproduce them with `python examples/tui_preview.py`. No billed
agent or fake product data is used. [Narrow view](https://github.com/muratkareem/timemachine/blob/main/docs/assets/narrow.svg) · [Light theme](https://github.com/muratkareem/timemachine/blob/main/docs/assets/light.svg) ·
[Before the redesign](https://github.com/muratkareem/timemachine/blob/main/docs/assets/tui-before.svg) · [UX decisions](https://github.com/muratkareem/timemachine/blob/main/docs/UX_OVERHAUL.md).

## A small before / after

```sh
printf 'before\n' > hello.txt
timemachine run -- python3 -c "from pathlib import Path; Path('hello.txt').write_text('after\n')"
timemachine diff                  # shows before → after
timemachine undo --preview        # review first
timemachine undo                  # confirm; hello.txt becomes before again
```

A real [scripted terminal recording](https://github.com/muratkareem/timemachine/blob/main/docs/assets/demo.cast) can be played with
`asciinema play docs/assets/demo.cast` from a checkout. Regenerate it with
`python scripts/record_demo.py --output /tmp/timemachine-demo.cast`.
For a fully disposable, self-checking demo, run `python examples/demo.py` from the
installed checkout. It asserts the bytes after undo and redo, then removes its fixture.

## The tools you need, in one place

| Task | Command |
| --- | --- |
| Save a manual checkpoint | `timemachine checkpoint -m 'Before refactor'` |
| Discover coding agents | `timemachine agents` |
| Opt in once in Bash/Zsh | `timemachine integrate --output /new/path/agents.sh` |
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

Read the [safety contract](https://github.com/muratkareem/timemachine/blob/main/docs/SAFETY.md) and [recovery guide](https://github.com/muratkareem/timemachine/blob/main/docs/RECOVERY.md).
Existing v1 catalogs require an explicit `timemachine migrate --preview` and
`timemachine migrate --yes` before new writes. Manifests and objects stay compatible.
Native Windows, hunk recovery, vendor hooks, watch, export and compression are deferred.

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
ruff check src tests examples scripts
mypy
python -m build --no-isolation
```

[Contributing](https://github.com/muratkareem/timemachine/blob/main/CONTRIBUTING.md) · [CLI reference](https://github.com/muratkareem/timemachine/blob/main/docs/CLI.md) ·
[Installation](https://github.com/muratkareem/timemachine/blob/main/docs/INSTALL.md) · [Architecture](https://github.com/muratkareem/timemachine/blob/main/docs/ARCHITECTURE.md) ·
[Agent wrappers](https://github.com/muratkareem/timemachine/blob/main/docs/INTEGRATIONS.md) · [Security](https://github.com/muratkareem/timemachine/blob/main/SECURITY.md) ·
[Measured benchmarks](https://github.com/muratkareem/timemachine/blob/main/docs/BENCHMARKS.md) · [Status](https://github.com/muratkareem/timemachine/blob/main/docs/STATUS.md) · [MIT license](https://github.com/muratkareem/timemachine/blob/main/LICENSE)

Prepared release details, publication blockers and reproducible checks: [Release procedure](https://github.com/muratkareem/timemachine/blob/main/docs/RELEASE.md).
