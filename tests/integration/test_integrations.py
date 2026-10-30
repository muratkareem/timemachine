import shutil

import pytest

from timemachine.integrations import capabilities
from timemachine.runner import run


def test_capability_detection(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: "/bin/codex" if name == "codex" else None)
    result = capabilities()
    assert result["codex"]["available"] is True
    assert result["aider"]["available"] is False
    assert all(value["integration"] == "generic subprocess; no hooks" for value in result.values())


@pytest.mark.parametrize("agent", ["codex", "claude", "gemini", "aider"])
def test_available_agent_help_smoke(project, agent):
    if not shutil.which(agent):
        pytest.skip(f"{agent} executable not installed; no live integration claim")
    with project.lock():
        result = run(project, [agent, "--help"], project.root)
    assert result["exit_code"] == 0 and result["post"]
