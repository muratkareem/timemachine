![TimeMachine — local recovery for coding agents](https://raw.githubusercontent.com/muratkareem/timemachine/9f804707fc229321daf520e5ee91d029b9186320/docs/assets/pixel/wordmark.svg)

**Undo AI coding agent changes without losing your own work.**

TimeMachine saves selected local files before and after a coding-agent session.
Review the diff and undo that session while preserving unrelated work. It captures
selected untracked and ignored files, and keeps your Git index and history intact.
No account, daemon or API key is required by TimeMachine.

## Try it in a minute

Python **3.12+** · macOS / Linux · **v0.2.0 release candidate**, prepared for review.
Try this verified source revision without cloning:

```sh
uv tool install --python 3.12 'timemachine-cli[tui] @ https://github.com/muratkareem/timemachine/archive/6ca4525535877a53d3c8cf4e096b142091aeb606.tar.gz'

cd /path/to/your/project
timemachine init
timemachine run -- codex          # or claude, gemini, aider, or any command
timemachine tui                   # inspect the session and preview undo
```

The published [stable v0.1.0](https://github.com/muratkareem/timemachine/releases/tag/v0.1.0)
remains available with its previous interface; its tag and artifacts are unchanged.
No v0.2.0 tag, GitHub Release or PyPI publication is claimed.

Prefer the CLI? `timemachine diff`, then `timemachine undo --preview` and
`timemachine undo`. Every restore still uses conflict checks and confirmation.
`timemachine quickstart` explains the workflow and lists installed agents without
launching anything. The agents keep their own authentication and billing.

**Initialization is setup, not a backup.** Wrap each session or create a checkpoint.
The tool installation stays separate from your project dependencies.
[Other installation methods](https://github.com/muratkareem/timemachine/blob/main/docs/INSTALL.md) include pipx and the macOS Homebrew tap.
No PyPI publication is claimed; `timemachine` on PyPI is a different project.

## See the session, understand the recovery

![Real TimeMachine dashboard and unified diff](https://raw.githubusercontent.com/muratkareem/timemachine/9f804707fc229321daf520e5ee91d029b9186320/docs/assets/pixel/dark-160x45.svg)

The dashboard distinguishes saved checkpoints from current files. The timeline
connects agent sessions to PRE/POST snapshots. Choose a file to read its diff,
filter directory paths, or inspect its saved bytes, type and permissions. The primary
action follows actual Undo/Redo session order. File pages remain bounded, and theme
switching preserves selection without reloading snapshot data.

![Real undo review with explicit confirmation](https://raw.githubusercontent.com/muratkareem/timemachine/9f804707fc229321daf520e5ee91d029b9186320/docs/assets/pixel/undo.svg)

Undo first checks affected current paths against the recorded result. A conflicting
newer edit is refused. A recovery checkpoint and journal are retained before writes;
success appears only after the backend verifies the selected result.

These are real screenshots from a disposable project and a wrapped synthetic
Python command. Reproduce them with `python examples/tui_preview.py`. No billed
agent or fake product data is used. [Narrow view](https://raw.githubusercontent.com/muratkareem/timemachine/9f804707fc229321daf520e5ee91d029b9186320/docs/assets/pixel/dark-60x24.svg) · [Light theme](https://raw.githubusercontent.com/muratkareem/timemachine/9f804707fc229321daf520e5ee91d029b9186320/docs/assets/pixel/light-120x40.svg) ·
[Before the redesign](https://github.com/muratkareem/timemachine/blob/main/docs/assets/tui-before.svg) · [Pixel UI guide](docs/PIXEL_UI_GUIDE.md) · [Design and measurements](docs/PIXEL_OVERHAUL.md).

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

In the TUI: **1/2/3** switches archive/files/inspector; arrows or **j/k** navigate.
**Enter/d** opens changes, **/** filters loaded history, **f** filters paths, **u**
reviews Undo, **Ctrl+R** reviews Redo, **r** reviews the full saved checkpoint and
**s** reviews the selected path. **?** opens the field guide; **Esc** cancels or
returns to the archive; **t** switches themes. Find searches the bounded preview.

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

Candidate notes: [v0.2.0](docs/releases/v0.2.0.md). Release details and reproducible checks: [Release procedure](https://github.com/muratkareem/timemachine/blob/main/docs/RELEASE.md).
