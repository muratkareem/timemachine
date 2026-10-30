"""Immutable validated restore intent. No filesystem mutations here."""

from dataclasses import asdict, dataclass
from typing import Any

from .diff import changed
from .errors import ConflictError
from .models import Entry, Manifest
from .project import Project
from .scanner import Scan, scan


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
    current = scan(project)
    return from_scan(current, expected, target, paths, warnings)


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
