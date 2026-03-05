from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


ToolHandler = Callable[..., str]


class ModelClient(Protocol):
    def respond(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        self._handlers[name] = handler

    def execute(self, call: ToolCall) -> str:
        handler = self._handlers.get(call.name)
        if handler is None:
            return f"Error: unknown tool '{call.name}'"
        return handler(**call.arguments)


class AgentLoop:
    def __init__(
        self, model: ModelClient, tools: ToolRegistry, max_iterations: int = 12
    ) -> None:
        self.model = model
        self.tools = tools
        self.max_iterations = max_iterations

    def run(self, user_prompt: str) -> tuple[str, list[dict[str, Any]]]:
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

        for _ in range(self.max_iterations):
            response = self.model.respond(messages)
            response_type = str(response.get("type", "text"))

            if response_type == "text":
                text = str(response.get("content", ""))
                messages.append({"role": "assistant", "content": text})
                return text, messages

            if response_type == "tool_call":
                call = ToolCall(
                    name=str(response.get("name", "")),
                    arguments=dict(response.get("arguments", {})),
                )
                result = self.tools.execute(call)
                messages.append(
                    {
                        "role": "tool",
                        "name": call.name,
                        "arguments": call.arguments,
                        "content": result,
                    }
                )
                continue

            messages.append(
                {
                    "role": "assistant",
                    "content": f"Error: unsupported response type '{response_type}'",
                }
            )
            return f"Error: unsupported response type '{response_type}'", messages

        fallback = "Error: max iterations reached"
        messages.append({"role": "assistant", "content": fallback})
        return fallback, messages
