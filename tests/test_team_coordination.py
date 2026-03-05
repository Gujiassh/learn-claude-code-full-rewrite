from __future__ import annotations

from pathlib import Path

import pytest

from src.full_rewrite.task_board import TaskBoard
from src.full_rewrite.team_coordination import TeamCoordinator, TeamMailbox


def test_assign_and_completion_flow(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "task-a")
    board.add_task("b", "task-b", deps=["a"])

    mailbox = TeamMailbox(tmp_path / "mail")
    coordinator = TeamCoordinator(board=board, mailbox=mailbox, lead_name="lead")

    assigned = coordinator.assign_next("worker-1")
    assert assigned is not None
    assert assigned["task_id"] == "a"

    worker_messages = mailbox.receive_new("worker-1")
    assert len(worker_messages) == 1
    assert worker_messages[0].msg_type == "task_assigned"

    coordinator.report_done("worker-1", "a")
    lead_messages = mailbox.receive_new("lead")
    assert len(lead_messages) == 1
    assert lead_messages[0].msg_type == "task_completed"

    assigned_next = coordinator.assign_next("worker-2")
    assert assigned_next is not None
    assert assigned_next["task_id"] == "b"


def test_assign_returns_none_when_no_ready_tasks(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "task-a", deps=["missing"])

    mailbox = TeamMailbox(tmp_path / "mail")
    coordinator = TeamCoordinator(board=board, mailbox=mailbox)

    assigned = coordinator.assign_next("worker")
    assert assigned is None


def test_receive_new_only_returns_incremental_messages(tmp_path: Path) -> None:
    mailbox = TeamMailbox(tmp_path / "mail")

    mailbox.send("task_assigned", "lead", "worker", {"task_id": "a"})
    first = mailbox.receive_new("worker")
    assert len(first) == 1

    second = mailbox.receive_new("worker")
    assert second == []

    mailbox.send("task_assigned", "lead", "worker", {"task_id": "b"})
    third = mailbox.receive_new("worker")
    assert len(third) == 1
    assert third[0].payload["task_id"] == "b"


def test_report_done_rejects_non_assignee(tmp_path: Path) -> None:
    board = TaskBoard(tmp_path / "board.json")
    board.add_task("a", "task-a")

    mailbox = TeamMailbox(tmp_path / "mail")
    coordinator = TeamCoordinator(board=board, mailbox=mailbox, lead_name="lead")
    coordinator.assign_next("worker-1")

    with pytest.raises(PermissionError):
        coordinator.report_done("worker-2", "a")


def test_mailbox_rejects_unsafe_receiver_name(tmp_path: Path) -> None:
    mailbox = TeamMailbox(tmp_path / "mail")

    with pytest.raises(ValueError):
        mailbox.send("task_assigned", "lead", "../worker", {"task_id": "a"})
