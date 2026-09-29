"""Central device resolution and AMP gating for inference.

Single source of truth for which torch device to run on, which
``device_type`` string is safe to pass to ``torch.autocast``, and whether
half-precision is allowed on the selected device.
"""

from __future__ import annotations

import torch

from gui_data.constants import CPU, CUDA_DEVICE, DEFAULT


class DeviceManager:
    """Pure classmethod helpers; no instance state."""

    @staticmethod
    def _device_type_str(device: torch.device | str) -> str:
        if isinstance(device, torch.device):
            return device.type
        return str(device).split(":")[0]

    @staticmethod
    def autocast_device(device: torch.device | str) -> str:
        """Return a safe ``torch.autocast`` device_type for ``device``.

        Only ``"cuda"`` is returned for CUDA devices; everything else
        (cpu, mps, unknown strings) normalizes to ``"cpu"`` so entering
        the autocast context with ``enabled=False`` can never raise on
        backends without autocast support.
        """
        return CUDA_DEVICE if DeviceManager._device_type_str(device) == CUDA_DEVICE else CPU

    @staticmethod
    def _device_index(device: torch.device | str) -> int:
        if isinstance(device, torch.device):
            return device.index if device.index is not None else 0
        parts = str(device).split(":")
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
        return 0

    @staticmethod
    def half_allowed(device: torch.device | str) -> bool:
        """True only on CUDA devices with compute capability >= (7, 0)."""
        if DeviceManager._device_type_str(device) != CUDA_DEVICE:
            return False
        try:
            if not torch.cuda.is_available():
                return False
            cap = torch.cuda.get_device_capability(DeviceManager._device_index(device))
            return cap[0] >= 7
        except Exception:
            return False

    @staticmethod
    def resolve(device_set: str | int, want_gpu: bool) -> torch.device | str:
        """Resolve the inference device from UI-level settings.

        ``device_set`` is ``DEFAULT`` (first CUDA device) or a CUDA index.
        Returns ``torch.device("cpu")`` when GPU is not wanted or CUDA is
        unavailable; returns the ``"mps"`` string on Apple Silicon (matching
        legacy ``base.py`` behavior). Raises ``ValueError`` for an
        out-of-range CUDA index.
        """
        import sys

        if not want_gpu or not torch.cuda.is_available():
            if sys.platform == "darwin" and want_gpu:
                try:
                    if torch.backends.mps.is_available():
                        return "mps"
                except Exception:
                    pass
            return torch.device(CPU)
        count = torch.cuda.device_count()
        if device_set == DEFAULT or device_set is None:
            return torch.device(CUDA_DEVICE)
        try:
            index = int(device_set)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid CUDA device selector: {device_set!r}") from None
        if index < 0 or index >= count:
            raise ValueError(f"CUDA device index {index} out of range (found {count})")
        return torch.device(f"{CUDA_DEVICE}:{index}")
