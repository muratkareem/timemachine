# Publication drafts — approval required

Replace personal wording if it does not reflect your own experience. Check each
community's current rules, self-promotion policy and title limits before posting.
Do not cross-post identical copy or claim live-agent footage for the replay demo.

## Hacker News / Show HN

**Title:** Show HN: TimeMachine – local checkpoints and undo for coding-agent sessions

**URL:** https://github.com/muratkareem/timemachine

**First comment:**

I built TimeMachine to make changes from coding-agent sessions easier to inspect
and recover. Wrap an executable with `timemachine run -- ...`; it records selected
local files before and after the command. You can review the diff, preview undo,
undo the recorded session, and redo it. A newer edit to an affected file causes
recovery to refuse rather than overwrite it.

It runs locally on macOS/Linux with Python 3.12–3.14. No account or daemon; Git
history and the index stay outside recovery. Selected untracked and ignored files
are included, which also means local snapshots may contain secrets.

It is not a sandbox or an atomic whole-project backup. Stop other writers before
recovery and keep independent backups. The repository includes real CLI output
and UI captures; the short demo captures a real Codex tool edit with a coordinated wait command. v0.2.0 is available as a GitHub wheel, not on PyPI.

I'd welcome feedback on the recovery review and which safety limitations need
clearer explanation.

## Reddit / developer community

**Title:** I made a local checkpoint/undo tool for coding-agent sessions (Python, macOS/Linux)

TimeMachine wraps an agent command, saves selected files before and after it, and
lets you review the diff and undo or redo the session. It checks affected files
before recovery: a conflicting newer edit is refused.

The MIT-licensed CLI and terminal UI run locally, without an account or daemon.
Git remains your version-control system; this adds session-level recovery for
selected file state, including untracked/ignored files within scope.

Limits: no native Windows support, no hunk-level recovery, and no protection from
a malicious agent with your user permissions. External writers must be stopped;
restore is not globally atomic. Local snapshots can contain secrets.

Source, installation and a reproducible demo:
https://github.com/muratkareem/timemachine

Disclosure: I'm the author. The demo uses actual TimeMachine output around a real Codex tool edit. I'd especially value feedback on whether preview and
conflict messages make the recovery scope clear.

## LinkedIn

Coding-agent changes are easier to trust when you can inspect and recover them.

I've released TimeMachine v0.2.0: a local CLI and terminal UI that records selected
files around an agent command, shows the diff, and supports previewed undo/redo.
Conflict checks refuse to overwrite newer edits to affected files.

MIT-licensed. Python 3.12–3.14. macOS/Linux. No TimeMachine account or daemon.
It complements Git; it is not a sandbox or a replacement for independent backups.

The repository includes installation instructions, real UI captures and a
reproducible recovery demo (actual CLI output around a Codex tool edit).

I'd welcome feedback from developers using coding agents:
https://github.com/muratkareem/timemachine

## X / Twitter

TimeMachine v0.2.0: local checkpoints + previewed undo/redo for coding-agent sessions. Review the diff; conflict checks refuse newer edits. MIT, macOS/Linux, Python 3.12+. Not a sandbox or universal backup.
https://github.com/muratkareem/timemachine
