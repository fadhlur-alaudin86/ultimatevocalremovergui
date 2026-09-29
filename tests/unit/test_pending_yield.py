"""Tests for pending-yield scheduling (paused pending jobs are skipped)."""

import threading
import time

from uvr.core.service import InferenceService


def _spec(tmp_path, name):
    from uvr.core.jobs import JobSpec

    src = tmp_path / f"{name}.wav"
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


def test_paused_pending_job_is_skipped_until_resumed(tmp_path):
    release_first = threading.Event()
    finished = []

    def run_fn(spec, pause, cancel):
        from uvr.models.base import check_control

        if "first" in spec.input_paths[0]:
            assert release_first.wait(timeout=10.0)
        else:
            for _ in range(50):
                check_control(pause, cancel)
                time.sleep(0.01)
        finished.append(spec.input_paths[0])

    svc = InferenceService(run_fn=run_fn)
    try:
        svc.submit(_spec(tmp_path, "first"))
        svc.submit(_spec(tmp_path, "second"))
        # Hold the running job, pause the pending one, then let go.
        time.sleep(0.5)
        running = [jid for jid, s in svc.statuses().items() if s in ("running", "paused")]
        assert len(running) == 1
        others = [jid for jid in svc.statuses() if jid not in running]
        assert len(others) == 1
        svc.pause(others)
        release_first.set()
        deadline = time.time() + 10.0
        while svc.statuses()[others[0]] != "paused" or any("first" in f for f in finished) is False:
            if time.time() > deadline:
                break
            time.sleep(0.05)
        # First job finished while the second stayed paused (yield proven).
        assert any("first" in f for f in finished)
        assert svc.statuses()[others[0]] == "paused"
        assert not any("second" in f for f in finished)
        svc.resume(others)
        deadline = time.time() + 10.0
        while svc.statuses()[others[0]] not in ("completed", "failed", "cancelled"):
            assert time.time() < deadline
            time.sleep(0.05)
        assert svc.statuses()[others[0]] == "completed"
    finally:
        release_first.set()
        svc.stop()
