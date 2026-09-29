"""Per-method capability matrix, shared options, and legacy settings migrator.

Single source of truth for which options each process method owns. Flet
forms render dynamically from ``CAPABILITIES`` so a config can never appear
under a method that cannot use it.
"""

from __future__ import annotations

from gui_data.constants import (
    AUDIO_TOOLS,
    DEMUCS_ARCH_TYPE,
    ENSEMBLE_MODE,
    MDX_ARCH_TYPE,
    VR_ARCH_PM,
)

SETTINGS_VERSION = 2

SHARED_OPTIONS: list[str] = [
    "is_gpu_conversion",
    "device_set",
    "is_half_precision",
    "model_sample_mode",
    "model_sample_mode_duration",
    "save_format",
    "wav_type_set",
    "mp3_bit_set",
]

CAPABILITIES: dict[str, list[str]] = {
    VR_ARCH_PM: [
        "vr_model",
        "aggression_setting",
        "window_size",
        "batch_size",
        "crop_size",
        "is_tta",
        "is_post_process",
        "post_process_threshold",
        "is_high_end_process",
        "vr_voc_inst_secondary_model",
        "vr_other_secondary_model",
        "vr_bass_secondary_model",
        "vr_drums_secondary_model",
        "vr_is_secondary_model_activate",
        "vr_voc_inst_secondary_model_scale",
        "vr_other_secondary_model_scale",
        "vr_bass_secondary_model_scale",
        "vr_drums_secondary_model_scale",
    ],
    MDX_ARCH_TYPE: [
        "mdx_net_model",
        "mdx_segment_size",
        "overlap_mdx",
        "overlap_mdx23",
        "mdx_batch_size",
        "chunks",
        "margin",
        "compensate",
        "is_mdx_tta",
        "denoise_option",
        "is_mdx_c_seg_def",
        "is_invert_spec",
        "is_match_frequency_pitch",
        "is_mdx23_combine_stems",
        "mdx_voc_inst_secondary_model",
        "mdx_other_secondary_model",
        "mdx_bass_secondary_model",
        "mdx_drums_secondary_model",
        "mdx_is_secondary_model_activate",
        "mdx_voc_inst_secondary_model_scale",
        "mdx_other_secondary_model_scale",
        "mdx_bass_secondary_model_scale",
        "mdx_drums_secondary_model_scale",
        "mdx_stems",
        "is_chunk_mdxnet",
    ],
    DEMUCS_ARCH_TYPE: [
        "demucs_model",
        "segment",
        "shifts",
        "overlap",
        "is_split_mode",
        "is_demucs_tta",
        "is_chunk_demucs",
        "chunks_demucs",
        "margin_demucs",
        "is_demucs_combine_stems",
        "demucs_voc_inst_secondary_model",
        "demucs_other_secondary_model",
        "demucs_bass_secondary_model",
        "demucs_drums_secondary_model",
        "demucs_is_secondary_model_activate",
        "demucs_voc_inst_secondary_model_scale",
        "demucs_other_secondary_model_scale",
        "demucs_bass_secondary_model_scale",
        "demucs_drums_secondary_model_scale",
        "demucs_stems",
        "demucs_pre_proc_model",
        "is_demucs_pre_proc_model_activate",
        "is_demucs_pre_proc_model_inst_mix",
    ],
    ENSEMBLE_MODE: [
        "chosen_ensemble",
        "ensemble_main_stem",
        "ensemble_type",
        "is_save_all_outputs_ensemble",
        "is_append_ensemble_name",
        "is_wav_ensemble",
    ],
    AUDIO_TOOLS: [
        "chosen_audio_tool",
        "choose_algorithm",
        "time_stretch_rate",
        "pitch_rate",
        "phase_option",
        "phase_shifts",
        "is_save_align",
        "is_match_silence",
        "is_spec_match",
        "intro_analysis",
        "time_window",
        "db_analysis",
    ],
}

# Cross-method output and post-processing behavior. Rendered in the output
# section of every method form (not the always-visible shared row).
OUTPUT_OPTIONS: list[str] = [
    "is_primary_stem_only",
    "is_secondary_stem_only",
    "is_normalization",
    "is_replaygain",
    "semitone_shift",
    "is_deverb_vocals",
    "deverb_vocal_opt",
    "is_mixer_mode",
    "set_vocal_splitter",
    "is_set_vocal_splitter",
    "is_save_inst_set_vocal_splitter",
    "voc_split_save_opt",
    "is_add_model_name",
    "is_create_model_folder",
    "is_task_complete",
    "is_testing_audio",
    "is_use_opencl",
    "is_time_correction",
    "is_output_image",
    "is_auto_update_model_params",
    "is_accept_any_input",
]

# The legacy Demucs-only stem pair folds into the shared pair.
_LEGACY_STEM_FOLD = {
    "is_primary_stem_only_Demucs": "is_primary_stem_only",
    "is_secondary_stem_only_Demucs": "is_secondary_stem_only",
}

_KNOWN_KEYS: set[str] = set(SHARED_OPTIONS) | set(OUTPUT_OPTIONS)
for _options in CAPABILITIES.values():
    _KNOWN_KEYS.update(_options)


def is_known_option(key: str) -> bool:
    """True for store keys the GUI recognizes (submit merge filter)."""
    return key in _KNOWN_KEYS


def migrate_legacy(data: dict) -> tuple[dict, list[str]]:
    """Migrate a legacy flat settings dict toward the v2 schema.

    Returns ``(kept, unknown)``: known keys preserved, legacy Demucs stem
    keys folded into the shared pair, unknown keys dropped and reported for
    logging. Input is never mutated.
    """
    kept: dict = {}
    unknown: list[str] = []
    for key, value in data.items():
        if key in _LEGACY_STEM_FOLD:
            target = _LEGACY_STEM_FOLD[key]
            kept.setdefault(target, value)
        elif key in _KNOWN_KEYS:
            kept[key] = value
        else:
            unknown.append(key)
    return kept, sorted(unknown)
