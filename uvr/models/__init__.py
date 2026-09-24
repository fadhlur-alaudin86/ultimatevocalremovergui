"""Separation model engines and inference architectures for UVR.
"""

from __future__ import annotations

from uvr.models.base import (
    SeparateAttributes,
    SeperateAttributes,
    apply_replaygain,
    clear_gpu_cache,
    cpu,
    cuda_available,
    list_to_dictionary,
    loading_mix,
    mps_available,
    pitch_shift,
    prepare_mix,
    rerun_mp3,
    save_format,
    vr_denoiser,
)
from uvr.models.demucs import SeparateDemucs, SeperateDemucs
from uvr.models.mdx import SeparateMDX, SeperateMDX
from uvr.models.mdxc import SeparateMDXC, SeperateMDXC
from uvr.models.pipeline import (
    gather_sources,
    process_chain_model,
    process_secondary_model,
)
from uvr.models.vr import SeparateVR, SeperateVR

__all__ = [
    "SeparateAttributes",
    "SeparateDemucs",
    "SeparateMDX",
    "SeparateMDXC",
    "SeparateVR",
    "SeperateAttributes",
    "SeperateDemucs",
    "SeperateMDX",
    "SeperateMDXC",
    "SeperateVR",
    "apply_replaygain",
    "clear_gpu_cache",
    "cpu",
    "cuda_available",
    "gather_sources",
    "list_to_dictionary",
    "loading_mix",
    "mps_available",
    "pitch_shift",
    "prepare_mix",
    "process_chain_model",
    "process_secondary_model",
    "rerun_mp3",
    "save_format",
    "vr_denoiser",
]
