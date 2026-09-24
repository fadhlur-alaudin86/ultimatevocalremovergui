"""Settings management, serialization, variable loading, and defaults for UVR GUI.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from gui_data.app_size_values import FONT_SIZE_1, MENU_PADDING_1
from gui_data.constants import (
    CANCEL_TEXT,
    DEF_OPT,
    DEFAULT_DATA,
    DEMUCS_ARCH_TYPE,
    ENSEMBLE_INPUT_RULE,
    ENSEMBLE_MODE,
    EXIT_DOWNLOAD_ERROR,
    FULL_APP_SET_TEXT,
    MDX_ARCH_TYPE,
    NAME_SETTINGS_TEXT,
    OPT_SEPARATOR_SAVE,
    REG_SAVE_INPUT,
    RESET_ALL_TO_DEFAULT_WARNING,
    RESET_TO_DEFAULT,
    SAMPLE_MODE_CHECKBOX,
    SAVE_CURRENT_SETTINGS_TEXT,
    SAVE_SET_OPTIONS,
    SAVE_SETTINGS,
    SAVE_TEXT,
    SELECT_SAVED_SET,
    VR_ARCH_PM,
)
from uvr.constants import (
    ENSEMBLE_TEMP_PATH,
    MAIN_FONT_NAME,
    SAMPLE_CLIP_PATH,
    SETTINGS_CACHE_DIR,
)
from uvr.core.settings import save_data
from uvr.utils.file_utils import remove_temps

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages application settings persistence, Tkinter variable binding, and profiles."""

    def __init__(self, root: Any) -> None:
        self.root = root

    def load_to_default_confirm(self) -> None:
        """Prompts confirmation and resets all configuration parameters to system defaults."""
        confirm = messagebox.askyesno(
            parent=self.root,
            title=RESET_ALL_TO_DEFAULT_WARNING[0],
            message=RESET_ALL_TO_DEFAULT_WARNING[1],
        )
        if not confirm:
            return

        self.load_saved_settings(DEFAULT_DATA, is_default_reset=True)
        self.root.update_checkbox_text()

        if (
            self.root.pre_proc_model_toggle is not None
            and self.root.is_open_menu_advanced_demucs_options.get()
        ):
            self.root.pre_proc_model_toggle()

        if self.root.change_state_lambda is not None and (
            self.root.is_open_menu_advanced_vr_options.get()
            or self.root.is_open_menu_advanced_mdx_options.get()
            or self.root.is_open_menu_advanced_demucs_options.get()
        ):
            self.root.change_state_lambda()

    def load_saved_vars(self, data: dict[str, Any]) -> None:
        """Initializes all primary Tkinter variables on root with values from settings dict."""
        self.root.active_custom_config_name = data.get("active_custom_config_name", None)
        self.root.active_ensemble_name = data.get("active_ensemble_name", None)
        self.root.ensemble_model_settings = data.get("ensemble_model_settings", {})
        for key, value in DEFAULT_DATA.items():
            if key not in data:
                data[key] = value
                data["batch_size"] = DEF_OPT

        self.root.chosen_process_method_var = tk.StringVar(value=data["chosen_process_method"])

        # VR Architecture Vars
        self.root.vr_model_var = tk.StringVar(value=data["vr_model"])
        self.root.aggression_setting_var = tk.StringVar(value=data["aggression_setting"])
        self.root.window_size_var = tk.StringVar(value=data["window_size"])
        self.root.mdx_segment_size_var = tk.StringVar(value=data["mdx_segment_size"])
        self.root.batch_size_var = tk.StringVar(value=data["batch_size"])
        self.root.crop_size_var = tk.StringVar(value=data["crop_size"])
        self.root.is_tta_var = tk.BooleanVar(value=data["is_tta"])
        self.root.is_mdx_tta_var = tk.BooleanVar(value=data.get("is_mdx_tta", False))
        self.root.is_demucs_tta_var = tk.BooleanVar(value=data.get("is_demucs_tta", False))
        self.root.is_output_image_var = tk.BooleanVar(value=data["is_output_image"])
        self.root.is_post_process_var = tk.BooleanVar(value=data["is_post_process"])
        self.root.is_high_end_process_var = tk.BooleanVar(value=data["is_high_end_process"])
        self.root.post_process_threshold_var = tk.StringVar(value=data["post_process_threshold"])
        self.root.vr_voc_inst_secondary_model_var = tk.StringVar(
            value=data["vr_voc_inst_secondary_model"]
        )
        self.root.vr_other_secondary_model_var = tk.StringVar(
            value=data["vr_other_secondary_model"]
        )
        self.root.vr_bass_secondary_model_var = tk.StringVar(
            value=data["vr_bass_secondary_model"]
        )
        self.root.vr_drums_secondary_model_var = tk.StringVar(
            value=data["vr_drums_secondary_model"]
        )
        self.root.vr_is_secondary_model_activate_var = tk.BooleanVar(
            value=data["vr_is_secondary_model_activate"]
        )
        self.root.vr_voc_inst_secondary_model_scale_var = tk.StringVar(
            value=data["vr_voc_inst_secondary_model_scale"]
        )
        self.root.vr_other_secondary_model_scale_var = tk.StringVar(
            value=data["vr_other_secondary_model_scale"]
        )
        self.root.vr_bass_secondary_model_scale_var = tk.StringVar(
            value=data["vr_bass_secondary_model_scale"]
        )
        self.root.vr_drums_secondary_model_scale_var = tk.StringVar(
            value=data["vr_drums_secondary_model_scale"]
        )

        # Demucs Vars
        self.root.demucs_model_var = tk.StringVar(value=data["demucs_model"])
        self.root.segment_var = tk.StringVar(value=data["segment"])
        self.root.overlap_var = tk.StringVar(value=data["overlap"])
        self.root.overlap_mdx_var = tk.StringVar(value=data["overlap_mdx"])
        self.root.overlap_mdx23_var = tk.StringVar(value=data["overlap_mdx23"])
        self.root.shifts_var = tk.StringVar(value=data["shifts"])
        self.root.chunks_demucs_var = tk.StringVar(value=data["chunks_demucs"])
        self.root.margin_demucs_var = tk.StringVar(value=data["margin_demucs"])
        self.root.is_chunk_demucs_var = tk.BooleanVar(value=data["is_chunk_demucs"])
        self.root.is_chunk_mdxnet_var = tk.BooleanVar(value=False)
        self.root.is_primary_stem_only_Demucs_var = tk.BooleanVar(
            value=data["is_primary_stem_only_Demucs"]
        )
        self.root.is_secondary_stem_only_Demucs_var = tk.BooleanVar(
            value=data["is_secondary_stem_only_Demucs"]
        )
        self.root.is_split_mode_var = tk.BooleanVar(value=data["is_split_mode"])
        self.root.is_demucs_combine_stems_var = tk.BooleanVar(
            value=data["is_demucs_combine_stems"]
        )
        self.root.is_mdx23_combine_stems_var = tk.BooleanVar(
            value=data["is_mdx23_combine_stems"]
        )
        self.root.demucs_voc_inst_secondary_model_var = tk.StringVar(
            value=data["demucs_voc_inst_secondary_model"]
        )
        self.root.demucs_other_secondary_model_var = tk.StringVar(
            value=data["demucs_other_secondary_model"]
        )
        self.root.demucs_bass_secondary_model_var = tk.StringVar(
            value=data["demucs_bass_secondary_model"]
        )
        self.root.demucs_drums_secondary_model_var = tk.StringVar(
            value=data["demucs_drums_secondary_model"]
        )
        self.root.demucs_is_secondary_model_activate_var = tk.BooleanVar(
            value=data["demucs_is_secondary_model_activate"]
        )
        self.root.demucs_voc_inst_secondary_model_scale_var = tk.StringVar(
            value=data["demucs_voc_inst_secondary_model_scale"]
        )
        self.root.demucs_other_secondary_model_scale_var = tk.StringVar(
            value=data["demucs_other_secondary_model_scale"]
        )
        self.root.demucs_bass_secondary_model_scale_var = tk.StringVar(
            value=data["demucs_bass_secondary_model_scale"]
        )
        self.root.demucs_drums_secondary_model_scale_var = tk.StringVar(
            value=data["demucs_drums_secondary_model_scale"]
        )
        self.root.demucs_pre_proc_model_var = tk.StringVar(value=data["demucs_pre_proc_model"])
        self.root.is_demucs_pre_proc_model_activate_var = tk.BooleanVar(
            value=data["is_demucs_pre_proc_model_activate"]
        )
        self.root.is_demucs_pre_proc_model_inst_mix_var = tk.BooleanVar(
            value=data["is_demucs_pre_proc_model_inst_mix"]
        )

        # MDX-Net Vars
        self.root.mdx_net_model_var = tk.StringVar(value=data["mdx_net_model"])
        self.root.chunks_var = tk.StringVar(value=data["chunks"])
        self.root.margin_var = tk.StringVar(value=data["margin"])
        self.root.compensate_var = tk.StringVar(value=data["compensate"])
        self.root.denoise_option_var = tk.StringVar(value=data["denoise_option"])
        self.root.phase_option_var = tk.StringVar(value=data["phase_option"])
        self.root.phase_shifts_var = tk.StringVar(value=data["phase_shifts"])
        self.root.is_save_align_var = tk.BooleanVar(value=data["is_save_align"])
        self.root.is_match_silence_var = tk.BooleanVar(value=data["is_match_silence"])
        self.root.is_spec_match_var = tk.BooleanVar(value=data["is_spec_match"])
        self.root.is_match_frequency_pitch_var = tk.BooleanVar(
            value=data["is_match_frequency_pitch"]
        )
        self.root.is_mdx_c_seg_def_var = tk.BooleanVar(value=data["is_mdx_c_seg_def"])
        self.root.is_invert_spec_var = tk.BooleanVar(value=data["is_invert_spec"])
        self.root.is_deverb_vocals_var = tk.BooleanVar(value=data["is_deverb_vocals"])
        self.root.vocal_deverb_model_var = tk.StringVar(value=data["vocal_deverb_model"])
        self.root.deverb_vocal_opt_var = tk.StringVar(value=data["deverb_vocal_opt"])
        self.root.voc_split_save_opt_var = tk.StringVar(value=data["voc_split_save_opt"])
        self.root.is_mixer_mode_var = tk.BooleanVar(value=data["is_mixer_mode"])
        self.root.mdx_batch_size_var = tk.StringVar(value=data["mdx_batch_size"])
        self.root.mdx_voc_inst_secondary_model_var = tk.StringVar(
            value=data["mdx_voc_inst_secondary_model"]
        )
        self.root.mdx_other_secondary_model_var = tk.StringVar(
            value=data["mdx_other_secondary_model"]
        )
        self.root.mdx_bass_secondary_model_var = tk.StringVar(
            value=data["mdx_bass_secondary_model"]
        )
        self.root.mdx_drums_secondary_model_var = tk.StringVar(
            value=data["mdx_drums_secondary_model"]
        )
        self.root.mdx_is_secondary_model_activate_var = tk.BooleanVar(
            value=data["mdx_is_secondary_model_activate"]
        )
        self.root.mdx_voc_inst_secondary_model_scale_var = tk.StringVar(
            value=data["mdx_voc_inst_secondary_model_scale"]
        )
        self.root.mdx_other_secondary_model_scale_var = tk.StringVar(
            value=data["mdx_other_secondary_model_scale"]
        )
        self.root.mdx_bass_secondary_model_scale_var = tk.StringVar(
            value=data["mdx_bass_secondary_model_scale"]
        )
        self.root.mdx_drums_secondary_model_scale_var = tk.StringVar(
            value=data["mdx_drums_secondary_model_scale"]
        )
        self.root.is_mdxnet_c_model_var = tk.BooleanVar(value=False)

        # Ensemble Vars
        self.root.is_save_all_outputs_ensemble_var = tk.BooleanVar(
            value=data["is_save_all_outputs_ensemble"]
        )
        self.root.is_append_ensemble_name_var = tk.BooleanVar(
            value=data["is_append_ensemble_name"]
        )

        # Audio Tool Vars
        self.root.chosen_audio_tool_var = tk.StringVar(value=data["chosen_audio_tool"])
        self.root.choose_algorithm_var = tk.StringVar(value=data["choose_algorithm"])
        self.root.time_stretch_rate_var = tk.StringVar(value=data["time_stretch_rate"])
        self.root.pitch_rate_var = tk.StringVar(value=data["pitch_rate"])
        self.root.is_time_correction_var = tk.BooleanVar(value=data["is_time_correction"])

        # Shared Vars
        self.root.semitone_shift_var = tk.StringVar(value=data["semitone_shift"])
        self.root.mp3_bit_set_var = tk.StringVar(value=data["mp3_bit_set"])
        self.root.save_format_var = tk.StringVar(value=data["save_format"])
        self.root.wav_type_set_var = tk.StringVar(value=data["wav_type_set"])
        self.root.device_set_var = tk.StringVar(value=data["device_set"])
        self.root.user_code_var = tk.StringVar(value=data["user_code"])
        self.root.is_gpu_conversion_var = tk.BooleanVar(value=data["is_gpu_conversion"])
        self.root.is_half_precision_var = tk.BooleanVar(
            value=data.get("is_half_precision", False)
        )
        self.root.is_primary_stem_only_var = tk.BooleanVar(value=data["is_primary_stem_only"])
        self.root.is_secondary_stem_only_var = tk.BooleanVar(
            value=data["is_secondary_stem_only"]
        )
        self.root.is_testing_audio_var = tk.BooleanVar(value=data["is_testing_audio"])
        self.root.is_auto_update_model_params_var = tk.BooleanVar(value=True)
        self.root.is_auto_update_model_params = data["is_auto_update_model_params"]
        self.root.is_add_model_name_var = tk.BooleanVar(value=data["is_add_model_name"])
        self.root.is_accept_any_input_var = tk.BooleanVar(value=data["is_accept_any_input"])
        self.root.is_task_complete_var = tk.BooleanVar(value=data["is_task_complete"])
        self.root.is_normalization_var = tk.BooleanVar(value=data["is_normalization"])
        self.root.is_replaygain_var = tk.BooleanVar(value=data.get("is_replaygain", False))
        self.root.is_use_opencl_var = tk.BooleanVar(value=data.get("is_use_opencl", False))
        self.root.is_wav_ensemble_var = tk.BooleanVar(value=data["is_wav_ensemble"])
        self.root.is_create_model_folder_var = tk.BooleanVar(value=data["is_create_model_folder"])
        self.root.help_hints_var = tk.BooleanVar(value=data["help_hints_var"])
        self.root.model_sample_mode_var = tk.BooleanVar(value=data["model_sample_mode"])
        self.root.model_sample_mode_duration_var = tk.StringVar(
            value=data["model_sample_mode_duration"]
        )
        self.root.model_sample_mode_duration_checkbox_var = tk.StringVar(
            value=SAMPLE_MODE_CHECKBOX(self.root.model_sample_mode_duration_var.get())
        )
        self.root.model_sample_mode_duration_label_var = tk.StringVar(
            value=f"{self.root.model_sample_mode_duration_var.get()} Seconds"
        )
        self.root.set_vocal_splitter_var = tk.StringVar(value=data["set_vocal_splitter"])
        self.root.is_set_vocal_splitter_var = tk.BooleanVar(value=data["is_set_vocal_splitter"])
        self.root.is_save_inst_set_vocal_splitter_var = tk.BooleanVar(
            value=data["is_save_inst_set_vocal_splitter"]
        )

        # Path Vars
        self.root.export_path_var = tk.StringVar(value=data["export_path"])
        self.root.inputPaths = data["input_paths"]
        self.root.lastDir = data["lastDir"]

        # DualPaths-Align
        self.root.time_window_var = tk.StringVar(value=data["time_window"])
        self.root.intro_analysis_var = tk.StringVar(value=data["intro_analysis"])
        self.root.db_analysis_var = tk.StringVar(value=data["db_analysis"])

        self.root.fileOneEntry_var = tk.StringVar(value=data["fileOneEntry"])
        self.root.fileOneEntry_Full_var = tk.StringVar(value=data["fileOneEntry_Full"])
        self.root.fileTwoEntry_var = tk.StringVar(value=data["fileTwoEntry"])
        self.root.fileTwoEntry_Full_var = tk.StringVar(value=data["fileTwoEntry_Full"])
        self.root.DualBatch_inputPaths = data["DualBatch_inputPaths"]

    def load_saved_settings(
        self,
        loaded_setting: dict[str, Any],
        process_method: Any = None,
        is_default_reset: bool = False,
    ) -> None:
        """Applies saved configuration settings to active Tkinter variables."""
        for key, value in DEFAULT_DATA.items():
            if key not in loaded_setting:
                loaded_setting[key] = value
                loaded_setting["batch_size"] = DEF_OPT

        is_default_reset = (
            True if process_method == ENSEMBLE_MODE or is_default_reset else False
        )

        saved_process_method = loaded_setting.get("chosen_process_method", process_method)
        effective_method = saved_process_method if saved_process_method else process_method

        if effective_method and effective_method != process_method:
            self.root.chosen_process_method_var.set(effective_method)
        self.root.selection_action_process_method(
            effective_method or process_method, is_from_conv_menu=True
        )

        if process_method == VR_ARCH_PM or effective_method == VR_ARCH_PM or is_default_reset:
            self.root.vr_model_var.set(loaded_setting["vr_model"])
            self.root.aggression_setting_var.set(loaded_setting["aggression_setting"])
            self.root.window_size_var.set(loaded_setting["window_size"])
            self.root.mdx_segment_size_var.set(loaded_setting["mdx_segment_size"])
            self.root.batch_size_var.set(loaded_setting["batch_size"])
            self.root.crop_size_var.set(loaded_setting["crop_size"])
            if "is_tta" in loaded_setting:
                self.root.is_tta_var.set(loaded_setting["is_tta"])
                self.root.is_mdx_tta_var.set(loaded_setting.get("is_mdx_tta", False))
                self.root.is_demucs_tta_var.set(loaded_setting.get("is_demucs_tta", False))
            self.root.is_output_image_var.set(loaded_setting["is_output_image"])
            self.root.is_post_process_var.set(loaded_setting["is_post_process"])
            self.root.is_high_end_process_var.set(loaded_setting["is_high_end_process"])
            self.root.post_process_threshold_var.set(loaded_setting["post_process_threshold"])
            self.root.vr_voc_inst_secondary_model_var.set(
                loaded_setting["vr_voc_inst_secondary_model"]
            )
            self.root.vr_other_secondary_model_var.set(loaded_setting["vr_other_secondary_model"])
            self.root.vr_bass_secondary_model_var.set(loaded_setting["vr_bass_secondary_model"])
            self.root.vr_drums_secondary_model_var.set(loaded_setting["vr_drums_secondary_model"])
            self.root.vr_is_secondary_model_activate_var.set(
                loaded_setting["vr_is_secondary_model_activate"]
            )
            self.root.vr_voc_inst_secondary_model_scale_var.set(
                loaded_setting["vr_voc_inst_secondary_model_scale"]
            )
            self.root.vr_other_secondary_model_scale_var.set(
                loaded_setting["vr_other_secondary_model_scale"]
            )
            self.root.vr_bass_secondary_model_scale_var.set(
                loaded_setting["vr_bass_secondary_model_scale"]
            )
            self.root.vr_drums_secondary_model_scale_var.set(
                loaded_setting["vr_drums_secondary_model_scale"]
            )
            self.root.selection_action_models(loaded_setting["vr_model"])

        if (
            process_method == DEMUCS_ARCH_TYPE
            or effective_method == DEMUCS_ARCH_TYPE
            or is_default_reset
        ):
            self.root.demucs_model_var.set(loaded_setting["demucs_model"])
            self.root.segment_var.set(loaded_setting["segment"])
            self.root.overlap_var.set(loaded_setting["overlap"])
            self.root.shifts_var.set(loaded_setting["shifts"])
            self.root.chunks_demucs_var.set(loaded_setting["chunks_demucs"])
            self.root.margin_demucs_var.set(loaded_setting["margin_demucs"])
            self.root.is_chunk_demucs_var.set(loaded_setting["is_chunk_demucs"])
            self.root.is_chunk_mdxnet_var.set(loaded_setting["is_chunk_mdxnet"])
            self.root.is_primary_stem_only_Demucs_var.set(
                loaded_setting["is_primary_stem_only_Demucs"]
            )
            self.root.is_secondary_stem_only_Demucs_var.set(
                loaded_setting["is_secondary_stem_only_Demucs"]
            )
            self.root.is_split_mode_var.set(loaded_setting["is_split_mode"])
            self.root.is_demucs_combine_stems_var.set(loaded_setting["is_demucs_combine_stems"])
            self.root.is_mdx23_combine_stems_var.set(loaded_setting["is_mdx23_combine_stems"])
            self.root.demucs_voc_inst_secondary_model_var.set(
                loaded_setting["demucs_voc_inst_secondary_model"]
            )
            self.root.demucs_other_secondary_model_var.set(
                loaded_setting["demucs_other_secondary_model"]
            )
            self.root.demucs_bass_secondary_model_var.set(
                loaded_setting["demucs_bass_secondary_model"]
            )
            self.root.demucs_drums_secondary_model_var.set(
                loaded_setting["demucs_drums_secondary_model"]
            )
            self.root.demucs_is_secondary_model_activate_var.set(
                loaded_setting["demucs_is_secondary_model_activate"]
            )
            self.root.demucs_voc_inst_secondary_model_scale_var.set(
                loaded_setting["demucs_voc_inst_secondary_model_scale"]
            )
            self.root.demucs_other_secondary_model_scale_var.set(
                loaded_setting["demucs_other_secondary_model_scale"]
            )
            self.root.demucs_bass_secondary_model_scale_var.set(
                loaded_setting["demucs_bass_secondary_model_scale"]
            )
            self.root.demucs_drums_secondary_model_scale_var.set(
                loaded_setting["demucs_drums_secondary_model_scale"]
            )
            self.root.demucs_stems_var.set(loaded_setting["demucs_stems"])
            self.root.mdxnet_stems_var.set(loaded_setting["mdx_stems"])
            self.root.update_stem_checkbox_labels(self.root.demucs_stems_var.get(), demucs=True)
            self.root.demucs_pre_proc_model_var.set(loaded_setting["demucs_pre_proc_model"])
            self.root.is_demucs_pre_proc_model_activate_var.set(
                loaded_setting["is_demucs_pre_proc_model_activate"]
            )
            self.root.is_demucs_pre_proc_model_inst_mix_var.set(
                loaded_setting["is_demucs_pre_proc_model_inst_mix"]
            )
            self.root.selection_action_models(loaded_setting["demucs_model"])
            self.root.segment_var.set(loaded_setting["segment"])
            self.root.overlap_var.set(loaded_setting["overlap"])

        if process_method == MDX_ARCH_TYPE or effective_method == MDX_ARCH_TYPE or is_default_reset:
            self.root.mdx_net_model_var.set(loaded_setting["mdx_net_model"])
            self.root.mdx_segment_size_var.set(loaded_setting["mdx_segment_size"])
            self.root.chunks_var.set(loaded_setting["chunks"])
            self.root.margin_var.set(loaded_setting["margin"])
            self.root.compensate_var.set(loaded_setting["compensate"])
            self.root.denoise_option_var.set(loaded_setting["denoise_option"])
            self.root.is_match_frequency_pitch_var.set(loaded_setting["is_match_frequency_pitch"])
            self.root.overlap_mdx_var.set(loaded_setting["overlap_mdx"])
            self.root.overlap_mdx23_var.set(loaded_setting["overlap_mdx23"])
            self.root.is_mdx_c_seg_def_var.set(loaded_setting["is_mdx_c_seg_def"])
            self.root.is_invert_spec_var.set(loaded_setting["is_invert_spec"])
            self.root.is_mixer_mode_var.set(loaded_setting["is_mixer_mode"])
            self.root.mdx_batch_size_var.set(loaded_setting["mdx_batch_size"])
            self.root.mdx_voc_inst_secondary_model_var.set(
                loaded_setting["mdx_voc_inst_secondary_model"]
            )
            self.root.mdx_other_secondary_model_var.set(loaded_setting["mdx_other_secondary_model"])
            self.root.mdx_bass_secondary_model_var.set(loaded_setting["mdx_bass_secondary_model"])
            self.root.mdx_drums_secondary_model_var.set(loaded_setting["mdx_drums_secondary_model"])
            self.root.mdx_is_secondary_model_activate_var.set(
                loaded_setting["mdx_is_secondary_model_activate"]
            )
            self.root.mdx_voc_inst_secondary_model_scale_var.set(
                loaded_setting["mdx_voc_inst_secondary_model_scale"]
            )
            self.root.mdx_other_secondary_model_scale_var.set(
                loaded_setting["mdx_other_secondary_model_scale"]
            )
            self.root.mdx_bass_secondary_model_scale_var.set(
                loaded_setting["mdx_bass_secondary_model_scale"]
            )
            self.root.mdx_drums_secondary_model_scale_var.set(
                loaded_setting["mdx_drums_secondary_model_scale"]
            )
            self.root.selection_action_models(loaded_setting["mdx_net_model"])
            self.root.mdx_segment_size_var.set(loaded_setting["mdx_segment_size"])
            self.root.overlap_mdx_var.set(loaded_setting["overlap_mdx"])
            self.root.overlap_mdx23_var.set(loaded_setting["overlap_mdx23"])

        if is_default_reset:
            self.root.is_save_all_outputs_ensemble_var.set(
                loaded_setting["is_save_all_outputs_ensemble"]
            )
            self.root.is_append_ensemble_name_var.set(loaded_setting["is_append_ensemble_name"])
            self.root.choose_algorithm_var.set(loaded_setting["choose_algorithm"])
            self.root.time_stretch_rate_var.set(loaded_setting["time_stretch_rate"])
            self.root.pitch_rate_var.set(loaded_setting["pitch_rate"])
            self.root.is_time_correction_var.set(loaded_setting["is_time_correction"])
            self.root.phase_option_var.set(loaded_setting["phase_option"])
            self.root.phase_shifts_var.set(loaded_setting["phase_shifts"])
            self.root.is_save_align_var.set(loaded_setting["is_save_align"])
            self.root.time_window_var.set(loaded_setting["time_window"])
            self.root.is_match_silence_var.set(loaded_setting["is_match_silence"])
            self.root.is_spec_match_var.set(loaded_setting["is_spec_match"])
            self.root.intro_analysis_var.set(loaded_setting["intro_analysis"])
            self.root.db_analysis_var.set(loaded_setting["db_analysis"])
            self.root.fileOneEntry_var.set(loaded_setting["fileOneEntry"])
            self.root.fileOneEntry_Full_var.set(loaded_setting["fileOneEntry_Full"])
            self.root.fileTwoEntry_var.set(loaded_setting["fileTwoEntry"])
            self.root.fileTwoEntry_Full_var.set(loaded_setting["fileTwoEntry_Full"])
            self.root.DualBatch_inputPaths = []

        self.root.is_primary_stem_only_var.set(loaded_setting["is_primary_stem_only"])
        self.root.is_secondary_stem_only_var.set(loaded_setting["is_secondary_stem_only"])
        self.root.is_testing_audio_var.set(loaded_setting["is_testing_audio"])
        self.root.is_auto_update_model_params_var.set(
            loaded_setting["is_auto_update_model_params"]
        )
        self.root.is_add_model_name_var.set(loaded_setting["is_add_model_name"])
        self.root.is_accept_any_input_var.set(loaded_setting["is_accept_any_input"])
        self.root.is_task_complete_var.set(loaded_setting["is_task_complete"])
        self.root.is_create_model_folder_var.set(loaded_setting["is_create_model_folder"])
        self.root.mp3_bit_set_var.set(loaded_setting["mp3_bit_set"])
        self.root.semitone_shift_var.set(loaded_setting["semitone_shift"])
        self.root.save_format_var.set(loaded_setting["save_format"])
        self.root.wav_type_set_var.set(loaded_setting["wav_type_set"])
        self.root.device_set_var.set(loaded_setting["device_set"])
        self.root.user_code_var.set(loaded_setting["user_code"])
        self.root.chosen_audio_tool_var.set(
            loaded_setting.get("chosen_audio_tool", DEFAULT_DATA.get("chosen_audio_tool", ""))
        )

        self.root.is_gpu_conversion_var.set(loaded_setting["is_gpu_conversion"])
        self.root.is_half_precision_var.set(loaded_setting.get("is_half_precision", False))
        self.root.is_normalization_var.set(loaded_setting["is_normalization"])
        self.root.is_replaygain_var.set(loaded_setting.get("is_replaygain", False))
        self.root.is_use_opencl_var.set(loaded_setting.get("is_use_opencl", False))
        self.root.is_wav_ensemble_var.set(loaded_setting["is_wav_ensemble"])
        self.root.help_hints_var.set(loaded_setting["help_hints_var"])
        self.root.set_vocal_splitter_var.set(loaded_setting["set_vocal_splitter"])
        self.root.is_set_vocal_splitter_var.set(loaded_setting["is_set_vocal_splitter"])
        self.root.is_save_inst_set_vocal_splitter_var.set(
            loaded_setting["is_save_inst_set_vocal_splitter"]
        )
        self.root.deverb_vocal_opt_var.set(loaded_setting["deverb_vocal_opt"])
        self.root.vocal_deverb_model_var.set(loaded_setting["vocal_deverb_model"])
        self.root.voc_split_save_opt_var.set(loaded_setting["voc_split_save_opt"])
        self.root.is_deverb_vocals_var.set(loaded_setting["is_deverb_vocals"])

        self.root.model_sample_mode_var.set(loaded_setting["model_sample_mode"])
        self.root.model_sample_mode_duration_var.set(loaded_setting["model_sample_mode_duration"])
        self.root.model_sample_mode_duration_checkbox_var.set(
            SAMPLE_MODE_CHECKBOX(self.root.model_sample_mode_duration_var.get())
        )
        self.root.model_sample_mode_duration_label_var.set(
            f"{self.root.model_sample_mode_duration_var.get()} Seconds"
        )

    def save_values(
        self,
        app_close: bool = True,
        is_restart: bool = False,
        is_auto_save: bool = False,
    ) -> dict[str, Any] | None:
        """Serializes current application variable values to dict and saves to data.json."""
        main_settings = {
            "vr_model": self.root.vr_model_var.get(),
            "aggression_setting": self.root.aggression_setting_var.get(),
            "window_size": self.root.window_size_var.get(),
            "mdx_segment_size": self.root.mdx_segment_size_var.get(),
            "batch_size": self.root.batch_size_var.get(),
            "crop_size": self.root.crop_size_var.get(),
            "is_tta": self.root.is_tta_var.get(),
            "is_mdx_tta": self.root.is_mdx_tta_var.get(),
            "is_demucs_tta": self.root.is_demucs_tta_var.get(),
            "is_output_image": self.root.is_output_image_var.get(),
            "is_post_process": self.root.is_post_process_var.get(),
            "is_high_end_process": self.root.is_high_end_process_var.get(),
            "post_process_threshold": self.root.post_process_threshold_var.get(),
            "vr_voc_inst_secondary_model": self.root.vr_voc_inst_secondary_model_var.get(),
            "vr_other_secondary_model": self.root.vr_other_secondary_model_var.get(),
            "vr_bass_secondary_model": self.root.vr_bass_secondary_model_var.get(),
            "vr_drums_secondary_model": self.root.vr_drums_secondary_model_var.get(),
            "vr_is_secondary_model_activate": self.root.vr_is_secondary_model_activate_var.get(),
            "vr_voc_inst_secondary_model_scale": self.root.vr_voc_inst_secondary_model_scale_var.get(),
            "vr_other_secondary_model_scale": self.root.vr_other_secondary_model_scale_var.get(),
            "vr_bass_secondary_model_scale": self.root.vr_bass_secondary_model_scale_var.get(),
            "vr_drums_secondary_model_scale": self.root.vr_drums_secondary_model_scale_var.get(),
            "demucs_model": self.root.demucs_model_var.get(),
            "segment": self.root.segment_var.get(),
            "overlap": self.root.overlap_var.get(),
            "overlap_mdx": self.root.overlap_mdx_var.get(),
            "overlap_mdx23": self.root.overlap_mdx23_var.get(),
            "shifts": self.root.shifts_var.get(),
            "chunks_demucs": self.root.chunks_demucs_var.get(),
            "margin_demucs": self.root.margin_demucs_var.get(),
            "is_chunk_demucs": self.root.is_chunk_demucs_var.get(),
            "is_chunk_mdxnet": self.root.is_chunk_mdxnet_var.get(),
            "is_primary_stem_only_Demucs": self.root.is_primary_stem_only_Demucs_var.get(),
            "is_secondary_stem_only_Demucs": self.root.is_secondary_stem_only_Demucs_var.get(),
            "is_split_mode": self.root.is_split_mode_var.get(),
            "is_demucs_combine_stems": self.root.is_demucs_combine_stems_var.get(),
            "is_mdx23_combine_stems": self.root.is_mdx23_combine_stems_var.get(),
            "demucs_voc_inst_secondary_model": self.root.demucs_voc_inst_secondary_model_var.get(),
            "demucs_other_secondary_model": self.root.demucs_other_secondary_model_var.get(),
            "demucs_bass_secondary_model": self.root.demucs_bass_secondary_model_var.get(),
            "demucs_drums_secondary_model": self.root.demucs_drums_secondary_model_var.get(),
            "demucs_is_secondary_model_activate": self.root.demucs_is_secondary_model_activate_var.get(),
            "demucs_voc_inst_secondary_model_scale": self.root.demucs_voc_inst_secondary_model_scale_var.get(),
            "demucs_other_secondary_model_scale": self.root.demucs_other_secondary_model_scale_var.get(),
            "demucs_bass_secondary_model_scale": self.root.demucs_bass_secondary_model_scale_var.get(),
            "demucs_drums_secondary_model_scale": self.root.demucs_drums_secondary_model_scale_var.get(),
            "demucs_pre_proc_model": self.root.demucs_pre_proc_model_var.get(),
            "is_demucs_pre_proc_model_activate": self.root.is_demucs_pre_proc_model_activate_var.get(),
            "is_demucs_pre_proc_model_inst_mix": self.root.is_demucs_pre_proc_model_inst_mix_var.get(),
            "mdx_net_model": self.root.mdx_net_model_var.get(),
            "chunks": self.root.chunks_var.get(),
            "margin": self.root.margin_var.get(),
            "compensate": self.root.compensate_var.get(),
            "denoise_option": self.root.denoise_option_var.get(),
            "is_match_frequency_pitch": self.root.is_match_frequency_pitch_var.get(),
            "phase_option": self.root.phase_option_var.get(),
            "phase_shifts": self.root.phase_shifts_var.get(),
            "is_save_align": self.root.is_save_align_var.get(),
            "is_match_silence": self.root.is_match_silence_var.get(),
            "is_spec_match": self.root.is_spec_match_var.get(),
            "is_mdx_c_seg_def": self.root.is_mdx_c_seg_def_var.get(),
            "is_invert_spec": self.root.is_invert_spec_var.get(),
            "is_deverb_vocals": self.root.is_deverb_vocals_var.get(),
            "vocal_deverb_model": self.root.vocal_deverb_model_var.get(),
            "deverb_vocal_opt": self.root.deverb_vocal_opt_var.get(),
            "voc_split_save_opt": self.root.voc_split_save_opt_var.get(),
            "is_mixer_mode": self.root.is_mixer_mode_var.get(),
            "mdx_batch_size": self.root.mdx_batch_size_var.get(),
            "mdx_voc_inst_secondary_model": self.root.mdx_voc_inst_secondary_model_var.get(),
            "mdx_other_secondary_model": self.root.mdx_other_secondary_model_var.get(),
            "mdx_bass_secondary_model": self.root.mdx_bass_secondary_model_var.get(),
            "mdx_drums_secondary_model": self.root.mdx_drums_secondary_model_var.get(),
            "mdx_is_secondary_model_activate": self.root.mdx_is_secondary_model_activate_var.get(),
            "mdx_voc_inst_secondary_model_scale": self.root.mdx_voc_inst_secondary_model_scale_var.get(),
            "mdx_other_secondary_model_scale": self.root.mdx_other_secondary_model_scale_var.get(),
            "mdx_bass_secondary_model_scale": self.root.mdx_bass_secondary_model_scale_var.get(),
            "mdx_drums_secondary_model_scale": self.root.mdx_drums_secondary_model_scale_var.get(),
            "is_save_all_outputs_ensemble": self.root.is_save_all_outputs_ensemble_var.get(),
            "is_append_ensemble_name": self.root.is_append_ensemble_name_var.get(),
            "chosen_audio_tool": self.root.chosen_audio_tool_var.get(),
            "choose_algorithm": self.root.choose_algorithm_var.get(),
            "time_stretch_rate": self.root.time_stretch_rate_var.get(),
            "pitch_rate": self.root.pitch_rate_var.get(),
            "is_time_correction": self.root.is_time_correction_var.get(),
            "is_gpu_conversion": self.root.is_gpu_conversion_var.get(),
            "is_half_precision": self.root.is_half_precision_var.get(),
            "is_primary_stem_only": self.root.is_primary_stem_only_var.get(),
            "is_secondary_stem_only": self.root.is_secondary_stem_only_var.get(),
            "is_testing_audio": self.root.is_testing_audio_var.get(),
            "is_auto_update_model_params": self.root.is_auto_update_model_params_var.get(),
            "is_add_model_name": self.root.is_add_model_name_var.get(),
            "is_accept_any_input": self.root.is_accept_any_input_var.get(),
            "is_task_complete": self.root.is_task_complete_var.get(),
            "is_normalization": self.root.is_normalization_var.get(),
            "is_replaygain": self.root.is_replaygain_var.get(),
            "is_use_opencl": self.root.is_use_opencl_var.get(),
            "is_wav_ensemble": self.root.is_wav_ensemble_var.get(),
            "is_create_model_folder": self.root.is_create_model_folder_var.get(),
            "mp3_bit_set": self.root.mp3_bit_set_var.get(),
            "semitone_shift": self.root.semitone_shift_var.get(),
            "save_format": self.root.save_format_var.get(),
            "wav_type_set": self.root.wav_type_set_var.get(),
            "device_set": self.root.device_set_var.get(),
            "user_code": self.root.user_code_var.get(),
            "help_hints_var": self.root.help_hints_var.get(),
            "set_vocal_splitter": self.root.set_vocal_splitter_var.get(),
            "is_set_vocal_splitter": self.root.is_set_vocal_splitter_var.get(),
            "is_save_inst_set_vocal_splitter": self.root.is_save_inst_set_vocal_splitter_var.get(),
            "model_sample_mode": self.root.model_sample_mode_var.get(),
            "model_sample_mode_duration": self.root.model_sample_mode_duration_var.get(),
        }

        other_data = {
            "chosen_process_method": self.root.chosen_process_method_var.get(),
            "input_paths": self.root.inputPaths,
            "lastDir": self.root.lastDir,
            "export_path": self.root.export_path_var.get(),
            "time_window": self.root.time_window_var.get(),
            "intro_analysis": self.root.intro_analysis_var.get(),
            "db_analysis": self.root.db_analysis_var.get(),
            "fileOneEntry": self.root.fileOneEntry_var.get(),
            "fileOneEntry_Full": self.root.fileOneEntry_Full_var.get(),
            "fileTwoEntry": self.root.fileTwoEntry_var.get(),
            "fileTwoEntry_Full": self.root.fileTwoEntry_Full_var.get(),
            "DualBatch_inputPaths": self.root.DualBatch_inputPaths,
            "active_custom_config_name": self.root.active_custom_config_name,
            "active_ensemble_name": getattr(self.root, "active_ensemble_name", None),
            "ensemble_model_settings": getattr(self.root, "ensemble_model_settings", {}),
        }

        user_saved_extras = {
            "demucs_stems": self.root.demucs_stems_var.get(),
            "mdx_stems": self.root.mdxnet_stems_var.get(),
        }

        if app_close:
            save_data(data={**main_settings, **other_data})

            if self.root.thread_check(self.root.active_download_thread):
                self.root.error_dialoge(EXIT_DOWNLOAD_ERROR)
                return None

            if self.root.thread_check(self.root.active_processing_thread):
                confirm = messagebox.askyesno(
                    parent=self.root,
                    title="Active Process",
                    message="A process is currently running. Are you sure you want to exit? This will stop the active process and clear the queue.",
                )
                if confirm:
                    try:
                        self.root.active_processing_thread.terminate()
                    except Exception:
                        pass
                    self.root.is_process_stopped = True
                    self.root.processing_queue.clear()
                    if hasattr(self.root, "update_queue_ui_display"):
                        self.root.update_queue_ui_display()
                else:
                    return None

            remove_temps(ENSEMBLE_TEMP_PATH)
            remove_temps(SAMPLE_CLIP_PATH)
            self.root.delete_temps()

            if is_restart:
                try:
                    subprocess.Popen("UVR_Launcher.exe")
                except Exception:
                    subprocess.Popen('python "UVR.py"', shell=True)

            self.root.destroy()
            return None

        if is_auto_save:
            save_data(data={**main_settings, **other_data})
            return None

        return {**main_settings, **user_saved_extras}

    def get_settings_list(self) -> str:
        """Returns string representation of current application settings for debugging."""
        settings_dict = self.save_values(app_close=False) or {}
        settings_list = "\n".join(
            "".join(f"{key}: {value}")
            for key, value in settings_dict.items()
            if key != "user_code"
        )
        return f"\n{FULL_APP_SET_TEXT}:\n\n{settings_list}"

    def auto_save(self) -> None:
        """Periodically auto-saves application settings in background."""
        try:
            self.save_values(app_close=False, is_auto_save=True)
        except Exception as exc:
            logger.debug("Auto-save failed: %s", exc)

    def pop_up_save_current_settings(self) -> None:
        """Opens dialog to save current settings profile."""
        settings_save = tk.Toplevel(self.root)

        default_name = (
            self.root.active_custom_config_name if self.root.active_custom_config_name else ""
        )
        settings_save_var = tk.StringVar(value=default_name)

        settings_save_frame = self.root.menu_FRAME_SET(settings_save)
        settings_save_frame.grid(row=1)

        save_func = lambda: (
            self.pop_up_save_current_settings_sub_json_dump(settings_save_var.get()),
            settings_save.destroy(),
        )
        validation = lambda value: re.fullmatch(REG_SAVE_INPUT, value) is not None

        title_lbl = self.root.menu_title_LABEL_SET(
            settings_save_frame, SAVE_CURRENT_SETTINGS_TEXT
        )
        title_lbl.grid()

        name_lbl = self.root.menu_sub_LABEL_SET(settings_save_frame, NAME_SETTINGS_TEXT)
        name_lbl.grid(pady=MENU_PADDING_1)
        name_entry = ttk.Entry(
            settings_save_frame, textvariable=settings_save_var, justify="center", width=25
        )
        name_entry.grid(pady=MENU_PADDING_1)
        invalid_message = self.root.invalid_tooltip(name_entry)
        name_entry.bind(self.root.right_click_button, self.root.right_click_menu_popup)
        self.root.current_text_box = name_entry
        name_entry.focus_set()
        name_entry.icursor(tk.END)
        name_entry.select_range(0, tk.END)

        self.root.spacer_label(settings_save_frame)

        rules_lbl = tk.Label(
            settings_save_frame,
            text=ENSEMBLE_INPUT_RULE,
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
            foreground="#868687",
            justify="left",
        )
        rules_lbl.grid()

        save_btn = ttk.Button(
            settings_save_frame,
            text=SAVE_TEXT,
            command=lambda: save_func()
            if validation(settings_save_var.get())
            else invalid_message(),
        )
        save_btn.grid(pady=MENU_PADDING_1)

        cancel_btn = ttk.Button(
            settings_save_frame, text=CANCEL_TEXT, command=settings_save.destroy
        )
        cancel_btn.grid(pady=MENU_PADDING_1)

        self.root.menu_placement(settings_save, SAVE_CURRENT_SETTINGS_TEXT, pop_up=True)

    def pop_up_save_current_settings_sub_json_dump(self, settings_save_name: str) -> None:
        """Dumps current settings to a json file in SETTINGS_CACHE_DIR."""
        if settings_save_name:
            self.root.active_custom_config_name = settings_save_name
            self.root.save_current_settings_var.set(settings_save_name)
            file_name = settings_save_name.replace(" ", "_")
            current_settings = self.save_values(app_close=False)

            with open(
                os.path.join(SETTINGS_CACHE_DIR, f"{file_name}.json"),
                "w",
                encoding="utf-8",
            ) as outfile:
                outfile.write(json.dumps(current_settings, indent=4))

    def selection_action_saved_settings(
        self, selection: str, process_method: Any = None
    ) -> None:
        """Activates specific action based on selected settings entry."""
        chosen_process_method = (
            process_method if process_method else self.root.chosen_process_method_var.get()
        )

        if selection in SAVE_SET_OPTIONS:
            self.handle_special_options(selection, chosen_process_method)
        else:
            self.handle_saved_settings(selection, chosen_process_method)

        self.root.update_checkbox_text()

    def handle_special_options(self, selection: str, process_method: Any) -> None:
        """Handles special settings dropdown selections (Save, Reset to default, Separator)."""
        if selection == SAVE_SETTINGS:
            self.root.save_current_settings_var.set(SELECT_SAVED_SET)
            self.pop_up_save_current_settings()
        elif selection == RESET_TO_DEFAULT:
            self.root.save_current_settings_var.set(SELECT_SAVED_SET)
            self.root.active_custom_config_name = None
            self.load_saved_settings(DEFAULT_DATA, process_method)
        elif selection == OPT_SEPARATOR_SAVE:
            self.root.save_current_settings_var.set(SELECT_SAVED_SET)

    def handle_saved_settings(self, selection: str, process_method: Any) -> None:
        """Loads and applies a saved settings profile JSON from disk."""
        self.root.active_custom_config_name = selection.replace("_", " ")
        file_name = selection.replace(" ", "_")
        saved_path = os.path.join(SETTINGS_CACHE_DIR, f"{file_name}.json")

        if os.path.isfile(saved_path):
            with open(saved_path, encoding="utf-8") as file:
                saved_data = json.load(file)

            if saved_data:
                self.load_saved_settings(saved_data, process_method)
