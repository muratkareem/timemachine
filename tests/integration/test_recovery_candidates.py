import sys

from timemachine.metadata import connect
from timemachine.operations import redo_plan, undo, undo_plan
from timemachine.runner import run
from timemachine.ui_data import Workspace


def test_ui_candidates_follow_backend_stack_order_without_live_scan(project, monkeypatch):
    (project.root / "x").write_text("before")
    with project.lock():
        first = run(project, [sys.executable, "-c", "pass"], project.root)
        second = run(project, [sys.executable, "-c", "pass"], project.root)
        expected_undo, _ = undo_plan(project)
        assert expected_undo["id"] == second["run"]
        undo(project)
        expected_redo, _ = redo_plan(project)
        assert expected_redo["id"] == second["run"]

    def forbidden(*args, **kwargs):
        raise AssertionError("Catalog navigation must not scan live files")

    monkeypatch.setattr("timemachine.scanner.scan", forbidden)
    state = Workspace(project).dashboard()
    assert state["undo"]["id"] == first["run"]
    assert state["redo"]["id"] == expected_redo["id"]
    assert not state["blocked"]


def test_unfinished_older_run_blocks_both_actions(project):
    with project.lock():
        first = run(project, [sys.executable, "-c", "pass"], project.root)
        run(project, [sys.executable, "-c", "pass"], project.root)
    with connect(project.store) as db:
        db.execute("UPDATE runs SET status='FINALIZING' WHERE id=?", (first["run"],))
    state = Workspace(project).dashboard()
    assert state["undo"] is None and state["redo"] is None
    assert "Unfinished session" in state["blocked"]
