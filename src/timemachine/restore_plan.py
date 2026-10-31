"""Immutable validated restore intent. No filesystem mutations here."""

from dataclasses import asdict, dataclass, replace
from typing import Any

from .diff import changed
from .errors import ConflictError
from .git_context import git_context
from .models import Entry, Manifest
from .project import Project
from .scanner import Scan, excluded, scan
from .security import encode


@dataclass(frozen=True)
class Change:
    path: str
    expected: Entry | None
    target: Entry | None

    def data(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Plan:
    changes: tuple[Change, ...]
    warnings: tuple[str, ...] = ()
    # Ephemeral consent observations, deliberately outside the durable v1 plan schema.
    observed: tuple[tuple[str, Entry | None], ...] = ()
    identities: tuple[tuple[str, int, int], ...] = ()
    git_fingerprint: bytes | None = None

    def data(self) -> dict[str, Any]:
        return {
            "changes": [c.data() for c in self.changes],
            "warnings": list(self.warnings),
            "change_count": len(self.changes),
        }


def make_plan(
    project: Project,
    expected: Manifest,
    target: Manifest,
    paths: list[str] | None = None,
    warnings: tuple[str, ...] = (),
) -> Plan:
    root_before = project.root.lstat()
    git_before = encode(git_context(project.root))
    current = scan(project)
    root_after = project.root.lstat()
    if (root_before.st_dev, root_before.st_ino) != (
        root_after.st_dev,
        root_after.st_ino,
    ) or git_before != encode(git_context(project.root)):
        raise ConflictError("Root or Git state changed during preview; preview again")
    selected_paths = paths if paths is not None else changed(expected, target)
    for path in selected_paths:
        target_entry = target.get(path)
        if (
            target_entry
            and target_entry.kind == "symlink"
            and project.config.get("symlink_policy", "record") == "reject"
        ):
            raise ConflictError(f"Symlink target refused by current policy: {path!r}")
        if excluded(project, path):
            raise ConflictError(f"Path is excluded by current policy: {path!r}")
    plan = from_scan(current, expected, target, paths, warnings)
    ancestors = set(selected_paths)
    for path in selected_paths:
        parent = path.rpartition("/")[0]
        while parent:
            ancestors.add(parent)
            parent = parent.rpartition("/")[0]
    identities = [("", root_after.st_dev, root_after.st_ino)]
    identities.extend(
        (p, current.identities[p][0], current.identities[p][1])
        for p in sorted(ancestors)
        if p in current.identities
    )
    return replace(
        plan,
        observed=tuple((p, current.entries.get(p)) for p in selected_paths),
        identities=tuple(identities),
        git_fingerprint=git_before,
    )


def from_scan(
    current: Scan,
    expected: Manifest,
    target: Manifest,
    paths: list[str] | None = None,
    warnings: tuple[str, ...] = (),
) -> Plan:
    changes = []
    conflicts = []
    for path in paths if paths is not None else changed(expected, target):
        actual, old, new = current.entries.get(path), expected.get(path), target.get(path)
        if actual != old and actual != new:
            conflicts.append(path)
        elif actual != new:
            changes.append(Change(path, actual, new))
    removing_dirs = {
        c.path
        for c in changes
        if c.expected
        and c.expected.kind == "directory"
        and (c.target is None or c.target.kind != "directory")
    }
    removing = {c.path for c in changes if c.target is None or c.path in removing_dirs}
    for directory in removing_dirs:
        for path in current.entries.keys() | set(current.excluded):
            if path.startswith(directory + "/") and path not in removing:
                conflicts.append(path)
    # A targeted child must have directory ancestors in the resulting tree.
    resulting = dict(current.entries)
    for change in changes:
        if change.target is None:
            resulting.pop(change.path, None)
        else:
            resulting[change.path] = change.target
    for change in changes:
        if change.target is None:
            continue
        parent = change.path.rpartition("/")[0]
        while parent:
            if parent not in resulting or resulting[parent].kind != "directory":
                conflicts.append(parent)
            parent = parent.rpartition("/")[0]
    if conflicts:
        raise ConflictError(f"Restore conflicts; no files changed: {sorted(set(conflicts))!r}")
    return Plan(tuple(changes), warnings)
