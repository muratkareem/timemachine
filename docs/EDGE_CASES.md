# Verified behavior and limits by edge case

| Case | Behavior and evidence |
| --- | --- |
| Add/delete/rename/move/multiple edits | Exact PRE/POST path differences; rename treated as delete+add; E2E synthetic agent, redo tests |
| Empty/binary/Unicode/odd names | Bytes and empty directories captured; escaped JSON/text previews; snapshot/diff/property tests |
| Modes | Regular and directory POSIX bits restored; unsupported special bits rejected; mode/type-transition tests |
| Symlinks/link attacks | Opaque targets, no traversal; parent substitution refuses; outside targets unchanged in safety tests |
| Hardlinks | st_nlink != 1 rejected; no unsupported relationship claim |
| Permission denied | Checkpoint fails INCOMPLETE; deterministic read-denial injection tested; OS permission behavior varies |
| Concurrent writes | Stable reads/double scans, inode validation, per-project flock; observed races and contention tested; no universal TOCTOU protection |
| Partial snapshot/full disk | INCOMPLETE marker retained; fsync/full-disk injections tested; never selected as complete |
| Interrupted restore | Journal/recovery checkpoint retained; later-edit refusal and explicit recovery tested |
| Corrupt manifest/blob | Hash/schema/duplicate-key/portable-collision validation; corruption blocks restore/verify/GC |
| Large files/repositories | Streaming bytes; size/quota failure; tested 2 MiB file plus 150 entries; 200-file measured baseline; no million-file claim |
| Case-insensitive filesystems | Casefold/NFC collisions refused; reserved Git/marker names casefolded; malicious-manifest tests |
| Nested repositories/submodules | Their .git entries always excluded; ordinary nested worktree bytes included; no submodule Git history recovery |
| Ignored valuable files | Included unless explicit exclusion; snapshot and E2E tests |
| Dirty/staged Git state | Original index/HEAD/refs preserved when agent leaves Git alone; Git E2E checks exact fingerprint |
| Agent Git commits/refs/index | Mismatch warnings; filesystem undo leaves changed Git metadata intact; E2E agent commit test |
| User edits between run/undo | Differing affected paths conflict before mutation; unrelated edits survive |
| Redo conflicts/invalidation | Linear stack; new successful run/restore invalidates; roundtrip/conflict tests |
| Moved root | Refused until explicit rebind; CLI rebind tested |
| External modifications | Outside-root content not protected; symlink outside-target test; no sandbox claim |
| Lingering children | Direct child only; delayed write after POST triggers undo conflict in subprocess test |
| Signals/crashes | SIGINT/SIGTERM forwarded and POST attempted; SIGKILL leaves PRE/stale run, blocks mutations; explicit late finish-run tested |
| Excluded children | Cannot delete their parent directory silently; nonempty rmdir fails safely or planning refuses |
| Sparse files/ACL/xattr/ownership/time | Logical file bytes only; these attributes are not captured or restored |
| Interrupted GC | Reference-safe idempotent unlink; restart/dry-run tests |
| New edits while TUI modal open | Frozen expected states/run ID refuse stale confirmation; headless pilot tests |

Tests detect specific injected/observed races, not all schedules or hardware faults.
Local results establish the current macOS/Python environment only; CI results must
be read separately. Network filesystems and Windows are not supported claims.
