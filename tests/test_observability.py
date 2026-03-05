from __future__ import annotations

import json
from pathlib import Path

from src.full_rewrite.observability import ObservabilityHub


def test_observability_summary_counts() -> None:
    hub = ObservabilityHub()
    hub.record("task.claim", status="ok", duration_ms=3.0)
    hub.record("task.claim", status="ok", duration_ms=5.0)
    hub.record("task.complete", status="fail", duration_ms=8.0)

    summary = hub.summary()
    assert summary["total"] == 3
    assert summary["ok"] == 2
    assert summary["fail"] == 1
    assert summary["by_name"]["task.claim"] == 2


def test_observability_exports_json_and_markdown(tmp_path: Path) -> None:
    hub = ObservabilityHub()
    hub.record("bg.submit", status="ok", duration_ms=1.5)

    json_path = tmp_path / "metrics.json"
    md_path = tmp_path / "metrics.md"
    hub.save_json(json_path)
    hub.save_markdown(md_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total"] == 1
    assert "可观测性报告" in md_path.read_text(encoding="utf-8")
