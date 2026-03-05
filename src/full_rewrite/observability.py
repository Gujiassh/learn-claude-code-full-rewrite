from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class MetricEvent:
    ts: str
    name: str
    status: str
    duration_ms: float
    metadata: dict[str, str]


class ObservabilityHub:
    def __init__(self) -> None:
        self.events: list[MetricEvent] = []

    def record(
        self,
        name: str,
        status: str = "ok",
        duration_ms: float = 0.0,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.events.append(
            MetricEvent(
                ts=now_iso(),
                name=name,
                status=status,
                duration_ms=float(duration_ms),
                metadata=dict(metadata or {}),
            )
        )

    def summary(self) -> dict[str, Any]:
        total = len(self.events)
        ok = sum(1 for event in self.events if event.status == "ok")
        fail = sum(1 for event in self.events if event.status != "ok")
        total_duration = sum(event.duration_ms for event in self.events)
        avg_duration = (total_duration / total) if total else 0.0
        names: dict[str, int] = {}
        for event in self.events:
            names[event.name] = names.get(event.name, 0) + 1
        return {
            "total": total,
            "ok": ok,
            "fail": fail,
            "avg_duration_ms": round(avg_duration, 3),
            "by_name": names,
        }

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "saved_at": now_iso(),
            "summary": self.summary(),
            "events": [asdict(event) for event in self.events],
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def save_markdown(self, path: Path) -> None:
        stats = self.summary()
        lines: list[str] = []
        lines.append(f"# 可观测性报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append(f"- 事件总数: {stats['total']}")
        lines.append(f"- 成功: {stats['ok']}")
        lines.append(f"- 失败: {stats['fail']}")
        lines.append(f"- 平均耗时(ms): {stats['avg_duration_ms']}")
        lines.append("")
        lines.append("## 按事件名统计")
        lines.append("")
        for name, count in sorted(stats["by_name"].items()):
            lines.append(f"- {name}: {count}")
        if not stats["by_name"]:
            lines.append("- 无")
        lines.append("")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
