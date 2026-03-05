from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .task_board import TaskBoard


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class TeamMessage:
    message_id: str
    msg_type: str
    sender: str
    receiver: str
    payload: dict[str, Any]
    created_at: str


class TeamMailbox:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._cursor: dict[str, int] = {}

    def _path(self, receiver: str) -> Path:
        return self.root / f"{receiver}.jsonl"

    def send(
        self, msg_type: str, sender: str, receiver: str, payload: dict[str, Any]
    ) -> TeamMessage:
        message = TeamMessage(
            message_id=str(uuid4()),
            msg_type=msg_type,
            sender=sender,
            receiver=receiver,
            payload=payload,
            created_at=now_iso(),
        )
        line = json.dumps(asdict(message), ensure_ascii=False)
        path = self._path(receiver)
        with path.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")
        return message

    def receive_new(self, receiver: str) -> list[TeamMessage]:
        path = self._path(receiver)
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        start = self._cursor.get(receiver, 0)
        rows = lines[start:]
        self._cursor[receiver] = len(lines)
        out: list[TeamMessage] = []
        for row in rows:
            data = json.loads(row)
            out.append(
                TeamMessage(
                    message_id=str(data.get("message_id", "")),
                    msg_type=str(data.get("msg_type", "")),
                    sender=str(data.get("sender", "")),
                    receiver=str(data.get("receiver", "")),
                    payload=dict(data.get("payload", {})),
                    created_at=str(data.get("created_at", "")),
                )
            )
        return out


class TeamCoordinator:
    def __init__(
        self, board: TaskBoard, mailbox: TeamMailbox, lead_name: str = "lead"
    ) -> None:
        self.board = board
        self.mailbox = mailbox
        self.lead_name = lead_name

    def assign_next(self, worker: str) -> dict[str, str] | None:
        task = self.board.claim_next_ready(worker)
        if task is None:
            return None
        self.mailbox.send(
            msg_type="task_assigned",
            sender=self.lead_name,
            receiver=worker,
            payload={"task_id": task.task_id, "title": task.title},
        )
        return {"task_id": task.task_id, "title": task.title}

    def report_done(self, worker: str, task_id: str) -> None:
        task = self.board.complete(task_id)
        self.mailbox.send(
            msg_type="task_completed",
            sender=worker,
            receiver=self.lead_name,
            payload={"task_id": task.task_id, "title": task.title},
        )
