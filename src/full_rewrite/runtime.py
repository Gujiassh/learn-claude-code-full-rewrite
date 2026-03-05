from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Protocol

from .context_governance import ContextGovernor
from .observability import ObservabilityHub
from .security_policy import AuditTrail, SecurityPolicy


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

    def run(
        self,
        user_prompt: str,
        governor: ContextGovernor | None = None,
        policy: SecurityPolicy | None = None,
        audit: AuditTrail | None = None,
        observability: ObservabilityHub | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        if governor is not None:
            governor.add("user", user_prompt)
            messages: list[dict[str, Any]] = governor.model_messages()
        else:
            messages = [{"role": "user", "content": user_prompt}]

        for _ in range(self.max_iterations):
            round_start = perf_counter()
            response = self.model.respond(messages)
            response_type = str(response.get("type", "text"))

            if response_type == "text":
                text = str(response.get("content", ""))
                messages.append({"role": "assistant", "content": text})
                if governor is not None:
                    governor.add("assistant", text)
                if observability is not None:
                    observability.record(
                        "agent.text_response",
                        status="ok",
                        duration_ms=(perf_counter() - round_start) * 1000,
                    )
                return text, messages

            if response_type == "tool_call":
                call = ToolCall(
                    name=str(response.get("name", "")),
                    arguments=dict(response.get("arguments", {})),
                )
                result = ""
                tool_decision = (
                    policy.check_tool(call.name) if policy is not None else None
                )
                if tool_decision is not None and not tool_decision.allowed:
                    result = f"Error: {tool_decision.reason}"
                    if audit is not None:
                        audit.append(
                            "tool", False, f"{call.name}: {tool_decision.reason}"
                        )
                    if observability is not None:
                        observability.record(
                            "agent.tool_call", status="blocked", duration_ms=0.0
                        )
                else:
                    cmd_decision_blocked = False
                    if policy is not None and call.name == "execute_bash":
                        command = str(call.arguments.get("command", ""))
                        command_decision = policy.check_command(command)
                        if not command_decision.allowed:
                            result = f"Error: {command_decision.reason}"
                            cmd_decision_blocked = True
                            if audit is not None:
                                audit.append(
                                    "command",
                                    False,
                                    f"{command}: {command_decision.reason}",
                                )
                    if not cmd_decision_blocked:
                        result = self.tools.execute(call)
                        if audit is not None and policy is not None:
                            audit.append("tool", True, f"{call.name} allowed")
                    if observability is not None:
                        observability.record(
                            "agent.tool_call",
                            status="ok" if not cmd_decision_blocked else "blocked",
                            duration_ms=(perf_counter() - round_start) * 1000,
                            metadata={"tool": call.name},
                        )
                messages.append(
                    {
                        "role": "tool",
                        "name": call.name,
                        "arguments": call.arguments,
                        "content": result,
                    }
                )
                if governor is not None:
                    governor.add("tool", result)
                continue

            messages.append(
                {
                    "role": "assistant",
                    "content": f"Error: unsupported response type '{response_type}'",
                }
            )
            if observability is not None:
                observability.record(
                    "agent.unsupported_response",
                    status="fail",
                    duration_ms=(perf_counter() - round_start) * 1000,
                    metadata={"type": response_type},
                )
            return f"Error: unsupported response type '{response_type}'", messages

        fallback = "Error: max iterations reached"
        messages.append({"role": "assistant", "content": fallback})
        if governor is not None:
            governor.add("assistant", fallback)
        if observability is not None:
            observability.record("agent.max_iterations", status="fail", duration_ms=0.0)
        return fallback, messages
