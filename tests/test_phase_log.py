from __future__ import annotations

from pathlib import Path

from src.full_rewrite.phase_log import PhaseEntry, PhaseLog


def test_phase_log_appends_entry(tmp_path: Path) -> None:
    log_path = tmp_path / "阶段记录.md"
    phase_log = PhaseLog(log_path)

    phase_log.append(
        PhaseEntry(
            phase="阶段-01",
            status="完成",
            summary="核心循环可运行",
            artifact="tests/test_runtime.py",
        )
    )

    text = log_path.read_text(encoding="utf-8")
    assert "阶段-01" in text
    assert "核心循环可运行" in text
