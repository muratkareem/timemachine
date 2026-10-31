# Release procedure

Target version: **0.1.0**. Distribution name: **timemachine-cli**. No PyPI ownership
or publication is implied by repository ownership. The unrelated PyPI project
`timemachine` must not be used. The public JSON endpoint for `timemachine-cli`
returned 404 during the 2026-10-31 audit; this is not a name reservation. Recheck
ownership immediately before upload. No upload token was available during preparation.

## Build and verify, without publication

Use Python 3.12+ on a supported host, a clean committed checkout, and a release
tool environment installed from `requirements/release.txt`. Then:

```sh
python scripts/build_release.py --output release-artifacts
python -m twine check release-artifacts/*.whl release-artifacts/*.tar.gz
```

The script builds a `git archive HEAD` twice in independent temporary directories,
sets SOURCE_DATE_EPOCH to the commit timestamp, and compares both artifact hashes.
It refuses dirty source or an existing output directory. It creates wheel, sdist,
SHA256SUMS and BUILD.json with commit/tool provenance. It never reads local snapshot
stores and never uploads. This establishes repeatability for that source/toolchain,
not a cryptographic attestation or identical bytes under every future tool version.

Install the wheel with `[tui]` into clean venv, uv tool and pipx environments;
run `scripts/acceptance.py`, `examples/demo.py` and `examples/tui_preview.py` using
each installed interpreter. Verify stylesheet resources. Test source installation
from the sdist too. CI builds twice, validates metadata and retains a candidate
artifact for fourteen days; upload-artifact is storage for review, not a release.

Before approval, check full pytest/coverage, Ruff/format, strict mypy, all six
macOS/Linux/Python matrix jobs, acceptance results, migration and changelog. Review
the actual wheel/sdist contents and dependency/license inventory. Confirm there
are no unresolved critical data-loss findings and the working tree is clean.

## Publication gate

Publishing a tag/GitHub Release needs explicit maintainer authorization separate
from pushing implementation commits. After authorization, create `v0.1.0` at the
reviewed commit, push that tag without force, and publish the exact verified wheel,
sdist, checksums and build manifest with `docs/releases/v0.1.0.md` as release notes.
Check that remote tag/commit, downloaded asset hashes and installed bytes match.
Do not silently replace existing tag/assets. Publication is intentionally manual.

PyPI additionally needs verified ownership and an authorized upload token or trusted
publisher. Never print credentials or put them in commands/docs/commits. Prefer a
scoped trusted-publisher setup. If ownership or credentials are unavailable, retain
validated artifacts and use the tested commit-archive install instead. Do not run
an upload command merely to test credentials.

## Homebrew maintenance

`Formula/timemachine.rb` pins the verified production runtime commit and all pure
Python wheels by public URL/SHA-256. The repository can be used as an explicit tap;
it is not submitted to Homebrew Core and no bottles are claimed. Update source
commit/hash, version and resources together. Build with the installed Homebrew
Python, then run `brew test` and the installed acceptance/TUI smoke before promotion.
`requirements/homebrew-resources.json` records the dependency inputs. Regenerate
resources from an isolated `[tui]` + release-backend resolution and official PyPI
JSON; review each hash/URL. Do not introduce unpinned network resolution at install.

Repository presentation, when separately authorized: description “Undo AI coding
agent changes without losing your own work”; topics `coding-agents`, `developer-tools`,
`python`, `cli`, `textual`, `checkpoints`, `undo`, `local-first`. Source templates and
README need no repository-setting change. Private vulnerability reporting requires
maintainer configuration and is not claimed enabled.
