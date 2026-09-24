"""Backward-compatibility shim for separate.py.

All model separation implementations and inference pipelines have moved to `uvr.models`.
This file preserves 100% backward compatibility for existing imports and scripts.
"""

from __future__ import annotations

from uvr.models import (
    SeparateAttributes,
    SeparateDemucs,
    SeparateMDX,
    SeparateMDXC,
    SeparateVR,
    SeperateAttributes,
    SeperateDemucs,
    SeperateMDX,
    SeperateMDXC,
    SeperateVR,
    apply_replaygain,
    clear_gpu_cache,
    cpu,
    cuda_available,
    gather_sources,
    list_to_dictionary,
    loading_mix,
    mps_available,
    pitch_shift,
    prepare_mix,
    process_chain_model,
    process_secondary_model,
    rerun_mp3,
    save_format,
    vr_denoiser,
)

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
