# Security and data-loss reports

Treat data-integrity defects as security-sensitive. Stop affected restore/GC
operations, preserve the external store and journal, and stop external writers.
Do not post secrets, snapshot contents or raw command arguments in public issues.
Use the repository's private vulnerability reporting if enabled; otherwise open
a minimal issue requesting a private maintainer channel without sensitive data.
No response-time SLA or enabled private-reporting facility is claimed.

TimeMachine is a local filesystem recovery tool, not a sandbox. A same-user
malicious agent can access or destroy its external store. Restrictive permissions
protect against other ordinary users, not unrestricted owner processes. Filesystem
races against hostile concurrent writers cannot be eliminated. Do not run as root.

Never upload the snapshot store for diagnostics. Tests use synthetic temp projects;
share only a minimal reproduction, tool/Python/OS versions, sanitized error types
and journal/checkpoint IDs. See docs/SAFETY.md for scope and unsupported metadata.
