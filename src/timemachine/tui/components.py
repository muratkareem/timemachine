"""Small original terminal components. All project text is literal and escaped."""

from typing import Any

from rich.text import Text
from textual.widgets import Static

from ..presentation import safe, short


class SaveSlot(Static):
    def show(self, label: str, value: str, detail: str, colors: dict[str, str], role: str) -> None:
        text = Text(safe(label) + "\n", style=colors["muted"])
        text.append(safe(value) + "\n", style="bold " + colors[role])
        text.append(safe(detail), style=colors["text"])
        self.update(text)


def archive_record(item: dict[str, Any], colors: dict[str, str]) -> tuple[Text, Text]:
    category, status = item["category"], item["status"]
    role = "error" if status not in ("COMPLETE", "RECOVERED") else "protected"
    marker, label = "S", "SAVE"
    if category == "run":
        label = item["state"].upper()
        marker = "<" if label == "UNDONE" else ">"
        if status not in ("COMPLETE", "LATE_POST"):
            marker, label, role = "!", status, "error"
        elif label == "UNDONE":
            role = "warning"
        elif label == "INVALIDATED":
            role = "muted"
        else:
            role = "success"
    elif category == "restore":
        marker, label = "R", item["kind"].upper()
    elif item.get("pinned"):
        marker, label, role = "*", "PINNED", "warning"
    elif item.get("kind") in ("pre", "post", "recovery"):
        label = item["kind"].upper()
    stamp = Text(item["created"][5:16].replace("T", " ") + "\n", style=colors["muted"])
    stamp.append(f"[{marker}] {label}", style=colors[role])
    title = item.get("message") or item.get("agent") or item.get("kind") or "Checkpoint"
    body = Text(safe(title) + "\n", style="bold " + colors["text"])
    detail = "#" + short(item["id"]) + " / " + status
    if category == "run":
        detail += " / PRE+POST" if item.get("post") else " / PRE only"
        detail += f" / exit {item['exit_code']}"
    body.append(detail, style=colors["muted"])
    return stamp, body
