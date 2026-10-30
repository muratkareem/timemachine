# Safety contract

TimeMachine protects selected regular-file bytes, relative names, POSIX permission
bits, symlink target text and directories (including empty directories). It does
not back up Git history/index, external targets, ownership, timestamps, ACLs,
xattrs, sparse extents or hardlink relationships. Hardlinked regular files and
special files are rejected, not silently flattened. Setuid/setgid/sticky file
modes are rejected. Case/Unicode-normalization collisions are rejected for portable
recovery. Symlinks are stored as links, never traversed; their targets may be
outside the root. Root itself must be a real directory. Root metadata is excluded.

Default exclusions at any depth: `.git`, `.timemachine.json`, `.venv`, `venv`,
`node_modules`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`.
All other tracked, untracked and ignored files are included, including secrets.
Excluded directories have no recovery guarantee. Status lists actual exclusions.
User exclusions are explicit glob patterns; removing optional defaults opts them
back in. `.git` and the project marker are always excluded. File limits and store
quota fail checkpoints rather than omitting protected content. Store is local and
private by default; this tool never uploads snapshots or executes shell strings.

Undo changes only PRE/POST differing paths. Current state must equal POST (or an
already restored PRE state); other changes are conflicts. All conflicts are found
before writes; unrelated edits survive. Redo requires the corresponding PRE
states. Directory removal refuses unexpected descendants. Arbitrary restore
previews all selected current/target differences and needs explicit confirmation;
later-created protected files may be deleted. Excluded children prevent deleting
their parent. No force override for conflicts. Git mismatch warnings require
acknowledgment; Git HEAD, refs, index and hooks are never repaired automatically.

Every restore has a recovery checkpoint and durable journal. Partial failures
retain both and report FAILED. Do not delete recovery artifacts. `doctor` reports
incomplete snapshots/runs/transactions; see RECOVERY.md for manual intervention.
Integrity errors stop affected operations. Garbage collection holds the writer
lock and retains every object referenced by any COMPLETE checkpoint. Checkpoints
referenced by runs/transactions, tagged or pinned cannot be deleted.

External editors/agents do not honor the lock. No-follow descriptor-relative
operations, repeated identity/hash validation and post-verification reduce races,
but cannot eliminate TOCTOU or provide a globally atomic multi-file restore.
Quiesce external writers before checkpoint/restore. Detached children may write
after POST; subsequent undo detects observable conflicts. Snapshot consistency
is two stable scans, not a filesystem freeze. An unrestricted malicious agent
with the same user permissions can destroy the store or alter Git metadata.
The wrapper is not a sandbox. Back up valuable data independently.

Unsupported Windows/network filesystem semantics are not claimed. fsync durability
is subject to filesystem/hardware behavior. Permission failures, disk exhaustion,
concurrent changes and unsupported entries fail clearly. Interrupted runs are
never silently undone. No PyPI publication or platform/CI success is implied by
source availability.
