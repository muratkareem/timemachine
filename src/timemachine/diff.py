"""Exact content/metadata comparisons with terminal-safe text previews."""

import difflib
import json
from dataclasses import asdict
from typing import Any

from .checkpoint import manifest
from .errors import TimeMachineError
from .metadata import connect
from .models import Entry, Manifest
from .objects import ObjectStore
from .project import Project
from .security import safe_path


def selected(path: str, selector: str | None) -> bool:
    if selector is None:
        return True
    safe_path(selector)
    return path == selector or path.startswith(selector + "/")


def changed(before: Manifest, after: Manifest, selector: str | None = None) -> list[str]:
    if selector is not None:
        safe_path(selector)
    return sorted(
        p
        for p in before.keys() | after.keys()
        if before.get(p) != after.get(p) and selected(p, selector)
    )


def describe(before: Entry | None, after: Entry | None) -> str:
    if before is None:
        return "added"
    if after is None:
        return "deleted"
    if before.kind != after.kind:
        return "type"
    if before.digest == after.digest and before.target == after.target:
        return "metadata"
    return "modified"


def text_content(objects: ObjectStore, entry: Entry | None) -> str | None:
    if entry is None:
        return ""
    if entry.kind != "file" or not entry.digest or entry.size > 1024 * 1024:
        return None
    data = objects.read(entry.digest, max_bytes=1024 * 1024)
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def compare(
    project: Project,
    a: str | None = None,
    b: str | None = None,
    selector: str | None = None,
    *,
    include_text: bool = True,
) -> dict[str, Any]:
    if a is None and b is None:
        with connect(project.store) as db:
            run = db.execute(
                "SELECT pre,post FROM runs WHERE post IS NOT NULL ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        if run is None:
            raise TimeMachineError("No completed run; specify two checkpoint IDs")
        a, b = run["pre"], run["post"]
    if a is None or b is None:
        raise TimeMachineError("Specify both checkpoint IDs, or neither for latest run")
    before, after = manifest(project, a), manifest(project, b)
    objects = ObjectStore(project.store, project.config["quota_bytes"])
    changes = []
    for path in changed(before, after, selector):
        old, new = before.get(path), after.get(path)
        item: dict[str, Any] = {
            "path": path,
            "change": describe(old, new),
            "before": asdict(old) if old else None,
            "after": asdict(new) if new else None,
        }
        if include_text:
            left, right = text_content(objects, old), text_content(objects, new)
            if left is None or right is None:
                item["preview"] = "Binary, non-UTF-8, directory, symlink or >1 MiB; metadata only"
            else:
                # Output adapter JSON-escapes all controls, including file contents.
                item["diff"] = "".join(
                    difflib.unified_diff(
                        left.splitlines(keepends=True),
                        right.splitlines(keepends=True),
                        fromfile=json.dumps(path) + " (before)",
                        tofile=json.dumps(path) + " (after)",
                    )
                )
        changes.append(item)
    return {"before": a, "after": b, "change_count": len(changes), "changes": changes}
