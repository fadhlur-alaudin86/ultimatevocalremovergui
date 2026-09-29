"""Tests for the frozen JobSpec snapshot and JobError."""

from dataclasses import FrozenInstanceError

import pytest

from uvr.core.jobs import JobError, JobSpec


def make_spec(**overrides):
    kwargs = {
        "job_id": 1,
        "process_method": "VR",
        "model_id": "m",
        "input_paths": ("a.wav",),
        "export_path": "/tmp/x",
        "is_half_precision": True,
        "is_gpu_conversion": True,
        "device_set": 0,
        "save_format": "WAV",
        "wav_type_set": "PCM_16",
        "mp3_bit_set": "320k",
        "is_model_sample_mode": False,
        "extra": {},
    }
    kwargs.update(overrides)
    return JobSpec(**kwargs)


def test_snapshot_is_immutable_after_source_mutation():
    spec = make_spec()
    assert spec.input_paths == ("a.wav",)
    with pytest.raises(FrozenInstanceError):
        spec.job_id = 2


def test_input_paths_coerced_to_tuple():
    spec = make_spec(input_paths=["a.wav", "b.wav"])
    assert spec.input_paths == ("a.wav", "b.wav")


def test_job_error_carries_code_message_hint():
    err = JobError(code="BAD_INPUT", message="no audio", hint="pick a wav file")
    assert (err.code, err.message, err.hint) == ("BAD_INPUT", "no audio", "pick a wav file")
