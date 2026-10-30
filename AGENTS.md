# TimeMachine development

Read docs/STATUS.md, docs/SAFETY.md and docs/DECISIONS.md before resuming.
Preserve the MIT license and existing history. Use coherent Conventional Commits.
Do not mutate developer data in tests: all mutation tests use temporary projects.
Never bypass restore conflicts, follow project symlinks, mutate Git metadata or
mark a partial snapshot/restore complete. Core services stay independent of UI.
Run focused pytest checks per slice and pytest, Ruff, mypy and build at final audit.
Update STATUS at milestone boundaries with commands, results and next work.
