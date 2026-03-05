from __future__ import annotations

from pathlib import Path
from typing import Any

from src.full_rewrite.context_governance import ContextGovernor
from src.full_rewrite.observability import ObservabilityHub
from src.full_rewrite.runtime import AgentLoop, ToolRegistry
from src.full_rewrite.security_policy import AuditTrail, SecurityPolicy


class FakeModel:
    def __init__(self, outputs: list[dict[str, Any]]) -> None:
        self.outputs = outputs
        self.index = 0

    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        _ = messages
        out = self.outputs[self.index]
        self.index += 1
        return out


def test_agent_loop_returns_text_when_model_finishes() -> None:
    model = FakeModel([{"type": "text", "content": "done"}])
    tools = ToolRegistry()
    loop = AgentLoop(model=model, tools=tools)

    text, messages = loop.run("start")

    assert text == "done"
    assert messages[-1]["content"] == "done"


def test_agent_loop_executes_tool_then_finishes() -> None:
    model = FakeModel(
        [
            {"type": "tool_call", "name": "echo", "arguments": {"text": "hi"}},
            {"type": "text", "content": "ok"},
        ]
    )
    tools = ToolRegistry()
    tools.register("echo", lambda text: f"ECHO:{text}")
    loop = AgentLoop(model=model, tools=tools)

    text, messages = loop.run("start")

    assert text == "ok"
    tool_messages = [m for m in messages if m["role"] == "tool"]
    assert tool_messages[0]["content"] == "ECHO:hi"


def test_agent_loop_handles_unknown_tool() -> None:
    model = FakeModel(
        [
            {"type": "tool_call", "name": "missing", "arguments": {}},
            {"type": "text", "content": "recovered"},
        ]
    )
    tools = ToolRegistry()
    loop = AgentLoop(model=model, tools=tools)

    text, messages = loop.run("start")

    assert text == "recovered"
    tool_messages = [m for m in messages if m["role"] == "tool"]
    assert "unknown tool" in tool_messages[0]["content"]


def test_agent_loop_enforces_security_policy_and_audits(tmp_path: Path) -> None:
    model = FakeModel(
        [
            {
                "type": "tool_call",
                "name": "execute_bash",
                "arguments": {"command": "rm -rf /"},
            },
            {"type": "text", "content": "done"},
        ]
    )
    tools = ToolRegistry()
    tools.register("execute_bash", lambda command: f"ran:{command}")
    loop = AgentLoop(model=model, tools=tools)
    policy = SecurityPolicy()
    audit = AuditTrail(tmp_path / "audit.jsonl")
    obs = ObservabilityHub()

    text, messages = loop.run("start", policy=policy, audit=audit, observability=obs)

    assert text == "done"
    tool_messages = [m for m in messages if m["role"] == "tool"]
    assert "command blocked by policy" in tool_messages[0]["content"]
    audit_rows = audit.read_all()
    assert len(audit_rows) >= 1
    assert any((not row.allowed) for row in audit_rows)
    assert obs.summary()["total"] >= 1


def test_agent_loop_with_context_governor() -> None:
    model = FakeModel([{"type": "text", "content": "final"}])
    tools = ToolRegistry()
    loop = AgentLoop(model=model, tools=tools)
    governor = ContextGovernor(max_recent=2, max_chars=100)

    text, _ = loop.run("hello", governor=governor)

    assert text == "final"
    rows = governor.model_messages()
    assert rows[-1]["content"] == "final"
