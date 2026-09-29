"""Tests for service status listeners (view auto-refresh hook)."""

import time

from uvr.core.service import InferenceService


def _spec(tmp_path):
    from uvr.core.jobs import JobSpec

    src = tmp_path / "in.wav"
    src.touch()
    return JobSpec(
        job_id=0,
        process_method="VR",
        model_id="m",
        input_paths=(str(src),),
        export_path=str(tmp_path),
        is_half_precision=False,
        is_gpu_conversion=False,
        device_set="Default",
        save_format="WAV",
        wav_type_set="PCM_16",
        mp3_bit_set="320k",
        is_model_sample_mode=False,
        extra={},
    )


def test_listener_sees_lifecycle_transitions(tmp_path):
    seen = []
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None)
    try:
        svc.add_listener(lambda job_id, status: seen.append((job_id, status)))
        jid = svc.submit(_spec(tmp_path))
        deadline = time.time() + 10.0
        while svc.statuses().get(jid) != "completed":
            assert time.time() < deadline
            time.sleep(0.02)
        kinds = {status for _, status in seen}
        assert "running" in kinds and "completed" in kinds
    finally:
        svc.stop()


def test_listener_sees_pause_and_cancel(tmp_path):
    seen = []
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None, autostart=False)
    try:
        svc.add_listener(lambda job_id, status: seen.append(status))
        jid = svc.submit(_spec(tmp_path))
        svc.pause([jid])
        svc.cancel([jid])
        assert "paused" in seen and "cancelled" in seen
    finally:
        svc.stop()
