from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class PhaseEntry:
    phase: str
    status: str
    summary: str
    artifact: str


class PhaseLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: PhaseEntry) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (
            f"- 时间: {ts} | 阶段: {entry.phase} | 状态: {entry.status}"
            f" | 摘要: {entry.summary} | 产物: {entry.artifact}\n"
        )
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(line)
