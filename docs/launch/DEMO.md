# Reproduce the recovery demo

Use a disposable environment and the official wheel; do not install the checkout
in this environment. Python 3.12–3.14, uv and macOS/Linux are required.

```sh
uv venv /tmp/tm-launch-env --python 3.12
uv pip install --python /tmp/tm-launch-env/bin/python 'https://github.com/muratkareem/timemachine/releases/download/v0.2.0/timemachine_cli-0.2.0-py3-none-any.whl[tui]'
/tmp/tm-launch-env/bin/python scripts/launch_demo.py --output /tmp/tm-launch-capture
asciinema play /tmp/tm-launch-capture/demo.cast
```

Choose a new output directory each time. The fixture and store are temporary;
only the recording and verification output survive. Actual CLI stdout/stderr are
captured with exit codes. The script asserts exact undo/redo bytes, rejection of
a conflicting newer edit and integrity verification. Disposable absolute paths
are replaced with `<fixture>` for readability. No result text is fabricated.
`--yes` is used only inside this self-checking disposable fixture.

The default edit is an **AI-authored edit replay**, executed by Python, not a live
agent. To capture an actual installed, authenticated agent, opt in explicitly:

```sh
/tmp/tm-launch-env/bin/python scripts/launch_demo.py --output /tmp/tm-live-agent-capture --agent-command codex exec --skip-git-repo-check 'Edit only hello.py. Make greet strip whitespace from name and append an exclamation mark. Do not modify other files.'
```

This uses your agent credentials and may incur usage. Review agent permissions;
TimeMachine does not sandbox the agent. The script requires the agent to exit
within 180 seconds and change hello.py. Review all captured text before sharing
live-agent footage; credentials, paths and model output may be sensitive.

## 54-second storyboard

| Time | Real output / action | Narration |
| --- | --- | --- |
| 0–12 s | Initialize, save checkpoint | “Save selected local files before a change.” |
| 12–18 s | Wrapped agent edit | “TimeMachine records the command's before and after states.” |
| 18–24 s | Diff | “Review exactly what changed.” |
| 24–36 s | Preview, then undo | “Preview recovery, then restore the original bytes.” |
| 36–42 s | Redo | “Reapply the recorded changes.” |
| 42–48 s | Newer user edit; undo refused | “A conflicting newer edit is preserved.” |
| 48–54 s | Integrity verification | “Local snapshots, explicit scope. Not a sandbox or universal backup.” |

The cast uses six-second presentation holds around actual captured output; this
is edited pacing, not a claim about execution speed. The MP4 is rendered from
those same captures, labelled with its capture mode. Full output is in evidence.json.

For fresh UI screenshots from the installed wheel:

```sh
/tmp/tm-launch-env/bin/python examples/tui_preview.py --view dashboard --output /tmp/dashboard.svg
/tmp/tm-launch-env/bin/python examples/tui_preview.py --view conflict --output /tmp/conflict.svg
```

To render the CLI MP4, install Pillow in a separate rendering environment and run
`python scripts/render_launch_video.py /tmp/tm-launch-capture`, then the ffmpeg
command printed by that script. It does not launch or simulate the product.

## Provenance of the committed capture

The committed video was captured with `--coordinated-edit`. The wrapper runs a
Python wait command that creates an output-directory READY file containing the
disposable project path. This Codex agent applied the greeting patch to hello.py
using its file-edit tool, then created DONE outside the project so the child could
exit and TimeMachine could record POST. No nested agent was launched. This is a
real tool-driven agent edit, not autonomous Codex CLI footage. To reproduce this
mode, start the script with `--coordinated-edit`, read READY, edit hello.py using
your agent, then create DONE within 180 seconds. Never use this wait coordination
with other writers or real projects. The script's default remains a replay.
