"""Model metadata, configuration resolution, and topology definition.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

import yaml
from ml_collections import ConfigDict

from gui_data.constants import *
from lib_v5.vr_network.model_param_init import ModelParameters
from uvr.constants import (
    DEMUCS_MODELS_DIR,
    DEMUCS_NEWER_REPO_DIR,
    DENOISER_MODEL_PATH,
    MDX_C_CONFIG_PATH,
    MDX_HASH_DIR,
    MDX_MIXER_PATH,
    MDX_MODELS_DIR,
    VR_HASH_DIR,
    VR_MODELS_DIR,
    VR_PARAM_DIR,
)

logger = logging.getLogger(__name__)

# Shared hash cache across instances
model_hash_table: dict[str, str] = {}

# Context reference for UI callbacks / variables
_app_root = None


def set_app_root(root_instance: Any) -> None:
    """Set global UI/App root instance for variable access."""
    global _app_root
    _app_root = root_instance
    try:
        import sys
        if "UVR" in sys.modules:
            sys.modules["UVR"].root = root_instance
        if "__main__" in sys.modules:
            sys.modules["__main__"].root = root_instance
    except Exception:
        pass


def get_app_root() -> Any:
    """Retrieve the registered UI/App root instance."""
    return _app_root


class ModelData:
    """Encapsulates all metadata, model architecture resolution, and parameter

    configurations for separation models (VR, MDX-Net, MDX-C, Demucs).
    """

    def __init__(
        self,
        model_name: str,
        selected_process_method: str = ENSEMBLE_MODE,
        is_secondary_model: bool = False,
        primary_model_primary_stem: str | None = None,
        is_primary_model_primary_stem_only: bool = False,
        is_primary_model_secondary_stem_only: bool = False,
        is_pre_proc_model: bool = False,
        is_dry_check: bool = False,
        is_change_def: bool = False,
        is_get_hash_dir_only: bool = False,
        is_vocal_split_model: bool = False,
        root: Any = None,
    ):
        if root is None:
            root = get_app_root()

        self.root = root
        device_set = root.device_set_var.get() if root else DEFAULT
        self.ensemble_settings = (
            root.ensemble_model_settings.get(model_name, {})
            if (root and selected_process_method == ENSEMBLE_MODE)
            else {}
        )
        self.DENOISER_MODEL = DENOISER_MODEL_PATH
        self.deverber_model_name = root.vocal_deverb_model_var.get() if root else NO_MODEL
        self.is_deverb_vocals = root.is_deverb_vocals_var.get() if root else False

        # Don't recursively load deverber model if we are already loading a secondary model
        if self.is_deverb_vocals and not self.deverber_model_name == NO_MODEL and not is_secondary_model:
            deverber_arch_type = (
                VR_ARCH_TYPE if self.deverber_model_name == "UVR-DeEcho-DeReverb" else MDX_ARCH_TYPE
            )
            self.deverber_model = ModelData(
                self.deverber_model_name,
                selected_process_method=deverber_arch_type,
                is_secondary_model=True,
                root=root,
            )
        else:
            self.deverber_model = None
            self.is_deverb_vocals = False

        self.deverb_vocal_opt = DEVERB_MAPPER[root.deverb_vocal_opt_var.get()] if root else None
        self.is_denoise_model = (
            True
            if (root and root.denoise_option_var.get() == DENOISE_M and os.path.isfile(DENOISER_MODEL_PATH))
            else False
        )
        self.is_gpu_conversion = 0 if (root and root.is_gpu_conversion_var.get()) else -1
        self.is_normalization = root.is_normalization_var.get() if root else False
        self.is_replaygain = getattr(root, "is_replaygain_var", None).get() if root else False
        self.is_use_opencl = False
        self.is_primary_stem_only = root.is_primary_stem_only_var.get() if root else False
        self.is_secondary_stem_only = root.is_secondary_stem_only_var.get() if root else False
        self.is_denoise = True if (root and not root.denoise_option_var.get() == DENOISE_NONE) else False
        self.is_mdx_c_seg_def = root.is_mdx_c_seg_def_var.get() if root else False
        mdx_batch_val = (
            self.ensemble_settings.get("mdx_batch_size", root.mdx_batch_size_var.get()) if root else DEF_OPT
        )
        self.mdx_batch_size = 1 if mdx_batch_val == DEF_OPT else int(mdx_batch_val)
        self.mdxnet_stem_select = root.mdxnet_stems_var.get() if root else None

        demucs_overlap_val = (
            self.ensemble_settings.get("overlap", root.overlap_var.get()) if root else DEFAULT
        )
        self.overlap = float(demucs_overlap_val) if demucs_overlap_val != DEFAULT else 0.25

        mdx_overlap_val = (
            self.ensemble_settings.get("overlap_mdx", root.overlap_mdx_var.get()) if root else DEFAULT
        )
        self.overlap_mdx = float(mdx_overlap_val) if mdx_overlap_val != DEFAULT else mdx_overlap_val
        mdx23_overlap_val = (
            self.ensemble_settings.get("overlap_mdx23", root.overlap_mdx23_var.get()) if root else DEFAULT
        )
        self.overlap_mdx23 = (
            int(float(mdx23_overlap_val)) if mdx23_overlap_val != DEFAULT else mdx23_overlap_val
        )
        self.semitone_shift = float(root.semitone_shift_var.get()) if root else 0.0
        self.is_pitch_change = False if self.semitone_shift == 0 else True
        self.is_match_frequency_pitch = root.is_match_frequency_pitch_var.get() if root else False
        self.is_mdx_ckpt = False
        self.is_mdx_c = False
        self.is_mdx_combine_stems = root.is_mdx23_combine_stems_var.get() if root else False
        self.mdx_c_configs = None
        self.mdx_model_stems = []
        self.mdx_dim_f_set = None
        self.mdx_dim_t_set = None
        self.mdx_stem_count = 1
        self.compensate = None
        self.mdx_n_fft_scale_set = None
        self.wav_type_set = root.wav_type_set if root else "PCM_16"
        self.device_set = device_set.split(":")[-1].strip() if ":" in device_set else device_set
        self.mp3_bit_set = root.mp3_bit_set_var.get() if root else "320k"
        self.save_format = root.save_format_var.get() if root else WAV
        self.is_invert_spec = root.is_invert_spec_var.get() if root else False
        self.is_mixer_mode = False
        self.demucs_stems = root.demucs_stems_var.get() if root else None
        self.is_demucs_combine_stems = root.is_demucs_combine_stems_var.get() if root else False
        self.demucs_source_list = []
        self.demucs_stem_count = 0
        self.mixer_path = MDX_MIXER_PATH
        self.model_name = model_name
        self.process_method = selected_process_method
        self.model_status = False if self.model_name in (CHOOSE_MODEL, NO_MODEL) else True
        self.primary_stem = None
        self.secondary_stem = None
        self.primary_stem_native = None
        self.is_ensemble_mode = False
        self.ensemble_primary_stem = None
        self.ensemble_secondary_stem = None
        self.primary_model_primary_stem = primary_model_primary_stem
        self.is_secondary_model = True if is_vocal_split_model else is_secondary_model
        self.secondary_model = None
        self.secondary_model_scale = None
        self.demucs_4_stem_added_count = 0
        self.is_demucs_4_stem_secondaries = False
        self.is_4_stem_ensemble = False
        self.pre_proc_model = None
        self.pre_proc_model_activated = False
        self.is_pre_proc_model = is_pre_proc_model
        self.is_dry_check = is_dry_check
        self.model_samplerate = 44100
        self.model_capacity = 32, 128
        self.is_vr_51_model = False
        self.is_demucs_pre_proc_model_inst_mix = False
        self.manual_download_Button = None
        self.secondary_model_4_stem = []
        self.secondary_model_4_stem_scale = []
        self.secondary_model_4_stem_names = []
        self.secondary_model_4_stem_model_names_list = []
        self.all_models = []
        self.secondary_model_other = None
        self.secondary_model_scale_other = None
        self.secondary_model_bass = None
        self.secondary_model_scale_bass = None
        self.secondary_model_drums = None
        self.secondary_model_scale_drums = None
        self.is_multi_stem_ensemble = False
        self.is_karaoke = False
        self.is_bv_model = False
        self.bv_model_rebalance = 0
        self.is_sec_bv_rebalance = False
        self.is_change_def = is_change_def
        self.model_hash_dir = None
        self.is_get_hash_dir_only = is_get_hash_dir_only
        self.is_secondary_model_activated = False
        self.vocal_split_model = None
        self.is_vocal_split_model = is_vocal_split_model
        self.is_vocal_split_model_activated = False
        self.is_save_inst_vocal_splitter = root.is_save_inst_set_vocal_splitter_var.get() if root else False
        self.is_inst_only_voc_splitter = (
            root.check_only_selection_stem(INST_STEM_ONLY) if root else False
        )
        self.is_save_vocal_only = (
            root.check_only_selection_stem(IS_SAVE_VOC_ONLY) if root else False
        )

        if selected_process_method == ENSEMBLE_MODE and root:
            self.process_method, _, self.model_name = model_name.partition(ENSEMBLE_PARTITION)
            self.model_and_process_tag = model_name
            self.ensemble_primary_stem, self.ensemble_secondary_stem = root.return_ensemble_stems()

            is_not_secondary_or_pre_proc = not is_secondary_model and not is_pre_proc_model
            self.is_ensemble_mode = is_not_secondary_or_pre_proc

            if root.ensemble_main_stem_var.get() == FOUR_STEM_ENSEMBLE:
                self.is_4_stem_ensemble = self.is_ensemble_mode
            elif (
                root.ensemble_main_stem_var.get() == MULTI_STEM_ENSEMBLE
                and root.chosen_process_method_var.get() == ENSEMBLE_MODE
            ):
                self.is_multi_stem_ensemble = True

            is_not_vocal_stem = self.ensemble_primary_stem != VOCAL_STEM
            self.pre_proc_model_activated = (
                root.is_demucs_pre_proc_model_activate_var.get() if is_not_vocal_stem else False
            )

        if self.process_method == VR_ARCH_TYPE:
            self.is_secondary_model_activated = (
                root.vr_is_secondary_model_activate_var.get() if (root and not is_secondary_model) else False
            )
            aggression = root.aggression_setting_var.get() if root else 0
            self.aggression_setting = float(int(self.ensemble_settings.get("aggression_setting", aggression)) / 100)
            self.is_tta = root.is_tta_var.get() if root else False
            self.is_post_process = root.is_post_process_var.get() if root else False
            win_size = root.window_size_var.get() if root else 512
            self.window_size = int(self.ensemble_settings.get("window_size", win_size))
            batch_val = self.ensemble_settings.get("batch_size", root.batch_size_var.get()) if root else DEF_OPT
            self.batch_size = 1 if batch_val == DEF_OPT else int(batch_val)
            crop_val = root.crop_size_var.get() if root else 256
            self.crop_size = int(self.ensemble_settings.get("crop_size", crop_val))
            self.is_high_end_process = (
                "mirroring" if (root and root.is_high_end_process_var.get()) else "None"
            )
            self.post_process_threshold = float(root.post_process_threshold_var.get()) if root else 0.2
            self.model_capacity = 32, 128
            self.model_path = os.path.join(VR_MODELS_DIR, f"{self.model_name}.pth")
            self.get_model_hash()
            if self.model_hash:
                self.model_hash_dir = os.path.join(VR_HASH_DIR, f"{self.model_hash}.json")
                if is_change_def:
                    self.model_data = self.change_model_data()
                else:
                    vr_mapper = root.vr_hash_MAPPER if root else {}
                    self.model_data = (
                        self.get_model_data(VR_HASH_DIR, vr_mapper)
                        if not self.model_hash == WOOD_INST_MODEL_HASH
                        else WOOD_INST_PARAMS
                    )
                if self.model_data:
                    vr_model_param = os.path.join(
                        VR_PARAM_DIR, "{}.json".format(self.model_data["vr_model_param"])
                    )
                    self.primary_stem = self.model_data["primary_stem"]
                    self.secondary_stem = secondary_stem(self.primary_stem)
                    self.vr_model_param = ModelParameters(vr_model_param)
                    self.model_samplerate = self.vr_model_param.param["sr"]
                    self.primary_stem_native = self.primary_stem
                    if "nout" in self.model_data.keys() and "nout_lstm" in self.model_data.keys():
                        self.model_capacity = self.model_data["nout"], self.model_data["nout_lstm"]
                        self.is_vr_51_model = True
                    self.check_if_karaokee_model()
                else:
                    self.model_status = False

        if self.process_method == MDX_ARCH_TYPE:
            self.is_secondary_model_activated = (
                root.mdx_is_secondary_model_activate_var.get() if (root and not is_secondary_model) else False
            )
            self.margin = int(root.margin_var.get()) if root else 44100
            self.chunks = 0
            mdx_seg_val = root.mdx_segment_size_var.get() if root else DEFAULT
            mdx_segment_size_val = self.ensemble_settings.get("mdx_segment_size", mdx_seg_val)
            self.mdx_segment_size = (
                int(float(mdx_segment_size_val)) if mdx_segment_size_val != DEFAULT else mdx_segment_size_val
            )
            self.is_tta = root.is_mdx_tta_var.get() if root else False
            self.get_mdx_model_path()
            self.get_model_hash()
            if self.model_hash:
                self.model_hash_dir = os.path.join(MDX_HASH_DIR, f"{self.model_hash}.json")
                if is_change_def:
                    self.model_data = self.change_model_data()
                else:
                    mdx_mapper = root.mdx_hash_MAPPER if root else {}
                    self.model_data = self.get_model_data(MDX_HASH_DIR, mdx_mapper)
                if self.model_data:
                    self.is_roformer = self.model_data.get("is_roformer", False)
                    self.is_scnet = self.model_data.get("is_scnet", False)
                    self.is_mamba2 = self.model_data.get("is_mamba2", False)
                    self.is_bandit = self.model_data.get("is_bandit", False)

                    # Workaround for faulty online MDX hash mapper where SCNet models are marked as roformer
                    if self.model_data.get("model_type") == "SCNet":
                        self.is_roformer = False
                        self.is_scnet = True
                    if "config_yaml" in self.model_data:
                        self.is_mdx_c = True
                        config_path = os.path.join(MDX_C_CONFIG_PATH, self.model_data["config_yaml"])
                        if os.path.isfile(config_path):
                            with open(config_path, encoding="utf-8") as f:
                                config = ConfigDict(yaml.load(f, Loader=yaml.FullLoader))

                            self.mdx_c_configs = config

                            if self.mdx_c_configs.training.target_instrument:
                                target = self.mdx_c_configs.training.target_instrument
                                self.mdx_model_stems = [target]
                                self.primary_stem = target
                            else:
                                self.mdx_model_stems = self.mdx_c_configs.training.instruments
                                self.mdx_stem_count = len(self.mdx_model_stems)

                                if self.mdx_stem_count == 2:
                                    self.primary_stem = self.mdx_model_stems[0]
                                else:
                                    self.primary_stem = self.mdxnet_stem_select

                                if self.is_ensemble_mode:
                                    self.mdxnet_stem_select = self.ensemble_primary_stem
                            self.check_if_karaokee_model()
                        else:
                            self.model_status = False
                    else:
                        compensate_val = root.compensate_var.get() if root else AUTO_SELECT
                        self.compensate = (
                            self.model_data["compensate"]
                            if compensate_val == AUTO_SELECT
                            else float(compensate_val)
                        )
                        self.mdx_dim_f_set = self.model_data["mdx_dim_f_set"]
                        self.mdx_dim_t_set = self.model_data["mdx_dim_t_set"]
                        self.mdx_n_fft_scale_set = self.model_data["mdx_n_fft_scale_set"]
                        self.primary_stem = self.model_data["primary_stem"]
                        self.primary_stem_native = self.model_data["primary_stem"]
                        self.check_if_karaokee_model()

                    self.secondary_stem = secondary_stem(self.primary_stem)
                else:
                    self.model_status = False

        if self.process_method == DEMUCS_ARCH_TYPE:
            self.is_secondary_model_activated = (
                root.demucs_is_secondary_model_activate_var.get()
                if (root and not is_secondary_model)
                else False
            )
            self.is_tta = root.is_demucs_tta_var.get() if root else False
            if not self.is_ensemble_mode and root:
                self.pre_proc_model_activated = (
                    root.is_demucs_pre_proc_model_activate_var.get()
                    if root.demucs_stems_var.get() not in [VOCAL_STEM, INST_STEM]
                    else False
                )
            self.margin_demucs = int(root.margin_demucs_var.get()) if root else 44100

            chunks_val = (
                self.ensemble_settings.get("chunks_demucs", root.chunks_demucs_var.get())
                if root
                else AUTO_SELECT
            )
            self.chunks_demucs = (
                0 if chunks_val in (AUTO_SELECT, "Full") else int(chunks_val)
            )
            self.shifts = int(self.ensemble_settings.get("shifts", root.shifts_var.get())) if root else 2
            self.is_split_mode = root.is_split_mode_var.get() if root else True

            segment_val = (
                self.ensemble_settings.get("segment", root.segment_var.get()) if root else DEF_OPT
            )
            self.segment = None if segment_val == DEF_OPT else int(segment_val)
            self.is_chunk_demucs = root.is_chunk_demucs_var.get() if root else False
            self.is_primary_stem_only = (
                root.is_primary_stem_only_var.get()
                if (root and self.is_ensemble_mode)
                else (root.is_primary_stem_only_Demucs_var.get() if root else False)
            )
            self.is_secondary_stem_only = (
                root.is_secondary_stem_only_var.get()
                if (root and self.is_ensemble_mode)
                else (root.is_secondary_stem_only_Demucs_var.get() if root else False)
            )
            self.get_demucs_model_data()
            self.get_demucs_model_path()

        if self.model_status and getattr(self, "model_path", None):
            self.model_basename = os.path.splitext(os.path.basename(self.model_path))[0]
        else:
            self.model_basename = None

        self.pre_proc_model_activated = (
            self.pre_proc_model_activated if not self.is_secondary_model else False
        )
        self.is_primary_model_primary_stem_only = is_primary_model_primary_stem_only
        self.is_primary_model_secondary_stem_only = is_primary_model_secondary_stem_only

        is_secondary_activated_and_status = self.is_secondary_model_activated and self.model_status
        is_demucs = self.process_method == DEMUCS_ARCH_TYPE
        is_all_stems = root and root.demucs_stems_var.get() == ALL_STEMS
        is_valid_ensemble = not self.is_ensemble_mode and is_all_stems and is_demucs
        is_multi_stem_ensemble_demucs = self.is_multi_stem_ensemble and is_demucs

        if is_secondary_activated_and_status:
            if is_valid_ensemble or self.is_4_stem_ensemble or is_multi_stem_ensemble_demucs:
                for key in DEMUCS_4_SOURCE_LIST:
                    self.secondary_model_data(key)
                    self.secondary_model_4_stem.append(self.secondary_model)
                    self.secondary_model_4_stem_scale.append(self.secondary_model_scale)
                    self.secondary_model_4_stem_names.append(key)

                self.demucs_4_stem_added_count = sum(i is not None for i in self.secondary_model_4_stem)
                self.is_secondary_model_activated = any(i is not None for i in self.secondary_model_4_stem)
                self.demucs_4_stem_added_count -= 1 if self.is_secondary_model_activated else 0

                if self.is_secondary_model_activated:
                    self.secondary_model_4_stem_model_names_list = [
                        i.model_basename if i is not None else None for i in self.secondary_model_4_stem
                    ]
                    self.is_demucs_4_stem_secondaries = True
            else:
                primary_stem = (
                    self.ensemble_primary_stem
                    if (self.is_ensemble_mode and is_demucs)
                    else self.primary_stem
                )
                self.secondary_model_data(primary_stem)

        if self.process_method == DEMUCS_ARCH_TYPE and not is_secondary_model and root:
            if self.demucs_stem_count >= 3 and self.pre_proc_model_activated:
                self.pre_proc_model = root.process_determine_demucs_pre_proc_model(self.primary_stem)
                self.pre_proc_model_activated = True if self.pre_proc_model else False
                self.is_demucs_pre_proc_model_inst_mix = (
                    root.is_demucs_pre_proc_model_inst_mix_var.get() if self.pre_proc_model else False
                )

        if self.is_vocal_split_model and self.model_status:
            self.is_secondary_model_activated = False
            if self.is_bv_model:
                primary = BV_VOCAL_STEM if self.primary_stem_native == VOCAL_STEM else LEAD_VOCAL_STEM
            else:
                primary = LEAD_VOCAL_STEM if self.primary_stem_native == VOCAL_STEM else BV_VOCAL_STEM
            self.primary_stem, self.secondary_stem = primary, secondary_stem(primary)

        self.vocal_splitter_model_data()

    def vocal_splitter_model_data(self) -> None:
        """Configure vocal splitting secondary model if enabled."""
        if not self.is_secondary_model and self.model_status and self.root:
            self.vocal_split_model = self.root.process_determine_vocal_split_model()
            self.is_vocal_split_model_activated = True if self.vocal_split_model else False

            if self.vocal_split_model and self.vocal_split_model.bv_model_rebalance:
                self.is_sec_bv_rebalance = True

    def secondary_model_data(self, primary_stem: str) -> None:
        """Resolve secondary model pairing and blending scale."""
        if not self.root:
            return
        secondary_model_data = self.root.process_determine_secondary_model(
            self.process_method,
            primary_stem,
            self.is_primary_stem_only,
            self.is_secondary_stem_only,
        )
        self.secondary_model = secondary_model_data[0]
        self.secondary_model_scale = secondary_model_data[1]
        self.is_secondary_model_activated = False if not self.secondary_model else True
        if self.secondary_model:
            self.is_secondary_model_activated = (
                False if self.secondary_model.model_basename == self.model_basename else True
            )

    def check_if_karaokee_model(self) -> None:
        """Inspect model dictionary metadata for karaoke and backing-vocal tags."""
        if not hasattr(self, "model_data") or not isinstance(self.model_data, dict):
            return
        if IS_KARAOKEE in self.model_data:
            self.is_karaoke = self.model_data[IS_KARAOKEE]
        if IS_BV_MODEL in self.model_data:
            self.is_bv_model = self.model_data[IS_BV_MODEL]
        if IS_BV_MODEL_REBAL in self.model_data and self.is_bv_model:
            self.bv_model_rebalance = self.model_data[IS_BV_MODEL_REBAL]

    def get_mdx_model_path(self) -> None:
        """Resolve file path for MDX/ONNX/PyTorch model."""
        if (
            self.model_name.endswith(CKPT)
            or self.model_name.endswith(".safetensors")
            or self.model_name.endswith(".pth")
        ):
            self.is_mdx_ckpt = True

        ext = "" if self.is_mdx_ckpt else ONNX

        mapper = getattr(self.root, "mdx_name_select_MAPPER", {}) if self.root else {}
        for file_name, chosen_mdx_model in mapper.items():
            if self.model_name == chosen_mdx_model:
                if (
                    file_name.endswith(CKPT)
                    or file_name.endswith(".safetensors")
                    or file_name.endswith(".pth")
                ):
                    ext = ""
                self.model_path = os.path.join(MDX_MODELS_DIR, f"{file_name}{ext}")
                break
        else:
            self.model_path = os.path.join(MDX_MODELS_DIR, f"{self.model_name}{ext}")

        self.mixer_path = os.path.join(MDX_MODELS_DIR, "mixer_val.ckpt")

    def get_demucs_model_path(self) -> None:
        """Resolve file path for Demucs v3/v4 repo model."""
        demucs_newer = getattr(self, "demucs_version", DEMUCS_V4) in {DEMUCS_V3, DEMUCS_V4}
        demucs_model_dir = DEMUCS_NEWER_REPO_DIR if demucs_newer else DEMUCS_MODELS_DIR

        mapper = getattr(self.root, "demucs_name_select_MAPPER", {}) if self.root else {}
        for file_name, chosen_model in mapper.items():
            if self.model_name == chosen_model:
                self.model_path = os.path.join(demucs_model_dir, file_name)
                break
        else:
            self.model_path = os.path.join(DEMUCS_NEWER_REPO_DIR, f"{self.model_name}.yaml")

    def get_demucs_model_data(self) -> None:
        """Resolve stem mapping configuration for Demucs model."""
        self.demucs_version = DEMUCS_V4

        for key, value in DEMUCS_VERSION_MAPPER.items():
            if value in self.model_name:
                self.demucs_version = key

        if DEMUCS_UVR_MODEL in self.model_name:
            self.demucs_source_list, self.demucs_source_map, self.demucs_stem_count = (
                DEMUCS_2_SOURCE,
                DEMUCS_2_SOURCE_MAPPER,
                2,
            )
        else:
            self.demucs_source_list, self.demucs_source_map, self.demucs_stem_count = (
                DEMUCS_4_SOURCE,
                DEMUCS_4_SOURCE_MAPPER,
                4,
            )

        if not self.is_ensemble_mode:
            self.primary_stem = (
                PRIMARY_STEM if self.demucs_stems == ALL_STEMS else self.demucs_stems
            )
            self.secondary_stem = secondary_stem(self.primary_stem)

    def get_model_data(self, model_hash_dir: str, hash_mapper: dict) -> dict | None:
        """Fetch or register model parameter dictionary from hash or preset."""
        COMMUNITY_MODEL_CONFIGS = {
            "becruily_guitar.ckpt": {
                "config_yaml": "config_guitar_becruily.yaml",
                "is_roformer": True,
                "model_type": "MelBand-Roformer",
                "is_karaoke": False,
            },
            "gilliaan_drumsV1.ckpt": {
                "config_yaml": "config_drums_gilliaan.yaml",
                "is_roformer": True,
                "model_type": "BS-Roformer",
                "is_karaoke": False,
            },
            "bs_roformer_4stems_ft.pth": {
                "config_yaml": "config_bs_roformer_4stems_syh99999.yaml",
                "is_roformer": True,
                "model_type": "BS-Roformer",
                "is_karaoke": False,
            },
            "dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt": {
                "config_yaml": "dereverb_bs_roformer_anvuew_sdr_22.5050.yaml",
                "is_roformer": True,
                "model_type": "BS-Roformer",
                "is_karaoke": False,
            },
            "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt": {
                "config_yaml": "model_mel_band_roformer_denoise.yaml",
                "is_roformer": True,
                "model_type": "MelBand-Roformer",
                "is_karaoke": False,
            },
            "model_BandSplit-Roformer_SW_by-jarredou.ckpt": {
                "config_yaml": "config_BandSplit-Roformer_SW_by-jarredou.yaml",
                "is_roformer": True,
                "model_type": "BS-Roformer",
                "is_karaoke": False,
            },
        }
        model_basename = os.path.basename(getattr(self, "model_path", ""))
        if model_basename in COMMUNITY_MODEL_CONFIGS:
            cfg = COMMUNITY_MODEL_CONFIGS[model_basename]
            model_settings_json = os.path.join(model_hash_dir, f"{self.model_hash}.json")
            try:
                with open(model_settings_json, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=4)
            except Exception:
                pass
            return cfg

        model_settings_json = os.path.join(model_hash_dir, f"{self.model_hash}.json")

        if os.path.isfile(model_settings_json):
            with open(model_settings_json, encoding="utf-8") as json_file:
                return json.load(json_file)
        else:
            for hash_val, settings in hash_mapper.items():
                if self.model_hash in hash_val:
                    return settings

            return self.get_model_data_from_popup()

    def change_model_data(self) -> dict | None:
        """Trigger configuration modification for unrecognized model."""
        if self.is_get_hash_dir_only:
            return None
        return self.get_model_data_from_popup()

    def get_model_data_from_popup(self) -> dict | None:
        """Display manual model parameter configuration modal if GUI is available."""
        if self.is_dry_check or not self.root:
            return None

        from tkinter import messagebox

        if not self.is_change_def:
            confirm = messagebox.askyesno(
                title=UNRECOGNIZED_MODEL[0],
                message=f'"{self.model_name}"{UNRECOGNIZED_MODEL[1]}',
                parent=self.root,
            )
            if not confirm:
                return None

        if self.process_method == VR_ARCH_TYPE:
            self.root.pop_up_vr_param(self.model_hash)
            return self.root.vr_model_params
        elif self.process_method == MDX_ARCH_TYPE:
            self.root.pop_up_mdx_model(self.model_hash, self.model_path)
            return self.root.mdx_model_params
        return None

    def get_model_hash(self) -> None:
        """Calculate fast partial MD5 hash of model weights file."""
        self.model_hash = None

        if not hasattr(self, "model_path") or not os.path.isfile(self.model_path):
            self.model_status = False
            return

        if model_hash_table:
            for key, value in model_hash_table.items():
                if self.model_path == key:
                    self.model_hash = value
                    break

        if not self.model_hash:
            try:
                with open(self.model_path, "rb") as f:
                    f.seek(-10000 * 1024, 2)
                    self.model_hash = hashlib.md5(f.read()).hexdigest()
            except Exception:
                with open(self.model_path, "rb") as f:
                    self.model_hash = hashlib.md5(f.read()).hexdigest()

            table_entry = {self.model_path: self.model_hash}
            model_hash_table.update(table_entry)
