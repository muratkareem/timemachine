"""Read model for UI navigation. Never scans or mutates the project filesystem."""

import json
import re
import threading
from collections import OrderedDict
from typing import Any

from .checkpoint import get_checkpoint
from .diff import changed, describe
from .errors import TimeMachineError
from .metadata import connect
from .project import Project


def resolve_checkpoint(project: Project, identifier: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{4,32}", identifier):
        raise TimeMachineError(
            "Use a full checkpoint ID or a unique prefix of at least 4 hex digits"
        )
    with connect(project.store) as db:
        rows = db.execute(
            "SELECT id FROM checkpoints WHERE substr(id,1,?)=? LIMIT 2",
            (len(identifier), identifier.lower()),
        ).fetchall()
    if len(rows) != 1:
        raise TimeMachineError(
            "Ambiguous checkpoint prefix; use more digits"
            if rows
            else "Unknown checkpoint; use timemachine list"
        )
    return str(rows[0][0])


class Workspace:
    def __init__(self, project: Project):
        self.project = project
        self.cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()

    def checkpoint(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            if identifier not in self.cache:
                self.cache[identifier] = get_checkpoint(self.project, identifier)
                if len(self.cache) > 8:
                    self.cache.popitem(last=False)
            self.cache.move_to_end(identifier)
            return self.cache[identifier]

    def reset(self) -> None:
        with self._lock:
            self.cache.clear()

    def timeline(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with connect(self.project.store) as db:
            rows = db.execute(
                """
                SELECT 'checkpoint' AS category,id,created FROM checkpoints
                WHERE id NOT IN (SELECT pre FROM runs UNION
                    SELECT post FROM runs WHERE post IS NOT NULL)
                UNION ALL SELECT 'run',id,created FROM runs
                UNION ALL SELECT 'restore',id,created FROM transactions
                ORDER BY created DESC LIMIT ? OFFSET ?
            """,
                (limit, offset),
            ).fetchall()
            details: dict[str, dict[str, Any]] = {}
            columns = {
                "checkpoint": ("checkpoints", "id,created,message,kind,status,pinned,tags"),
                "run": ("runs", "*"),
                "restore": ("transactions", "id,created,kind,status,recovery,run_id,error"),
            }
            for category, (table, fields) in columns.items():
                ids = [r["id"] for r in rows if r["category"] == category]
                if not ids:
                    continue
                placeholders = ",".join("?" for _ in ids)
                records = db.execute(
                    f"SELECT {fields} FROM {table} WHERE id IN ({placeholders})", ids
                ).fetchall()
                for record in records:
                    item = dict(record)
                    item["category"] = category
                    if category == "checkpoint":
                        item["tags"] = json.loads(item["tags"])
                    details[category + ":" + item["id"]] = item
            result = [details[r["category"] + ":" + r["id"]] for r in rows]
        return result

    def selection(self, event: dict[str, Any], anchor: str | None = None) -> dict[str, Any]:
        category = event["category"]
        if category == "restore":
            target = event["recovery"]
            base = anchor
        elif category == "run":
            target = event["post"] or event["pre"]
            base = anchor or (event["pre"] if event["post"] else None)
        else:
            target = event["id"]
            base = anchor
            if base is None:
                with connect(self.project.store) as db:
                    row = db.execute(
                        "SELECT id FROM checkpoints WHERE created<? AND status='COMPLETE' "
                        "ORDER BY created DESC LIMIT 1",
                        (event["created"],),
                    ).fetchone()
                if row:
                    base = row[0]
        after = self.checkpoint(target)["entries"]
        before = self.checkpoint(base)["entries"] if base else {}
        paths = changed(before, after) if base else sorted(after)
        files = [
            {
                "path": p,
                "change": describe(before.get(p), after.get(p)) if base else "saved",
                "before": before.get(p),
                "after": after.get(p),
            }
            for p in paths
        ]
        return {"target": target, "base": base, "files": files}
