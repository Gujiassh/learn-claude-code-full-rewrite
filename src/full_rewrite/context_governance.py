from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class ContextMessage:
    role: str
    content: str
    created_at: str


class ContextGovernor:
    def __init__(self, max_recent: int = 12, max_chars: int = 6000) -> None:
        self.max_recent = max_recent
        self.max_chars = max_chars
        self.summary = ""
        self.recent: list[ContextMessage] = []

    def add(self, role: str, content: str) -> None:
        self.recent.append(
            ContextMessage(role=role, content=content, created_at=now_iso())
        )
        self._compact_if_needed()

    def _compact_if_needed(self) -> None:
        while len(self.recent) > self.max_recent or self._char_count() > self.max_chars:
            oldest = self.recent.pop(0)
            summary_line = f"[{oldest.role}] {oldest.content}"
            if self.summary:
                self.summary = (self.summary + "\n" + summary_line)[-self.max_chars :]
            else:
                self.summary = summary_line[-self.max_chars :]

    def _char_count(self) -> int:
        size = len(self.summary)
        for row in self.recent:
            size += len(row.content)
        return size

    def model_messages(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        if self.summary:
            rows.append({"role": "system", "content": f"历史摘要:\n{self.summary}"})
        for row in self.recent:
            rows.append({"role": row.role, "content": row.content})
        return rows

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "saved_at": now_iso(),
            "max_recent": self.max_recent,
            "max_chars": self.max_chars,
            "summary": self.summary,
            "recent": [asdict(row) for row in self.recent],
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    @classmethod
    def load(
        cls, path: Path, max_recent: int = 12, max_chars: int = 6000
    ) -> ContextGovernor:
        governor = cls(max_recent=max_recent, max_chars=max_chars)
        if not path.exists():
            return governor
        payload = json.loads(path.read_text(encoding="utf-8"))
        governor.summary = str(payload.get("summary", ""))
        rows = list(payload.get("recent", []))
        for row in rows:
            governor.recent.append(
                ContextMessage(
                    role=str(row.get("role", "user")),
                    content=str(row.get("content", "")),
                    created_at=str(row.get("created_at", now_iso())),
                )
            )
        governor._compact_if_needed()
        return governor
