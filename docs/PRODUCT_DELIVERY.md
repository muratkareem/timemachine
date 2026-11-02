# v0.2.0 published — 2026-11-02

[GitHub Release v0.2.0](https://github.com/muratkareem/timemachine/releases/tag/v0.2.0)
is public. PR #1 merged with history preserved. Annotated tag v0.2.0 resolves to
5373901539c6d1748256263d76102f7b36f94fd3. All seven release-commit CI jobs pass
(run 41420598910). Fresh local suite: 173 passed, 3 documented skips, 86% coverage.
Clean double builds, Twine and isolated wheel/sdist recovery acceptance pass;
all four uploaded assets match verified originals. Public install: INSTALL.md.
The original v0.1.0 release is unchanged. No PyPI upload was performed.

## Historical preparation record

# Final product completion — 2026-11-02

Simple is the default presentation. Advanced retains the full workspace through
an explicit mode button and `a`. Both use the same recovery plans and services;
no backend, CLI JSON, metadata format, dependency or security policy changed.
The first-run view explains that initialization saves no files. Help documents a
generic protected command; no particular coding agent is required. Mode choice
is session-local and writes no preferences or project metadata.

## Evidence and assessment

Fresh baseline: 164 passed, 3 skipped. Final tests cover all original safety cases
and nine new beginner cases: six dimensions (60x24 through 207x58), mode switches
with byte-identical stores, mouse controls, keyboard focus, Help, Undo/Redo/cancel,
conflict refusal and edits between preview/confirmation. Original UI regression
assertions run explicitly in Advanced mode. No tests or safety rules were disabled.
Final local gate: **173 passed, zero failed, three skipped; 86% coverage**
(2,795 statements, 378 missed), 62.84 seconds. Skips are Gemini/Aider absence
and a filesystem-stripped setuid bit (pure validation is tested separately).
Remote checks are recorded in PR #1 at handoff.
Ruff lint/format (69 files) and strict mypy (29 source files) pass.

Real source acceptance passes: installation-facing command flow, unrelated edits,
conflicts, new/deleted files, Git index/history preservation, injected disk failure,
explicit recovery, integrity and packaged TUI. The full test suite covers POSIX
modes, symlinks, traversal, malformed snapshots, SQLite/catalog/GC, subprocess
transport and CLI JSON. Codex/Claude help are exercised; Gemini/Aider are absent.
No authenticated/billed model session or external human study is claimed.

Fresh 10,000-file, depth-20, 8 MiB binary, 100-edit fixture passes two Undo/Redo
roundtrips, verify and GC dry-run. Capture 2.828 s; unchanged 1.112 s with zero
object growth; Undo 2.183 s; Redo 2.122 s. Raw results: benchmarks/simple-scale.json.

Three alternating process runs compared the preceding installed candidate with
Simple mode: 500 checkpoints, 1,000 files, 1,800 changed source lines, 160x45,
macOS 27.2 arm64, Python 3.12.16. Timings include headless frame/idle waits; test
and capture processes also ran during parts of this pass, so treat small changes
as observations, not universal latency guarantees. No material regression was
observed. Startup median 276 -> 294 ms; navigation 101 -> 86 ms; diff 45.5 -> 44.5 ms;
search 93.8 -> 48.7 ms; theme 148.9 -> 117.0 ms. Cache remains eight manifests;
theme object reads remain zero. Raw results: benchmarks/simple-comparison.json.

Twenty-one real captures in assets/simple include both themes at all six sizes,
Advanced, Help, empty, completed, Undo/Redo/restore, conflict, history and narrow
review. Visual inspection corrected clipped narrow guidance, overly technical
reviews, narrow filenames, unwrapped conflict guidance and a first-run refresh
race that replaced onboarding with an empty-history message. Regression tests
cover the objective behavior. This is a simulated beginner walkthrough, not an
independent usability study. Remaining friction: commands start from the terminal,
small screens require pane navigation, and advanced recovery needs careful review.

| Area | Score /100 | Basis and limitation |
| --- | ---: | --- |
| Visual design | 90 | Original pixel identity, two themes, real inspected captures |
| Beginner usability | 87 | Two-panel default, visible guidance; no external user study |
| Navigation | 91 | Mouse/keyboard, focus and six-size tests; narrow panes require switching |
| Feature completeness | 92 | Existing features preserved; hunk restore and hooks deferred |
| Recovery safety | 95 | Original adversarial suite plus both-mode confirmation checks |
| Performance | 91 | Measured bounded workloads; no interactive latency guarantee |
| Documentation | 92 | Executable quickstart, branch-relative links, current screenshots |
| Installation | 92 | Isolated candidate packages; PyPI not published |

## Delivery and release decision

Existing branch codex/pixel-tui-v0.2.0 and [PR #1](https://github.com/muratkareem/timemachine/pull/1)
remain the review path. This pass starts after eccfc71. Commits follow actual
cohesive changes rather than artificially reaching a numerical target. Exact
final SHA, additional commit count, CI and build verification are on the PR.

Version 0.2.0 is prepared for final owner approval. Release artifacts are wheel,
source archive, SHA256SUMS and BUILD.json; BUILD.json identifies the precise
committed source. Clean double builds must agree. CI independently validates all
six macOS/Linux Python 3.12–3.14 combinations and reproducible artifacts. The final
handoff verifies CI and clean installs; no publication is inferred from preparation.

Classification: **RELEASE CANDIDATE, ready for owner acceptance and release decision**.
No known critical defect remains in the tested safety contract. Merge and release
remain explicitly unperformed; v0.1.0 stays unchanged. PyPI credentials/ownership
are unavailable. Optional future work: real-user studies, more terminal emulators,
native Windows, hunk recovery and automatic vendor hooks. Those are not claims of
current support. Bounds remain 1 MiB previews, 2,000 lines, 500 characters/line,
200 file rows/page and 500 recovery entries; larger reviews use CLI --preview.

## Owner acceptance (disposable project)

1. Install the pinned revision from INSTALL.md; run --version.
2. Follow QUICKSTART.md: init, verify no backup yet, run the Python example.
3. Open Simple mode; inspect hello.txt and its before/after diff.
4. Preview Undo, cancel once, then confirm; verify original bytes.
5. Confirm Redo; edit hello.txt manually; verify Undo refuses the conflict.
6. Open Help; switch Advanced/Simple; try Tab, 1/2/3 and light/dark themes.
7. Review the safety scope and final artifact provenance before approving release.
