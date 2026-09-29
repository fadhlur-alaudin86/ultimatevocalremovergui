"""Headless inference orchestration: submit/pause/resume/cancel + cleanup.

Single background worker, one active inference at a time. Views talk only
to this class; model code is reached through the injected ``run_fn`` so
tests stay torch-free.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any

from uvr.core.device_manager import DeviceManager
from uvr.core.jobs import JobError, JobSpec
from uvr.models.base import ControlCancelled
from uvr.utils.file_utils import remove_temps

logger = logging.getLogger(__name__)

PENDING = "pending"
RUNNING = "running"
PAUSED = "paused"
CANCELLED = "cancelled"
COMPLETED = "completed"
FAILED = "failed"


@dataclass
class _JobState:
    spec: JobSpec
    status: str = PENDING
    pause_event: threading.Event = field(default_factory=threading.Event)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    error: JobError | None = None
    runner: Any = None
    thread: threading.Thread | None = None


class InferenceService:
    """Serial job queue with cooperative pause/cancel and temp cleanup.

    Pause semantics: pausing PENDING jobs removes them from scheduling so the
    worker yields to the next unpaused file (resume re-queues at front).
    Pausing the RUNNING job blocks it mid-inference via ``check_control``
    and holds the worker: a single GPU cannot safely start a second
    inference while the first still holds VRAM, so the active inference
    keeps priority until resume/cancel/finish.
    """

    def __init__(self, run_fn=None, autostart: bool = True) -> None:
        self._run_fn = run_fn
        self._lock = threading.RLock()
        self._jobs: dict[int, _JobState] = {}
        self._order: list[int] = []
        self._listeners: list[Any] = []
        self._counter = 0
        self._stopped = False
        self._worker: threading.Thread | None = None
        if autostart:
            self.start()

    def add_listener(self, fn) -> None:
        """Register ``fn(job_id, status)`` called on every status transition."""
        with self._lock:
            self._listeners.append(fn)

    def _emit(self, job_id: int, status: str) -> None:
        with self._lock:
            fns = list(self._listeners)
        for fn in fns:
            try:
                fn(job_id, status)
            except Exception:
                logger.exception("service listener failed for job %s", job_id)

    def start(self) -> None:
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._stopped = False
                self._worker = threading.Thread(target=self._worker_loop, daemon=True)
                self._worker.start()

    def stop(self) -> None:
        with self._lock:
            self._stopped = True
        worker, _ = self._worker, None
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=5.0)

    def submit(self, spec: JobSpec, run_fn=None) -> int:
        """Enqueue a frozen ``JobSpec``; returns the job id."""
        runner = run_fn if run_fn is not None else self._run_fn
        if runner is None:
            raise JobError(code="NO_RUNNER", message="no run function", hint="pass run_fn")
        if not spec.input_paths:
            raise JobError(code="BAD_INPUT", message="empty input list", hint="add audio files")
        for path in spec.input_paths:
            if not os.path.isfile(path):
                raise JobError(code="BAD_INPUT", message=f"missing input: {path}", hint="re-check input files")
        try:
            DeviceManager.resolve(spec.device_set, want_gpu=spec.is_gpu_conversion)
        except ValueError as exc:
            raise JobError(code="BAD_DEVICE", message=str(exc), hint="pick an available GPU") from exc
        with self._lock:
            self._counter += 1
            job_id = self._counter
            self._jobs[job_id] = _JobState(spec=spec, runner=runner)
            self._order.append(job_id)
        self._emit(job_id, PENDING)
        return job_id

    def pause(self, ids: list[int]) -> None:
        """Pause selected jobs: pending ones are skipped, a running one blocks mid-inference."""
        changed = []
        with self._lock:
            for job_id in ids:
                state = self._jobs.get(job_id)
                if state is None:
                    continue
                if state.status == PENDING:
                    state.status = PAUSED
                    changed.append(job_id)
                elif state.status == RUNNING:
                    state.pause_event.set()
                    state.status = PAUSED
                    changed.append(job_id)
        for job_id in changed:
            self._emit(job_id, PAUSED)

    def resume(self, ids: list[int]) -> None:
        """Resume selected jobs; pending ones re-queue at the front, a paused running one unblocks."""
        changed = []
        with self._lock:
            for job_id in ids:
                state = self._jobs.get(job_id)
                if state is None or state.status != PAUSED:
                    continue
                state.pause_event.clear()
                if job_id in self._order:
                    self._order.remove(job_id)
                    self._order.insert(0, job_id)
                    state.status = PENDING
                else:
                    state.status = RUNNING
                changed.append((job_id, state.status))
        for job_id, status in changed:
            self._emit(job_id, status)

    def cancel(self, ids: list[int]) -> None:
        """Cancel selected jobs, remove them from the worker, and clean temps/partials."""
        threads: list[threading.Thread] = []
        immediate: list[int] = []
        with self._lock:
            for job_id in ids:
                state = self._jobs.get(job_id)
                if state is None or state.status in (CANCELLED, COMPLETED, FAILED):
                    continue
                state.cancel_event.set()
                state.pause_event.clear()
                if job_id in self._order:
                    self._order.remove(job_id)
                if state.status == RUNNING:
                    if state.thread is not None:
                        threads.append(state.thread)
                else:
                    state.status = CANCELLED
                    immediate.append(job_id)
                    self._cleanup(state.spec)
        for job_id in immediate:
            self._emit(job_id, CANCELLED)
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(timeout=30.0)

    def cancel_all(self) -> None:
        with self._lock:
            ids = list(self._jobs.keys())
        self.cancel(ids)
        with self._lock:
            self._order.clear()

    def statuses(self) -> dict[int, str]:
        with self._lock:
            return {job_id: state.status for job_id, state in self._jobs.items()}

    def error_of(self, job_id: int) -> JobError | None:
        with self._lock:
            state = self._jobs.get(job_id)
            return state.error if state else None

    def _worker_loop(self) -> None:
        while True:
            with self._lock:
                if self._stopped:
                    return
                next_id = next((i for i in self._order if self._jobs[i].status == PENDING), None)
                if next_id is None:
                    job_to_run = None
                else:
                    self._order.remove(next_id)
                    state = self._jobs[next_id]
                    state.status = RUNNING
                    job_to_run = (next_id, state)
            if job_to_run is None:
                threading.Event().wait(0.05)
                continue
            self._emit(job_to_run[0], RUNNING)
            self._run_job(*job_to_run)

    def _run_job(self, job_id: int, state: _JobState) -> None:
        runner = state.runner if state.runner is not None else self._run_fn

        def target() -> None:
            try:
                runner(state.spec, state.pause_event, state.cancel_event)
            except ControlCancelled as exc:
                with self._lock:
                    state.status = CANCELLED
                    state.error = JobError(code="CANCELLED", message=str(exc), hint="job cancelled by user")
                self._cleanup(state.spec)
                self._emit(job_id, CANCELLED)
            except JobError as exc:
                with self._lock:
                    state.status = FAILED
                    state.error = exc
                self._cleanup(state.spec)
                self._emit(job_id, FAILED)
            except Exception as exc:
                logger.exception("job %s failed", job_id)
                with self._lock:
                    state.status = FAILED
                    state.error = JobError(code="FAILED", message=str(exc), hint="see log for details")
                self._cleanup(state.spec)
                self._emit(job_id, FAILED)
            else:
                # Thread returned without exception: the job completed.
                # (A pause() racing the final checkpoint leaves status
                # PAUSED; completion still wins because all work is done.)
                with self._lock:
                    state.status = COMPLETED
                self._emit(job_id, COMPLETED)

        thread = threading.Thread(target=target, daemon=True)
        with self._lock:
            state.thread = thread
        thread.start()
        thread.join()

    def _cleanup(self, spec: JobSpec) -> None:
        base = (spec.extra or {}).get("audio_file_base")
        if base:
            self._cleanup_partials(spec.export_path, base)
        temp_dir = (spec.extra or {}).get("temp_dir")
        if temp_dir:
            remove_temps(temp_dir)

    def _cleanup_partials(self, export_path: str, audio_file_base: str) -> None:
        # Outputs are always "{base}_({stem}).wav" — match that shape exactly
        # so unrelated files sharing the base prefix are never touched.
        prefix = f"{audio_file_base}_("
        try:
            names = os.listdir(export_path)
        except OSError:
            return
        for name in names:
            if name.startswith(prefix):
                try:
                    os.remove(os.path.join(export_path, name))
                except OSError as exc:
                    logger.debug("Could not remove partial %s: %s", name, exc)
