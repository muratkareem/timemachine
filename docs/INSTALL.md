# Installation

Python 3.12+ and POSIX macOS/Linux are required. In the cloned repository:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e .
timemachine --help
```

For development use `pip install -e '.[dev]'`; for Textual use `.[tui]`.
Alternatively `pipx install .` isolates the command. Distribution name is
`timemachine-cli` (provisional, not published/availability-verified).

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
