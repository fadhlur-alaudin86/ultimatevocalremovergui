"""Tests for DeviceManager device resolution and AMP gating."""

import pytest
import torch

from uvr.core.device_manager import DeviceManager


def test_autocast_device_never_returns_mps():
    assert DeviceManager.autocast_device("mps") == "cpu"


def test_half_allowed_requires_cuda_cc7():
    assert DeviceManager.half_allowed(torch.device("cpu")) is False


def test_resolve_bad_index_raises():
    if not torch.cuda.is_available():
        pytest.skip("needs CUDA for index range check")
    with pytest.raises(ValueError):
        DeviceManager.resolve(99, want_gpu=True)
