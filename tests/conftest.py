from pathlib import Path

import pytest

from timemachine.project import Project


@pytest.fixture
def project(tmp_path: Path) -> Project:
    root = tmp_path / "project"
    root.mkdir()
    return Project.init(root, tmp_path / "store")
