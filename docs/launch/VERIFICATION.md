# Launch verification — 2026-11-03

Verified against main baseline `bc09c6a777a6895a595d3f1059d4370081b53d53`.
Documentation and capture tooling only; recovery engine, version and dependencies
are unchanged. No new distribution was built or release created.

## Published installation

```sh
uv tool install --python 3.12 'https://github.com/muratkareem/timemachine/releases/download/v0.2.0/timemachine_cli-0.2.0-py3-none-any.whl[tui]'
```

A fresh isolated environment installed that wheel directly and reported `0.2.0`.
SHA-256 of the downloaded wheel:
`37f55f1289a5f5d2387aa953e338146d0b9fcd1f865a3fec4031d1a412a78b7c`.
All four downloaded assets match GitHub's SHA-256 digests; wheel and source archive
also match SHA256SUMS and BUILD.json. The tag resolves to
`5373901539c6d1748256263d76102f7b36f94fd3`.

## Executed checks

- Installed-wheel `scripts/acceptance.py`: normal session, unrelated edits,
  conflict refusal, Git invariants, interrupted restore recovery, packaged TUI
  and first-run workflow passed in disposable projects.
- `scripts/launch_demo.py`: checkpoint, wrapped real Codex tool edit, diff,
  undo/redo byte assertions, conflict preservation and integrity passed.
  Default replay reproduction also passed. Captures: `docs/assets/launch/`.
- Full `pytest -q`: **173 passed, 3 skipped**. Skips: absent Gemini/Aider and
  host-stripped setuid mode. No claim of live integration for missing agents.
- Ruff lint and formatting: passed. Strict mypy: **29 source files passed**.
- MP4: H.264, 1600×1000, 54 seconds, no audio; actual CLI captures with explicit
  six-second presentation holds. Dashboard and conflict SVGs generated using the
  installed wheel, rendered and visually inspected, along with video frames.
- Repository description, ten topics and quickstart homepage configured.

## CI and remaining limitations

The tagged release's [original CI](https://github.com/muratkareem/timemachine/actions/runs/41420598910)
passed seven jobs. At audit time the previous main [workflow](https://github.com/muratkareem/timemachine/actions/runs/41484449652)
had five successful jobs and two cancelled macOS 3.13/3.14 jobs with no steps.
Annotations explicitly cite hosted macOS arm64 capacity constraints. No repeated
reruns or workflow changes were made for that external issue. New launch-commit
CI is reported separately in the delivery report; this file does not predict it.

The [social preview PNG](../assets/launch/social-preview.png) is a real installed
UI capture. Upload it under GitHub repository Settings → General → Social preview;
the repository API/CLI used here does not provide that upload control. It has not
been configured remotely.

Promotional posts remain drafts pending maintainer approval. No testimonials,
download counts or universal safety claims were invented. Native Windows, hunk
recovery and vendor hooks remain deferred. Local snapshots may contain secrets;
external writers must stop before restore, which is not globally atomic. Read
[the safety contract](../SAFETY.md) before protecting valuable work.
