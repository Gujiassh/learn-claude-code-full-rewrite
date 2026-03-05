from __future__ import annotations

from pathlib import Path

from src.full_rewrite.api import RewriteAPI


def test_api_task_flow(tmp_path: Path) -> None:
    api = RewriteAPI(tmp_path)
    api.add_task("t1", "task-1")
    claim = api.claim_task("worker")
    assert claim is not None
    assert claim["task_id"] == "t1"

    done = api.complete_task("t1")
    assert done["status"] == "completed"


def test_api_context_and_observability(tmp_path: Path) -> None:
    api = RewriteAPI(tmp_path)
    row = api.append_context("user", "hello")
    assert row["rows"] >= 1

    exported = api.export_observability()
    assert Path(exported["json"]).exists()
    assert Path(exported["markdown"]).exists()

    snap = api.snapshot()
    assert "tasks" in snap
    assert "observability" in snap
