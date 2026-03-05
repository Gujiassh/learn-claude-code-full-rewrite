from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class TaskItem:
    task_id: str
    title: str
    deps: list[str] = field(default_factory=list)
    status: str = "pending"
    assignee: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


class TaskBoard:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, TaskItem] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._tasks = {}
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        rows = list(payload.get("tasks", []))
        tasks: dict[str, TaskItem] = {}
        for row in rows:
            item = TaskItem(
                task_id=str(row.get("task_id", "")),
                title=str(row.get("title", "")),
                deps=list(row.get("deps", [])),
                status=str(row.get("status", "pending")),
                assignee=str(row.get("assignee", "")),
                created_at=str(row.get("created_at", now_iso())),
                updated_at=str(row.get("updated_at", now_iso())),
            )
            if item.task_id:
                tasks[item.task_id] = item
        self._tasks = tasks

    def save(self) -> None:
        rows = [asdict(item) for item in self.list_tasks()]
        payload = {
            "updated_at": now_iso(),
            "task_count": len(rows),
            "tasks": rows,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list_tasks(self) -> list[TaskItem]:
        return sorted(self._tasks.values(), key=lambda item: item.created_at)

    def add_task(
        self, task_id: str, title: str, deps: list[str] | None = None
    ) -> TaskItem:
        task_key = task_id.strip()
        if not task_key:
            raise ValueError("task_id is required")
        if task_key in self._tasks:
            raise ValueError(f"task_id exists: {task_key}")
        item = TaskItem(task_id=task_key, title=title.strip(), deps=list(deps or []))
        self._tasks[item.task_id] = item
        self.save()
        return item

    def get(self, task_id: str) -> TaskItem | None:
        return self._tasks.get(task_id)

    def complete(self, task_id: str) -> TaskItem:
        item = self._tasks.get(task_id)
        if item is None:
            raise KeyError(task_id)
        item.status = "completed"
        item.updated_at = now_iso()
        self.save()
        return item

    def claim_next_ready(self, assignee: str) -> TaskItem | None:
        worker = assignee.strip()
        if not worker:
            raise ValueError("assignee is required")

        for item in self.list_tasks():
            if item.status != "pending":
                continue
            ready = True
            for dep in item.deps:
                dep_task = self._tasks.get(dep)
                if dep_task is None or dep_task.status != "completed":
                    ready = False
                    break
            if not ready:
                continue
            item.status = "in_progress"
            item.assignee = worker
            item.updated_at = now_iso()
            self.save()
            return item
        return None
