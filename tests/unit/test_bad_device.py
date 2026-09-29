"""Tests for submit-time device validation (BAD_DEVICE)."""

import pytest

from uvr.core.jobs import JobError
from uvr.core.service import InferenceService


def _spec(tmp_path, device_set):
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
        is_gpu_conversion=True,
        device_set=device_set,
        save_format="WAV",
        wav_type_set="PCM_16",
        mp3_bit_set="320k",
        is_model_sample_mode=False,
        extra={},
    )


def test_submit_rejects_garbage_device_set(tmp_path):
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None, autostart=False)
    try:
        with pytest.raises(JobError) as exc_info:
            svc.submit(_spec(tmp_path, "nonsense"))
        assert exc_info.value.code == "BAD_DEVICE"
    finally:
        svc.stop()


def test_submit_rejects_out_of_range_cuda_index(tmp_path):
    import torch

    if not torch.cuda.is_available():
        pytest.skip("needs CUDA for index range check")
    svc = InferenceService(run_fn=lambda spec, pause, cancel: None, autostart=False)
    try:
        with pytest.raises(JobError) as exc_info:
            svc.submit(_spec(tmp_path, 99))
        assert exc_info.value.code == "BAD_DEVICE"
    finally:
        svc.stop()
