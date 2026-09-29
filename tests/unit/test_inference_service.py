"""Tests for InferenceService orchestration (torch-free via run_fn injection)."""

import threading
import time

import pytest

from uvr.core.jobs import JobError, JobSpec
from uvr.core.service import InferenceService


def make_spec(tmp_path, **overrides):
    src = tmp_path / "in.wav"
    src.touch()
    kwargs = {
        "job_id": 0,
        "process_method": "VR",
        "model_id": "m",
        "input_paths": (str(src),),
        "export_path": str(tmp_path),
        "is_half_precision": False,
        "is_gpu_conversion": False,
        "device_set": "Default",
        "save_format": "WAV",
        "wav_type_set": "PCM_16",
        "mp3_bit_set": "320k",
        "is_model_sample_mode": False,
        "extra": {},
    }
    kwargs.update(overrides)
    return JobSpec(**kwargs)


def test_pause_resume_and_cancel_selected(tmp_path):
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None, autostart=False)
    try:
        jid = svc.submit(make_spec(tmp_path))
        svc.pause([jid])
        assert svc.statuses()[jid] == "paused"
        svc.resume([jid])
        assert svc.statuses()[jid] == "pending"
        svc.cancel([jid])
        assert svc.statuses()[jid] == "cancelled"
    finally:
        svc.stop()


def test_running_job_pauses_mid_inference_and_resumes(tmp_path):
    entered = threading.Event()
    proceed = threading.Event()

    def run_fn(spec, pause, cancel):
        from uvr.models.base import check_control

        entered.set()
        for _ in range(200):
            check_control(pause, cancel)
            if proceed.is_set():
                return
            time.sleep(0.01)
        raise AssertionError("job should have finished via proceed flag")

    svc = InferenceService(run_fn=run_fn)
    try:
        jid = svc.submit(make_spec(tmp_path))
        assert entered.wait(timeout=5.0)
        svc.pause([jid])
        time.sleep(0.3)
        assert svc.statuses()[jid] == "paused"
        svc.resume([jid])
        proceed.set()
        deadline = time.time() + 10.0
        while svc.statuses()[jid] not in ("completed", "failed", "cancelled"):
            assert time.time() < deadline, "job did not finish after resume"
            time.sleep(0.05)
        assert svc.statuses()[jid] == "completed"
    finally:
        proceed.set()
        svc.stop()


def test_cancel_running_job_removes_partial_and_marks_cancelled(tmp_path):
    from uvr.models.base import check_control

    def run_fn(spec, pause, cancel):
        partial = tmp_path / "out_(Vocals).wav"
        partial.touch()
        for _ in range(600):
            check_control(pause, cancel)
            time.sleep(0.01)

    svc = InferenceService(run_fn=run_fn)
    try:
        spec = make_spec(tmp_path, extra={"audio_file_base": "out"})
        jid = svc.submit(spec)
        deadline = time.time() + 5.0
        while not (tmp_path / "out_(Vocals).wav").exists():
            assert time.time() < deadline
            time.sleep(0.02)
        svc.cancel([jid])
        assert svc.statuses()[jid] == "cancelled"
        assert not (tmp_path / "out_(Vocals).wav").exists()
    finally:
        svc.stop()


def test_submit_missing_input_raises_bad_input(tmp_path):
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None, autostart=False)
    try:
        spec = make_spec(tmp_path, input_paths=("/no/such/file.wav",))
        with pytest.raises(JobError) as exc_info:
            svc.submit(spec)
        assert exc_info.value.code == "BAD_INPUT"
    finally:
        svc.stop()


def test_job_error_is_raisable():
    err = JobError(code="BAD_INPUT", message="m", hint="h")
    with pytest.raises(JobError):
        raise err
