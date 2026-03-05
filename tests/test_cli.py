from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, "-m", "full_rewrite.cli", *args],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_cli_task_flow(tmp_path: Path) -> None:
    add = run_cli(tmp_path, "task", "add", "t1", "title")
    assert add.returncode == 0

    claim = run_cli(tmp_path, "task", "claim", "worker")
    assert claim.returncode == 0

    complete = run_cli(tmp_path, "task", "complete", "t1")
    assert complete.returncode == 0

    listing = run_cli(tmp_path, "task", "list")
    assert listing.returncode == 0
    assert "tasks=1" in listing.stdout


def test_cli_context_and_observe(tmp_path: Path) -> None:
    add_ctx = run_cli(tmp_path, "context", "add", "user", "hello")
    assert add_ctx.returncode == 0

    show_ctx = run_cli(tmp_path, "context", "show")
    assert show_ctx.returncode == 0

    observe = run_cli(tmp_path, "observe")
    assert observe.returncode == 0
    assert (tmp_path / ".rewrite_data" / "metrics.json").exists()
    assert (tmp_path / ".rewrite_data" / "metrics.md").exists()
