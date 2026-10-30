"""Strict, versioned immutable filesystem values."""

import hashlib
import json
import re
import stat
from dataclasses import asdict, dataclass
from typing import Any

from .errors import IntegrityError
from .security import encode, safe_path


@dataclass(frozen=True)
class Entry:
    kind: str
    mode: int
    size: int = 0
    digest: str | None = None
    target: str | None = None

    def validate(self) -> None:
        if (
            type(self.mode) is not int
            or self.mode < 0
            or self.mode > 0o777
            or type(self.size) is not int
            or self.size < 0
        ):
            raise IntegrityError("Invalid entry mode/size")
        if self.kind == "file":
            if not isinstance(self.digest, str) or not re.fullmatch(r"[a-f0-9]{64}", self.digest):
                raise IntegrityError("Invalid object digest")
            if self.target is not None:
                raise IntegrityError("File has link target")
        elif self.kind == "symlink":
            if (
                not isinstance(self.target, str)
                or not self.target
                or "\x00" in self.target
                or self.digest is not None
                or self.size != 0
                or self.mode != 0o777
            ):
                raise IntegrityError("Invalid symlink")
        elif self.kind == "directory":
            if self.digest is not None or self.target is not None or self.size != 0:
                raise IntegrityError("Invalid directory entry")
        else:
            raise IntegrityError("Unknown entry type")

    @classmethod
    def from_dict(cls, value: Any) -> "Entry":
        try:
            entry = cls(**value)
            entry.validate()
            return entry
        except (TypeError, ValueError) as exc:
            raise IntegrityError("Malformed manifest entry") from exc


Manifest = dict[str, Entry]


def dump_manifest(entries: Manifest) -> bytes:
    return encode({"version": 1, "entries": {p: asdict(e) for p, e in entries.items()}})


def load_manifest(data: bytes, digest: str) -> Manifest:
    if hashlib.sha256(data).hexdigest() != digest:
        raise IntegrityError("Manifest hash mismatch")
    try:
        value = json.loads(data)
        if set(value) != {"version", "entries"} or value["version"] != 1:
            raise IntegrityError("Unsupported manifest format")
        entries = {safe_path(p): Entry.from_dict(e) for p, e in value["entries"].items()}
        for path in entries:
            parent = path.rpartition("/")[0]
            if parent and (parent not in entries or entries[parent].kind != "directory"):
                raise IntegrityError("Manifest parent is missing or not a directory")
        return entries
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise IntegrityError("Malformed manifest") from exc


def fingerprint(info: Any) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


def mode_bits(mode: int) -> int:
    if stat.S_IMODE(mode) & 0o7000:
        raise IntegrityError("Special permission bits are unsupported")
    return stat.S_IMODE(mode)
