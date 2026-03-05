from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .context_governance import ContextGovernor
from .observability import ObservabilityHub
from .task_board import TaskBoard


class RewriteAPI:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.board = TaskBoard(self.data_root / "task_board.json")
        self.context_path = self.data_root / "context.json"
        self.observability = ObservabilityHub()

    def add_task(
        self, task_id: str, title: str, deps: list[str] | None = None
    ) -> dict[str, str]:
        row = self.board.add_task(task_id, title, deps)
        self.observability.record("api.add_task", status="ok")
        return {"task_id": row.task_id, "status": row.status}

    def claim_task(self, assignee: str) -> dict[str, str] | None:
        row = self.board.claim_next_ready(assignee)
        if row is None:
            self.observability.record("api.claim_task", status="none")
            return None
        self.observability.record("api.claim_task", status="ok")
        return {"task_id": row.task_id, "assignee": row.assignee}

    def complete_task(self, task_id: str) -> dict[str, str]:
        row = self.board.complete(task_id)
        self.observability.record("api.complete_task", status="ok")
        return {"task_id": row.task_id, "status": row.status}

    def append_context(self, role: str, content: str) -> dict[str, int]:
        governor = ContextGovernor.load(self.context_path)
        governor.add(role, content)
        governor.save(self.context_path)
        self.observability.record("api.append_context", status="ok")
        return {"rows": len(governor.model_messages())}

    def export_observability(self) -> dict[str, str]:
        json_path = self.data_root / "metrics.json"
        md_path = self.data_root / "metrics.md"
        self.observability.save_json(json_path)
        self.observability.save_markdown(md_path)
        return {"json": str(json_path), "markdown": str(md_path)}

    def snapshot(self) -> dict[str, object]:
        tasks = [asdict(row) for row in self.board.list_tasks()]
        context = ContextGovernor.load(self.context_path).model_messages()
        summary = self.observability.summary()
        return {"tasks": tasks, "context": context, "observability": summary}


def main() -> int:
    api = RewriteAPI(Path.cwd() / ".rewrite_data")
    api.export_observability()
    print(json.dumps(api.snapshot(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
