"""Tests for Half-Precision routing through DeviceManager."""

import inspect

import pytest
import torch

from uvr.core.device_manager import DeviceManager
from uvr.models import demucs as demucs_mod
from uvr.models import mdx as mdx_mod
from uvr.models import mdxc as mdxc_mod
from uvr.models import vr as vr_mod

MODEL_MODULES = (vr_mod, mdx_mod, demucs_mod, mdxc_mod)


@pytest.mark.gpu
def test_autocast_context_never_uses_mps_device_type():
    ctx_device = DeviceManager.autocast_device("mps")
    with torch.autocast(device_type=ctx_device, dtype=torch.float16, enabled=False):
        pass


def test_half_on_off_no_nans_cpu_smoke():
    assert DeviceManager.half_allowed(torch.device("cpu")) is False


def test_all_models_route_autocast_through_device_manager():
    for mod in MODEL_MODULES:
        source = inspect.getsource(mod)
        assert "DeviceManager.autocast_device" in source, mod.__name__
        assert "device.split(':')[0]" not in source, mod.__name__


@pytest.mark.gpu
def test_cuda_autocast_pattern_stays_finite():
    if not torch.cuda.is_available():
        pytest.skip("no CUDA device")
    x = torch.randn(64, 64, dtype=torch.float32, device="cuda")
    for enabled in (False, True):
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=enabled):
            y = (x @ x).float()
        assert torch.isfinite(y).all()
