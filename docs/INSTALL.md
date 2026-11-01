# Installation

## v0.2.0 review candidate

The pixel workspace is prepared on codex/pixel-tui-v0.2.0, not published as a new
release. Its compatible catalog remains v2 and manifest remains v1. Try the verified
candidate code revision without cloning:

```sh
uv tool install --python 3.12 'timemachine-cli[tui] @ https://github.com/muratkareem/timemachine/archive/3266e70e29a37dbb8631e1b09733ee383d677374.tar.gz'
```

Or install the prepared wheel using `uv tool install '/absolute/path/to/timemachine_cli-0.2.0-py3-none-any.whl[tui]'`.
End users need no development dependencies. The Homebrew formula still installs
published v0.1.0. The candidate does not change its source pin or existing assets.
The following stable installation and storage instructions remain valid.


Python 3.12+ and macOS/Linux local filesystems are required. Native Windows and
shared/network filesystem recovery are not validated. See PLATFORMS.md.

## No clone required

[GitHub v0.1.0](https://github.com/muratkareem/timemachine/releases/tag/v0.1.0) is published with wheel, source archive, checksums and
build manifest. Its tag points to `e10c054ec38eb129dc985d0b521b1214c4e65b19`.
The public release wheel install and installed acceptance/TUI checks pass:

```sh
uv tool install --python 3.12 'https://github.com/muratkareem/timemachine/releases/download/v0.1.0/timemachine_cli-0.1.0-py3-none-any.whl[tui]'
```

### Pinned source alternative

The verified runtime commit is pinned so installation does not silently track
future main-branch changes. Both uv and pipx isolate dependencies from your project:

```sh
uv tool install --python 3.12 'timemachine-cli[tui] @ https://github.com/muratkareem/timemachine/archive/9ae8c4d07ef4acbdbe2c87220a0d562276810b16.tar.gz'
timemachine --version
timemachine quickstart
```

If the executable is not on PATH, follow uv's tool-bin guidance (`uv tool dir --bin`)
and add that directory to your PATH. Install uv from its
[official documentation](https://docs.astral.sh/uv/). Alternatively, with pipx and
Python 3.12+ installed:

```sh
pipx install 'timemachine-cli[tui] @ https://github.com/muratkareem/timemachine/archive/9ae8c4d07ef4acbdbe2c87220a0d562276810b16.tar.gz'
```

Distribution name is `timemachine-cli`; `timemachine` on PyPI is unrelated. This
project has not been uploaded to PyPI. Public name lookup returned 404 for
`timemachine-cli` on 2026-10-31, which does not establish ownership/reservation.
Do not replace the archive install with an unverified package of the same name.
Omit `[tui]` for the smaller CLI-only install. No development dependencies are needed.
Wheel and commit-archive installations have been tested with both uv tool and pipx.

## macOS Homebrew tap

This repository is also an explicit tap (no Homebrew Core submission or bottles):

```sh
brew tap muratkareem/timemachine https://github.com/muratkareem/timemachine
brew install muratkareem/timemachine/timemachine
timemachine --version
```

The formula pins the same runtime commit and dependency-wheel hashes. It was built
from source and its undo/redo/integrity test executed on macOS arm64 with Homebrew
Python 3.12. A uniquely named temporary validation tap/formula was used locally;
the public formula commit is now pushed. Intel and Linux brew
installation are not validated. The CLI itself is tested separately on macOS/Linux.

## Built artifact or developer checkout

A verified local wheel supports `uv tool install '/absolute/path/to/wheel.whl[tui]'`
or `pipx install '/absolute/path/to/wheel.whl[tui]'`. Source archives install in a
clean venv as well. Publication status and checksums are in RELEASE.md and the
release build manifest; do not assume a GitHub Release URL exists before publication.

For contributors, from the cloned repository:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e .
timemachine --help
```

For development use `pip install -e '.[dev]'`; for Textual use `.[tui]`.

Remove a tool install with `uv tool uninstall timemachine-cli`,
`pipx uninstall timemachine-cli`, or `brew uninstall timemachine`, according to
the method used. These remove the tool, not project markers or external snapshots.
Preserve stores for recovery. Disable sourced agent functions with `unset -f`
before removing their bound interpreter; regenerate them after reinstalling.

## Project storage and policy

Initialize from the project root with `timemachine init [--storage /external/empty]`.
Default: `$XDG_DATA_HOME/timemachine/UUID`, macOS
`~/Library/Application Support/TimeMachine/UUID`, or Linux
`~/.local/share/timemachine/UUID`. Store must be outside the root and Git metadata.
Never store snapshots on a shared/untrusted filesystem. Back up the whole external
store and marker together when quiescent; objects alone omit metadata/relationships.

The JSON marker configures `exclude` glob patterns, `max_file_bytes` (256 MiB) and
`quota_bytes` (10 GiB). Edit deliberately; inspect status before checkpointing.
Git ignore rules do not exclude files. `.git` and `.timemachine.json` are mandatory
exclusions at any depth. Optional default directory names match at any depth.

`symlink_policy` is `record` (opaque link targets, default) or `reject` (fail any
checkpoint encountering a symlink). It never follows link targets. Older markers
without this optional key use `record`. `quota_bytes` limits object bytes; metadata,
WAL files and temporary/recovery staging need additional free disk space. It is
not an operating-system hard quota. Status/doctor expose actual included paths,
Git tracked/untracked/ignored categories and exclusions; directory/nested entries
that Git does not classify are labelled explicitly.
