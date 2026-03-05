from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable
from uuid import uuid4


UTC = timezone.utc
JobCallable = Callable[..., Any]


def now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class JobState:
    job_id: str
    name: str
    status: str
    created_at: str
    started_at: str
    finished_at: str
    result: str
    error: str


class BackgroundJobRunner:
    def __init__(self, max_workers: int = 2) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = Lock()
        self._jobs: dict[str, JobState] = {}

    def submit(self, name: str, fn: JobCallable, *args: Any, **kwargs: Any) -> str:
        job_id = str(uuid4())
        created = now_iso()
        state = JobState(
            job_id=job_id,
            name=name,
            status="queued",
            created_at=created,
            started_at="",
            finished_at="",
            result="",
            error="",
        )
        with self._lock:
            self._jobs[job_id] = state

        def run_job() -> None:
            with self._lock:
                current = self._jobs[job_id]
                current.status = "running"
                current.started_at = now_iso()

            try:
                output = fn(*args, **kwargs)
                with self._lock:
                    current = self._jobs[job_id]
                    current.status = "completed"
                    current.finished_at = now_iso()
                    current.result = str(output)
            except Exception as error:
                with self._lock:
                    current = self._jobs[job_id]
                    current.status = "failed"
                    current.finished_at = now_iso()
                    current.error = str(error)

        self._pool.submit(run_job)
        return job_id

    def get(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[JobState]:
        with self._lock:
            rows = list(self._jobs.values())
        rows.sort(key=lambda x: x.created_at)
        return rows

    def has_pending(self) -> bool:
        for row in self.list_jobs():
            if row.status in {"queued", "running"}:
                return True
        return False

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)
