from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Pattern


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(slots=True)
class AuditEvent:
    ts: str
    category: str
    allowed: bool
    detail: str


class SecurityPolicy:
    def __init__(
        self,
        allowed_tools: set[str] | None = None,
        blocked_patterns: list[str] | None = None,
    ) -> None:
        self.allowed_tools = allowed_tools or {
            "execute_bash",
            "read_file",
            "write_file",
        }
        patterns = blocked_patterns or [
            r"\brm\s+-rf\s+/",
            r"\bshutdown\b",
            r"\breboot\b",
            r":\(\)\{\s*:\|:&\s*\};:",
        ]
        self.blocked_patterns: list[Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in patterns
        ]

    def check_tool(self, tool_name: str) -> PolicyDecision:
        if tool_name in self.allowed_tools:
            return PolicyDecision(True, "tool allowed")
        return PolicyDecision(False, f"tool blocked: {tool_name}")

    def check_command(self, command: str) -> PolicyDecision:
        for pattern in self.blocked_patterns:
            if pattern.search(command):
                return PolicyDecision(
                    False, f"command blocked by policy: {pattern.pattern}"
                )
        return PolicyDecision(True, "command allowed")


class AuditTrail:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, category: str, allowed: bool, detail: str) -> None:
        event = AuditEvent(
            ts=now_iso(), category=category, allowed=allowed, detail=detail
        )
        line = json.dumps(asdict(event), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")

    def read_all(self) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        rows = self.path.read_text(encoding="utf-8").splitlines()
        out: list[AuditEvent] = []
        for row in rows:
            data = json.loads(row)
            out.append(
                AuditEvent(
                    ts=str(data.get("ts", "")),
                    category=str(data.get("category", "")),
                    allowed=bool(data.get("allowed", False)),
                    detail=str(data.get("detail", "")),
                )
            )
        return out
