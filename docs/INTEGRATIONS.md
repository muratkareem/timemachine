# Agent integrations

TimeMachine wraps ordinary argv subprocesses. No agent-specific hooks, MCP API,
SDK, environment injection or account access is required by TimeMachine.
`timemachine agents --json` reports executable availability without launching agents.
The agents retain their own installation, authentication, permissions and billing.

```sh
timemachine run -- codex
timemachine run -- claude
timemachine run -- gemini
timemachine run -- aider
```

Generic wrapper examples follow the vendors' normal executable names. Only
installed tools can be smoke-tested; availability is not proof of an authenticated
coding session. Local audit found Codex CLI 0.166.0-alpha.5.1; `--help` and wrapped
`--help` were tested without an AI request. Claude/Gemini/Aider were absent, so
no live integration test is claimed. No undocumented hook APIs are implemented.

Codex's local `--help` confirms interactive default and `exec` noninteractive.
The official [Codex CLI documentation](https://developers.openai.com/codex/cli)
describes the terminal agent. Generic wrapping also works with ordinary CLI modes:
`timemachine run -- codex exec 'your task'`. This example requires the user's
existing agent credentials and is not executed by the test suite.

Vendor references checked during implementation (2026-10-30):
[Claude Code CLI](https://code.claude.com/docs/en/cli-reference),
[Gemini CLI](https://geminicli.com/docs/cli/),
[Aider usage](https://aider.chat/docs/usage.html).
Use each tool's current local `--help` for its own options.

The wrapper inherits current subdirectory, environment and all terminal descriptors.
It never invokes a shell, logs raw arguments or stores the environment. Agent output
is intentionally passed through unchanged; it may itself contain secrets. Shell
history is outside TimeMachine's control. Do not put secrets in checkpoint messages.

The lock is held until the direct child exits and POST is captured. An agent may
spawn detached children, use a daemon, change working directories or write outside
root. These actions are not sandboxed. A detached process can modify files after
POST; undo then refuses observable conflicts. Changes in other worktrees/external
paths are not captured. SIGINT/SIGTERM are forwarded; a foreground terminal may
also deliver them directly. An ignoring child may need manual termination. SIGKILL
cannot be finalized automatically; use doctor and an explicitly late finish-run.
Git history/index modifications are detected where observable, never reversed.
