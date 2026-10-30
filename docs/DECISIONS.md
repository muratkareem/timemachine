# Decisions

- v1 uses stdlib SQLite, SHA-256 and flock; no daemon/network service.
- Identity marker is the only init change inside source; store is external.
- Include Git-ignored data by default except explicitly listed regenerable trees.
- Reject hardlinks/special files and portable-name collisions rather than making
  inaccurate recovery claims. Symlinks are opaque metadata.
- Use descriptor-relative POSIX operations; document external-writer races.
- Retain all run/recovery references; manual deletion and GC precede automatic
  retention. Advanced watch/export/compression require separate evidence.
