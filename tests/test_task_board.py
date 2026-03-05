from __future__ import annotations

from pathlib import Path

import pytest

from src.full_rewrite.task_board import TaskBoard


def test_add_task_persists_to_disk(tmp_path: Path) -> None:
    board_path = tmp_path / "board.json"
    board = TaskBoard(board_path)

    board.add_task("t1", "build loop")

    reloaded = TaskBoard(board_path)
    item = reloaded.get("t1")
    assert item is not None
    assert item.title == "build loop"
    assert item.status == "pending"


def test_claim_respects_dependencies(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "a")
    board.add_task("b", "b", deps=["a"])

    claimed = board.claim_next_ready("worker-1")
    assert claimed is not None
    assert claimed.task_id == "a"

    blocked = board.claim_next_ready("worker-1")
    assert blocked is None


def test_complete_unblocks_dependent_task(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "a")
    board.add_task("b", "b", deps=["a"])

    claimed = board.claim_next_ready("worker-1")
    assert claimed is not None
    board.complete("a")

    next_claim = board.claim_next_ready("worker-2")
    assert next_claim is not None
    assert next_claim.task_id == "b"
    assert next_claim.assignee == "worker-2"


def test_duplicate_task_id_raises(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("dup", "one")

    with pytest.raises(ValueError):
        board.add_task("dup", "two")


def test_complete_requires_in_progress(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "a")

    with pytest.raises(ValueError):
        board.complete("a")


def test_complete_with_actor_enforces_assignee(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "a")
    board.claim_next_ready("worker-1")

    with pytest.raises(PermissionError):
        board.complete("a", actor="worker-2")

    row = board.complete("a", actor="worker-1")
    assert row.status == "completed"
