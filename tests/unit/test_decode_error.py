"""Tests for audio decode failure mapping (BAD_INPUT)."""

import pytest

from uvr.core.jobs import JobError
from uvr.models.base import prepare_mix


def test_prepare_mix_garbage_file_raises_bad_input(tmp_path):
    bad = tmp_path / "garbage.wav"
    bad.write_bytes(b"this is not audio data at all" * 100)
    with pytest.raises(JobError) as exc_info:
        prepare_mix(str(bad))
    assert exc_info.value.code == "BAD_INPUT"
