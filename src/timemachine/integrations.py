"""Executable discovery only. No invented agent hooks or automatic agent launch."""

import shutil

from .runner import KNOWN_AGENTS


def capabilities() -> dict[str, dict[str, str | bool]]:
    return {
        agent: {
            "available": shutil.which(agent) is not None,
            "wrapper": f"timemachine run -- {agent}",
            "integration": "generic subprocess; no hooks",
        }
        for agent in sorted(KNOWN_AGENTS)
    }
