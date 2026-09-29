"""Frozen job snapshot and structured error for the inference service."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class JobSpec:
    """Immutable snapshot of everything a queued job needs.

    Captured at enqueue time so later UI edits never mutate pending tasks
    (the legacy ``QueueTask`` gap where half/device flags fell back to live
    root variables).
    """

    job_id: int
    process_method: str
    model_id: str | None
    input_paths: tuple[str, ...]
    export_path: str
    is_half_precision: bool
    is_gpu_conversion: bool
    device_set: str | int
    save_format: str
    wav_type_set: str
    mp3_bit_set: str
    is_model_sample_mode: bool
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_paths", tuple(self.input_paths))


@dataclass(frozen=True)
class JobError(Exception):
    """Structured backend failure for views to render actionably."""

    code: str
    message: str
    hint: str
