from __future__ import annotations

from typing import Any

from src.full_rewrite.runtime import AgentLoop, ToolRegistry


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
