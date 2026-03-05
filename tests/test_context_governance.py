from __future__ import annotations

from pathlib import Path

from src.full_rewrite.context_governance import ContextGovernor


def test_context_compacts_when_exceeding_recent_limit() -> None:
    gov = ContextGovernor(max_recent=2, max_chars=1000)
    gov.add("user", "u1")
    gov.add("assistant", "a1")
    gov.add("user", "u2")

    assert len(gov.recent) == 2
    assert "u1" in gov.summary


def test_context_compacts_when_exceeding_char_limit() -> None:
    gov = ContextGovernor(max_recent=10, max_chars=20)
    gov.add("user", "1234567890")
    gov.add("assistant", "abcdefghij")
    gov.add("user", "ZZZZZZ")

    total = len(gov.summary) + sum(len(row.content) for row in gov.recent)
    assert total <= 20


def test_context_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    gov = ContextGovernor(max_recent=3, max_chars=200)
    gov.add("user", "hello")
    gov.add("assistant", "world")
    gov.save(path)

    loaded = ContextGovernor.load(path, max_recent=3, max_chars=200)
    rows = loaded.model_messages()

    assert rows[-1]["content"] == "world"
