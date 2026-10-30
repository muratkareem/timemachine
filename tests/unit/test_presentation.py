import pytest

from timemachine.checkpoint import checkpoint
from timemachine.errors import TimeMachineError
from timemachine.presentation import safe, size
from timemachine.ui_data import Workspace, resolve_checkpoint


def test_safe_unicode_controls():
    assert safe("файл[red]\x1b\n\u202e") == "файл[red]\\u001b\\u000a\\u202e"
    assert safe("x\ny", multiline=True) == "x\ny"
    assert size(1024) == "1.0 KiB"


def test_lazy_navigation_no_source_scan(project, monkeypatch):
    (project.root / "x").write_text("before")
    with project.lock():
        a = checkpoint(project)
        (project.root / "x").write_text("after")
        checkpoint(project)

    def forbidden(*args, **kwargs):
        raise AssertionError("Navigation must not scan source files")

    monkeypatch.setattr("timemachine.scanner.scan", forbidden)
    workspace = Workspace(project)
    events = workspace.timeline(1)
    assert len(events) == 1
    assert workspace.selection(events[0])["files"][0]["change"] == "modified"
    assert workspace.checkpoint(a) is workspace.checkpoint(a)
    assert resolve_checkpoint(project, a[:8]) == a
    with pytest.raises(TimeMachineError):
        resolve_checkpoint(project, "%")


def test_timeline_headers_do_not_read_manifest_payload(project):
    from timemachine.metadata import connect

    with project.lock():
        identifier = checkpoint(project)
    with connect(project.store) as db:
        db.execute("UPDATE checkpoints SET manifest=? WHERE id=?", (b"invalid payload", identifier))
    assert Workspace(project).timeline()[0]["id"] == identifier
    # Selecting still validates it. Metadata browsing never certifies corrupt data.
    with pytest.raises(TimeMachineError):
        Workspace(project).selection(Workspace(project).timeline()[0])


def test_ambiguous_prefix_and_paged_timeline(project):
    from timemachine.metadata import connect

    with project.lock():
        first = checkpoint(project, "one")
        second = checkpoint(project, "two")
    with connect(project.store) as db:
        db.execute("UPDATE checkpoints SET id=? WHERE id=?", ("abcd" + "0" * 28, first))
        db.execute("UPDATE checkpoints SET id=? WHERE id=?", ("abcd" + "1" * 28, second))
    with pytest.raises(TimeMachineError, match="Ambiguous"):
        resolve_checkpoint(project, "abcd")
    assert len(Workspace(project).timeline(1, 1)) == 1
    assert Workspace(project).timeline(1, 2) == []
