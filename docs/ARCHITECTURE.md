# Architecture and storage formats

Python 3.12+ on POSIX (macOS/Linux). CLI: Typer/Rich; optional Textual UI.
Core services accept a Project and use no UI dependencies.

A project has an excluded `.timemachine.json` identity/config marker. A private
external store holds `project.json`, `metadata.sqlite3`, `objects/`, and a flock
file. The default store is under XDG_DATA_HOME or the macOS Application Support
TimeMachine directory, keyed by UUID. A moved root requires explicit rebind.
Custom stores inside the project, its ancestors, or Git metadata are refused.
The marker stores explicit exclusions, file limit and quota. Git ignore rules do
not change the protection scope. New catalogs use schema v2; manifests and checksummed JSON envelopes remain v1.
Schema v1 is readable, but writes require explicit `migrate`. Unknown versions
fail closed. Migration is additive and transactional.

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
stale lock ownership automatically; persisted run PIDs are diagnostic only.

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

Final v1 journals use a strict checksummed envelope (`version`, `kind`, `payload`,
`digest`), with SHA-256 of canonical payload JSON. Both immutable plans and each
mutable progress update are checked before recovery/verification/GC. Unsupported
or development-era unchecked journal formats fail closed and require manual
inspection with the original source version; there is no implicit trust-on-read
migration. Back up a complete store before any future explicit format migration.


Catalog v2 stores progress in `journal_steps`, keyed by transaction and sequence.
Each record is checksummed and includes the previous record's digest. A small
checksummed progress head (count and final digest) updates in the same SQLite
transaction as each append. Missing/reordered/changed steps fail verification.
Legacy v1 progress arrays remain readable. This removes quadratic JSON rewrites.
Recovery indexes removed/created paths once rather than rescanning step arrays.

`migrate --preview`, then `migrate --yes` under the project writer lock upgrades
v1 catalogs. A private SQLite catalog backup is fsynced first. It is for immediate
catalog inspection/rollback while quiescent, not an independent whole-store backup:
future user-authorized deletion/GC can remove old objects. Copy the entire store
for long-term recovery. Failure rolls DDL and user_version back together.
