from timemachine.checkpoint import checkpoint
from timemachine.diff import compare
from timemachine.history import history, show


def test_diff_metadata_binary_text_and_odd_names(project):
    path = project.root / "\x1b[31m"
    path.write_text("hello\n")
    with project.lock():
        before = checkpoint(project)
        path.write_text("world\n")
        (project.root / "binary").write_bytes(b"\0\xff")
        after = checkpoint(project)
    result = compare(project, before, after)
    assert result["change_count"] == 2
    assert "+world" in result["changes"][0]["diff"]
    assert "preview" in result["changes"][1]
    assert len(history(project)["checkpoints"]) == 2
    assert show(project, before)["entries"]["\x1b[31m"]["kind"] == "file"


def test_mode_only(project):
    p = project.root / "exec"
    p.write_bytes(b"a")
    with project.lock():
        a = checkpoint(project)
        p.chmod(0o755)
        b = checkpoint(project)
    assert compare(project, a, b)["changes"][0]["change"] == "metadata"
