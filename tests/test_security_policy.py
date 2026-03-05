from __future__ import annotations

from pathlib import Path

from src.full_rewrite.security_policy import AuditTrail, SecurityPolicy


def test_tool_allow_and_block() -> None:
    policy = SecurityPolicy(allowed_tools={"read_file"})
    allow = policy.check_tool("read_file")
    block = policy.check_tool("execute_bash")

    assert allow.allowed is True
    assert block.allowed is False


def test_command_block_pattern() -> None:
    policy = SecurityPolicy()
    bad = policy.check_command("rm -rf /")
    good = policy.check_command("ls -la")

    assert bad.allowed is False
    assert good.allowed is True


def test_audit_trail_roundtrip(tmp_path: Path) -> None:
    trail = AuditTrail(tmp_path / "audit.jsonl")
    trail.append("tool", True, "read_file")
    trail.append("command", False, "rm -rf /")

    rows = trail.read_all()
    assert len(rows) == 2
    assert rows[1].allowed is False
