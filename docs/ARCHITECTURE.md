# Architecture and format v1

Python 3.12+ on POSIX (macOS/Linux). CLI: Typer/Rich; optional Textual UI.
Core services accept a Project and use no UI dependencies.

A project has an excluded `.timemachine.json` identity/config marker. A private
external store holds `project.json`, `metadata.sqlite3`, `objects/`, and a flock
file. The default store is under XDG_DATA_HOME or the macOS Application Support
TimeMachine directory, keyed by UUID. A moved root requires explicit rebind.
Custom stores inside the project, its ancestors, or Git metadata are refused.
The marker stores explicit exclusions, file limit and quota. Git ignore rules do
not change the protection scope. Metadata schema and manifest schema are v1;
unknown versions fail closed. Future formats require an explicit migration.

Objects are SHA-256 named, immutable, fsynced temporary writes followed by rename.
SQLite uses WAL, synchronous FULL and transactions. A checkpoint is inserted as
INCOMPLETE before scanning. Its canonical JSON manifest and SHA-256 are committed
with COMPLETE only after objects are durable. Manifests live in SQLite, bytes in
objects. Integrity is checked on every manifest/object read. Unreferenced objects
from failed writes can be collected; incomplete checkpoints cannot be restored.

The scanner opens directory/file descriptors with O_NOFOLLOW, checks stat before
and after reads, and compares two full scans. This detects observed instability;
it is not a global point-in-time filesystem snapshot. A project flock serializes
cooperating writers (including an entire wrapped run); kernel release handles
stale lock ownership. Lock owner metadata is diagnostic only.

Runs persist PRE, POST, status, executable basename, exit code and Git context.
Raw command arguments and environment are never persisted. A linear operation
stack records applied/undone runs; a new successful run or restore clears redo.
Checkpoint-only activity does not invalidate redo. Referenced snapshots remain
retained. History includes checkpoints, runs and restore transactions.

Restore state machine: PLANNED -> PROTECTED -> APPLYING -> COMPLETE, or FAILED.
The immutable plan records paths, expected states, targets and Git warnings.
Validate all conflicts and target objects first; create a complete recovery
checkpoint; persist the plan and recovery ID; journal each step before mutation.
Revalidate paths immediately before descriptor-relative mutation, fsync files
and parent directories, then verify all selected target entries. Per-file replace
is atomic; multi-file operations are not. Pending/failed journals block subsequent
mutations except an explicit recovery operation. Recovery uses the recorded plan,
refuses any current state other than its expected/target states, and restores the
pre-transaction recovery snapshot with a new journal. No automatic rollback.
