# Production-completion audit

Baseline inspected: 34b487b, clean main, MIT license preserved. Historical results
are checked by a fresh local suite rather than assumed. Work order: audit/fixes,
measured scalability, installation/release artifacts, optional agent opt-in,
acceptance scenarios, clean builds and supported-platform CI, final publication
approval if required. Windows and hunk recovery are separate feasibility gates.

Initial actionable findings:

- CLI undo/redo and explicit partial recovery can rebuild a reviewed plan after
  confirmation. Freeze the reviewed intent through execution; refuse later state
  changes rather than adding unreviewed changes.
- Config/identity JSON shape validation is incomplete (e.g. a top-level list can
  raise an unexpected exception). Reject duplicate keys and invalid types cleanly.
- Object quota accounting enumerates every object for each newly captured file,
  producing quadratic work. Measure and optimize without bypassing verification.
- Full progress JSON is rewritten for every step; measure its scaling separately
  and retain crash-safe semantics if changing it.
- SQLite validation should include foreign-key/referenced checkpoint health;
  malformed metadata must stop GC before any objects are removed.

Audit limitations: same-user malicious processes can access the private store;
external filesystem writers do not honor TimeMachine locks. Descriptor-relative
checks reduce observable races, not global atomicity or hostile-race immunity.
No independent third-party certification is claimed by this internal audit.

## Confirmed and corrected: reviewed-intent widening

Three new tests reproduced failures on 34b487b: an already-restored path could
become a newly authorized CLI undo write after consent; Git state could change
after preview without renewed acknowledgment; an empty plan skipped all revalidation.
Corrected with ephemeral frozen observations (including already-target paths),
root/ancestor identity and Git-context checks, and passing the actual reviewed
plan through CLI undo/redo/recover. The persisted v1 journal shape is unchanged.
Parent descriptor identity is now checked after opening, near mutation as well.
Additional adversarial recovery-consent and parent-swap tests pass. External
uncooperative races still cannot be eliminated globally.

## Corrected: malformed metadata and unsafe collection authority

Bounded, no-follow, duplicate-key-rejecting JSON reads now validate project/identity
objects and enforce private real store directories. Catalog validation rejects
unknown/contradictory checkpoint states, invalid tags/pins, invalid run ordering,
unfinished references, and missing foreign-key targets. Verify/GC run SQLite and
reference health checks before object deletion. Errors preserve the store.
Focused config/catalog/retention tests: 26 passed. No migration or version bump
of valid v1 manifests is required.
