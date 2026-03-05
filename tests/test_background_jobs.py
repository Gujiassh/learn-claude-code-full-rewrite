from __future__ import annotations

import time

from src.full_rewrite.background_jobs import BackgroundJobRunner


def wait_until_done(runner: BackgroundJobRunner, timeout: float = 2.0) -> None:
    start = time.monotonic()
    while runner.has_pending():
        if time.monotonic() - start > timeout:
            raise TimeoutError("job not finished within timeout")
        time.sleep(0.01)


def test_background_job_completes() -> None:
    runner = BackgroundJobRunner(max_workers=1)
    try:
        job_id = runner.submit("sum", lambda a, b: a + b, 2, 3)
        wait_until_done(runner)
        state = runner.get(job_id)
        assert state is not None
        assert state.status == "completed"
        assert state.result == "5"
        assert state.error == ""
    finally:
        runner.shutdown()


def test_background_job_failure() -> None:
    runner = BackgroundJobRunner(max_workers=1)

    def boom() -> str:
        raise RuntimeError("failed job")

    try:
        job_id = runner.submit("fail", boom)
        wait_until_done(runner)
        state = runner.get(job_id)
        assert state is not None
        assert state.status == "failed"
        assert "failed job" in state.error
    finally:
        runner.shutdown()


def test_list_jobs_sorted() -> None:
    runner = BackgroundJobRunner(max_workers=1)
    try:
        first = runner.submit("first", lambda: "1")
        second = runner.submit("second", lambda: "2")
        wait_until_done(runner)
        ids = [job.job_id for job in runner.list_jobs()]
        assert ids == [first, second]
    finally:
        runner.shutdown()
