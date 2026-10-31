"""Versioned checksummed journals: corruption must not widen recovery authority."""

import hashlib
import json
from typing import Any

from .errors import IntegrityError
from .models import Entry, strict_pairs
from .security import encode, safe_path


def pack(kind: str, payload: Any) -> str:
    return encode(
        {
            "version": 1,
            "kind": kind,
            "payload": payload,
            "digest": hashlib.sha256(encode(payload)).hexdigest(),
        }
    ).decode()


def unpack(raw: str, kind: str) -> Any:
    try:
        value = json.loads(raw, object_pairs_hook=strict_pairs)
        if (
            not isinstance(value, dict)
            or set(value) != {"version", "kind", "payload", "digest"}
            or type(value["version"]) is not int
            or value["version"] != 1
            or value["kind"] != kind
            or value["digest"] != hashlib.sha256(encode(value["payload"])).hexdigest()
        ):
            raise IntegrityError(
                "Unsupported or corrupted journal; preserve store, inspect manually"
            )
        return value["payload"]
    except (ValueError, TypeError, KeyError) as exc:
        raise IntegrityError("Malformed journal; preserve store, inspect manually") from exc


def read_plan(raw: str) -> dict[str, Any]:
    value = unpack(raw, "plan")
    if (
        not isinstance(value, dict)
        or set(value) != {"changes", "warnings", "change_count"}
        or not isinstance(value["changes"], list)
        or not isinstance(value["warnings"], list)
        or not all(isinstance(w, str) for w in value["warnings"])
        or type(value["change_count"]) is not int
        or value["change_count"] != len(value["changes"])
    ):
        raise IntegrityError("Invalid journal plan schema")
    paths = set()
    for change in value["changes"]:
        if not isinstance(change, dict) or set(change) != {"path", "expected", "target"}:
            raise IntegrityError("Invalid journal change schema")
        path = safe_path(change["path"])
        if path in paths:
            raise IntegrityError("Duplicate journal path")
        paths.add(path)
        for key in ("expected", "target"):
            if change[key] is not None:
                Entry.from_dict(change[key])
    return value


def read_progress(raw: str) -> list[dict[str, str]]:
    value = unpack(raw, "progress")
    if not isinstance(value, list):
        raise IntegrityError("Invalid journal progress")
    for step in value:
        if (
            not isinstance(step, dict)
            or set(step) != {"path", "action", "state"}
            or step["action"] not in ("remove", "write", "directory", "mode")
            or step["state"] not in ("before", "after")
        ):
            raise IntegrityError("Invalid journal step")
        safe_path(step["path"])
    return value


def read_transaction_progress(db: Any, row: Any) -> list[dict[str, str]]:
    """Read legacy v1 arrays or verify v2 chained append-only steps."""
    try:
        value = json.loads(row["progress"], object_pairs_hook=strict_pairs)
        if not isinstance(value, dict):
            raise IntegrityError("Malformed progress envelope")
    except (ValueError, TypeError) as exc:
        raise IntegrityError("Malformed progress envelope") from exc
    if value.get("kind") == "progress":
        return read_progress(row["progress"])
    head = unpack(row["progress"], "progress-head")
    if (
        not isinstance(head, dict)
        or set(head) != {"count", "digest"}
        or type(head["count"]) is not int
        or head["count"] < 0
    ):
        raise IntegrityError("Invalid progress head")
    previous = ""
    result: list[dict[str, str]] = []
    for record in db.execute(
        "SELECT sequence,record FROM journal_steps WHERE transaction_id=? ORDER BY sequence",
        (row["id"],),
    ):
        step = unpack(record["record"], "step")
        if (
            not isinstance(step, dict)
            or set(step) != {"sequence", "previous", "path", "action", "state"}
            or step["sequence"] != len(result) + 1
            or record["sequence"] != step["sequence"]
            or step["previous"] != previous
        ):
            raise IntegrityError("Broken recovery journal sequence")
        item = {key: step[key] for key in ("path", "action", "state")}
        read_progress(pack("progress", [item]))
        result.append(item)
        previous = hashlib.sha256(record["record"].encode()).hexdigest()
    if len(result) != head["count"] or previous != head["digest"]:
        raise IntegrityError("Recovery journal head mismatch")
    return result


def append_step(db: Any, identifier: str, path: str, action: str, state: str) -> None:
    row = db.execute("SELECT progress FROM transactions WHERE id=?", (identifier,)).fetchone()
    head = unpack(row["progress"], "progress-head")
    sequence = head["count"] + 1
    record = pack(
        "step",
        {
            "sequence": sequence,
            "previous": head["digest"],
            "path": safe_path(path),
            "action": action,
            "state": state,
        },
    )
    db.execute(
        "INSERT INTO journal_steps(transaction_id,sequence,record) VALUES(?,?,?)",
        (identifier, sequence, record),
    )
    db.execute(
        "UPDATE transactions SET status='APPLYING',progress=? WHERE id=?",
        (
            pack(
                "progress-head",
                {"count": sequence, "digest": hashlib.sha256(record.encode()).hexdigest()},
            ),
            identifier,
        ),
    )
