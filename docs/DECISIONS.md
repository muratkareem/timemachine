# Decisions

- v1 uses stdlib SQLite, SHA-256 and flock; no daemon/network service.
- Identity marker is the only init change inside source; store is external.
- Include Git-ignored data by default except explicitly listed regenerable trees.
- Reject hardlinks/special files and portable-name collisions rather than making
  inaccurate recovery claims. Symlinks are opaque metadata.
- Use descriptor-relative POSIX operations; document external-writer races.
- Retain all run/recovery references; manual deletion and GC precede automatic
  retention. Advanced watch/export/compression require separate evidence.
- M11: include a reproducible disposable benchmark and real CLI demo. Defer watch,
  export/import, compression and plugin APIs; their independent safety contracts
  and migration tests need a separate iteration. No stub commands or fake metrics.
- Preserve all journal object references, even completed ones, for conservative
  retention. Storage quotas fail explicitly; no automatic purge of run history.
- Core runner requires the main thread for POSIX signal forwarding; CLI meets it.
