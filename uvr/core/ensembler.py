"""Multi-model ensemble processing and audio output blending.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from gui_data.constants import *
from lib_v5 import spec_utils
from separate import save_format
from uvr.constants import ENSEMBLE_TEMP_PATH
from uvr.core.model_data import ModelData, get_app_root

logger = logging.getLogger(__name__)


class Ensembler:
    """Orchestrates ensembling across multiple model outputs using various blending

    algorithms (Max Spec, Min Spec, Average, Weighted Average).
    """

    def __init__(self, is_manual_ensemble: bool = False, root: Any = None):
        if root is None:
            root = get_app_root()
        self.root = root

        self.is_save_all_outputs_ensemble = (
            root.is_save_all_outputs_ensemble_var.get() if root else False
        )
        chosen_name = root.chosen_ensemble_var.get() if root else CHOOSE_ENSEMBLE_OPTION
        chosen_ensemble_name = (
            "{}".format(chosen_name.replace(" ", "_"))
            if chosen_name != CHOOSE_ENSEMBLE_OPTION
            else "Ensembled"
        )
        ensemble_type = root.ensemble_type_var.get() if root else "Average/Average"
        ensemble_algorithm = ensemble_type.partition("/")
        main_stem_var = root.ensemble_main_stem_var.get() if root else "Vocals/Instrumental"
        ensemble_main_stem_pair = main_stem_var.partition("/")
        time_stamp = round(time.time())
        self.audio_tool = MANUAL_ENSEMBLE
        export_val = root.export_path_var.get() if root else ""
        self.main_export_path = Path(export_val)
        append_name = root.is_append_ensemble_name_var.get() if root else False
        self.chosen_ensemble = f"_{chosen_ensemble_name}" if append_name else ""
        ensemble_folder_name = (
            self.main_export_path if self.is_save_all_outputs_ensemble else ENSEMBLE_TEMP_PATH
        )
        self.ensemble_folder_name = os.path.join(
            ensemble_folder_name, f"{chosen_ensemble_name}_Outputs_{time_stamp}"
        )
        testing_audio = root.is_testing_audio_var.get() if root else False
        self.is_testing_audio = f"{time_stamp}_" if testing_audio else ""
        self.primary_algorithm = ensemble_algorithm[0]
        self.secondary_algorithm = ensemble_algorithm[2]
        self.ensemble_primary_stem = ensemble_main_stem_pair[0]
        self.ensemble_secondary_stem = ensemble_main_stem_pair[2]
        self.is_normalization = root.is_normalization_var.get() if root else False
        self.is_wav_ensemble = root.is_wav_ensemble_var.get() if root else False
        self.wav_type_set = root.wav_type_set if root else "PCM_16"
        self.mp3_bit_set = root.mp3_bit_set_var.get() if root else "320k"
        self.save_format = root.save_format_var.get() if root else WAV
        if not is_manual_ensemble and not os.path.exists(self.ensemble_folder_name):
            os.makedirs(self.ensemble_folder_name, exist_ok=True)

    def ensemble_outputs(
        self,
        audio_file_base: str,
        export_path: str,
        stem: str,
        is_4_stem: bool = False,
        is_inst_mix: bool = False,
    ) -> None:
        """Process output audio files and blend them using the configured ensemble algorithm."""
        if is_4_stem:
            algorithm = self.root.ensemble_type_var.get() if self.root else self.primary_algorithm
            stem_tag = stem
        else:
            if is_inst_mix:
                algorithm = self.secondary_algorithm
                stem_tag = f"{self.ensemble_secondary_stem} {INST_STEM}"
            else:
                algorithm = self.primary_algorithm if stem == PRIMARY_STEM else self.secondary_algorithm
                stem_tag = self.ensemble_primary_stem if stem == PRIMARY_STEM else self.ensemble_secondary_stem

        stem_outputs = self.get_files_to_ensemble(
            folder=export_path, prefix=audio_file_base, suffix=f"_({stem_tag}).wav"
        )
        audio_file_output = f"{self.is_testing_audio}{audio_file_base}{self.chosen_ensemble}_({stem_tag})"
        stem_save_path = os.path.join(f"{self.main_export_path}", f"{audio_file_output}.wav")

        if len(stem_outputs) > 1:
            weights = None
            if algorithm == WEIGHTED_AVERAGE and self.root:
                weights = []
                selected_models = self.root.ensemble_listbox_get_all_selected_models()
                model_basenames_map = {
                    ModelData(m, is_change_def=False, root=self.root).model_basename: float(
                        self.root.ensemble_model_settings.get(m, {}).get("weight", 10)
                    )
                    for m in selected_models
                }
                for f in stem_outputs:
                    f_base = os.path.basename(f)
                    prefix = f"{audio_file_base}_"
                    suffix = f"_({stem_tag}).wav"
                    m_name = f_base
                    if f_base.startswith(prefix):
                        m_name = m_name[len(prefix):]
                    m_name = m_name.removesuffix(suffix)
                    weights.append(model_basenames_map.get(m_name, 10.0))

            spec_utils.ensemble_inputs(
                stem_outputs,
                algorithm,
                self.is_normalization,
                self.wav_type_set,
                stem_save_path,
                is_wave=self.is_wav_ensemble,
                weights=weights,
            )
            replaygain = getattr(self.root, "is_replaygain_var", None).get() if self.root else False
            save_format(stem_save_path, self.save_format, self.mp3_bit_set, replaygain)

        replaygain = getattr(self.root, "is_replaygain_var", None).get() if self.root else False
        if self.is_save_all_outputs_ensemble:
            for i in stem_outputs:
                save_format(i, self.save_format, self.mp3_bit_set, replaygain)
        else:
            for i in stem_outputs:
                try:
                    os.remove(i)
                except Exception as exc:
                    logger.debug("Failed removing temp ensemble file %s: %s", i, exc)

    def ensemble_manual(self, audio_inputs: list[str], audio_file_base: str, is_bulk: bool = False) -> None:
        """Process manual ensemble blending on user-selected files."""
        is_mv_sep = True

        if is_bulk:
            number_list = list(set([os.path.basename(i).split("_")[0] for i in audio_inputs]))
            for n in number_list:
                current_list = [i for i in audio_inputs if os.path.basename(i).startswith(n)]
                base_name = os.path.basename(current_list[0]).split(".wav")[0]
                stem_testing = "instrum" if "Instrumental" in base_name else "vocals"
                if is_mv_sep:
                    parts = base_name.split("_")
                    if len(parts) >= 3:
                        base_name = f"{parts[1]}_{parts[2]}_{stem_testing}"
                self.ensemble_manual_process(current_list, base_name, is_bulk)
        else:
            self.ensemble_manual_process(audio_inputs, audio_file_base, is_bulk)

    def ensemble_manual_process(self, audio_inputs: list[str], audio_file_base: str, is_bulk: bool) -> None:
        """Execute manual ensembling algorithm over given inputs."""
        algorithm = self.root.choose_algorithm_var.get() if self.root else "Average"
        algorithm_text = "" if is_bulk else f"_({algorithm})"
        stem_save_path = os.path.join(
            f"{self.main_export_path}",
            f"{self.is_testing_audio}{audio_file_base}{algorithm_text}.wav",
        )
        spec_utils.ensemble_inputs(
            audio_inputs,
            algorithm,
            self.is_normalization,
            self.wav_type_set,
            stem_save_path,
            is_wave=self.is_wav_ensemble,
        )
        replaygain = getattr(self.root, "is_replaygain_var", None).get() if self.root else False
        save_format(stem_save_path, self.save_format, self.mp3_bit_set, replaygain)

    def get_files_to_ensemble(self, folder: str = "", prefix: str = "", suffix: str = "") -> list[str]:
        """Grab all the files in a folder matching prefix and suffix filters."""
        if not os.path.isdir(folder):
            return []
        return [
            os.path.join(folder, i)
            for i in os.listdir(folder)
            if i.startswith(prefix) and i.endswith(suffix)
        ]

    def combine_audio(self, audio_inputs: list[str], audio_file_base: str) -> None:
        """Combine multiple stems into a single audio mix."""
        replaygain = getattr(self.root, "is_replaygain_var", None).get() if self.root else False
        save_fmt = self.root.save_format_var.get() if self.root else WAV
        mp3_bit = self.root.mp3_bit_set_var.get() if self.root else "320k"
        save_format_ = lambda save_path: save_format(save_path, save_fmt, mp3_bit, replaygain)
        spec_utils.combine_audio(
            audio_inputs,
            os.path.join(self.main_export_path, f"{self.is_testing_audio}{audio_file_base}"),
            self.wav_type_set,
            save_format=save_format_,
        )
