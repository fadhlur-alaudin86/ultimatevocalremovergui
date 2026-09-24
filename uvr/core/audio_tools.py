"""Secondary audio processing utilities: phase alignment, mastering matchering,
pitch and time stretching.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matchering as match

from gui_data.constants import *
from lib_v5 import spec_utils
from separate import save_format
from uvr.core.model_data import get_app_root

logger = logging.getLogger(__name__)


class AudioTools:
    """Provides utility audio manipulations including spectral alignment, mastering matching

    via Matchering, time stretching, and semitone pitch shifting.
    """

    def __init__(self, audio_tool: str, root: Any = None):
        if root is None:
            root = get_app_root()
        self.root = root

        time_stamp = round(time.time())
        self.audio_tool = audio_tool
        export_val = root.export_path_var.get() if root else ""
        self.main_export_path = Path(export_val)
        self.wav_type_set = root.wav_type_set if root else "PCM_16"
        self.is_normalization = root.is_normalization_var.get() if root else False
        testing_audio = root.is_testing_audio_var.get() if root else False
        self.is_testing_audio = f"{time_stamp}_" if testing_audio else ""

        replaygain = getattr(root, "is_replaygain_var", None).get() if root else False
        save_fmt = root.save_format_var.get() if root else WAV
        mp3_bit = root.mp3_bit_set_var.get() if root else "320k"
        self.save_format = lambda save_path, **kwargs: save_format(save_path, save_fmt, mp3_bit, replaygain, **kwargs)

        time_win = root.time_window_var.get() if root else "Medium"
        self.align_window = TIME_WINDOW_MAPPER.get(time_win, 512)
        intro_val = root.intro_analysis_var.get() if root else "Medium"
        self.align_intro_val = INTRO_MAPPER.get(intro_val, 1)
        db_val = root.db_analysis_var.get() if root else "Medium"
        self.db_analysis_val = VOLUME_MAPPER.get(db_val, 1)
        self.is_save_align = root.is_save_align_var.get() if root else False
        self.is_match_silence = root.is_match_silence_var.get() if root else False
        self.is_spec_match = root.is_spec_match_var.get() if root else False

        self.phase_option = root.phase_option_var.get() if root else "None"
        phase_sh = root.phase_shifts_var.get() if root else "NONE"
        self.phase_shifts = PHASE_SHIFTS_OPT.get(phase_sh, 0)

    def align_inputs(
        self,
        audio_inputs: list[str],
        audio_file_base: str,
        audio_file_2_base: str,
        command_text: Callable[[str], None],
        set_progress_bar: Callable[..., None],
    ) -> None:
        """Align phase and time offset between primary and secondary audio inputs."""
        base_1 = f"{self.is_testing_audio}{audio_file_base}"
        base_2 = f"{self.is_testing_audio}{audio_file_2_base}"

        aligned_path = os.path.join(f"{self.main_export_path}", f"{base_2}_(Aligned).wav")
        inverted_path = os.path.join(f"{self.main_export_path}", f"{base_1}_(Inverted).wav")

        spec_utils.align_audio(
            audio_inputs[0],
            audio_inputs[1],
            aligned_path,
            inverted_path,
            self.wav_type_set,
            self.is_save_align,
            command_text,
            self.save_format,
            align_window=self.align_window,
            align_intro_val=self.align_intro_val,
            db_analysis=self.db_analysis_val,
            set_progress_bar=set_progress_bar,
            phase_option=self.phase_option,
            phase_shifts=self.phase_shifts,
            is_match_silence=self.is_match_silence,
            is_spec_match=self.is_spec_match,
        )

    def match_inputs(
        self,
        audio_inputs: list[str],
        audio_file_base: str,
        command_text: Callable[[str], None],
    ) -> None:
        """Perform Matchering mastering match between target and reference audio."""
        target = audio_inputs[0]
        reference = audio_inputs[1]

        command_text("Processing... ")

        save_path = os.path.join(
            f"{self.main_export_path}",
            f"{self.is_testing_audio}{audio_file_base}_(Matched).wav",
        )

        match.process(
            target=target,
            reference=reference,
            results=[match.save_audiofile(save_path, wav_set=self.wav_type_set)],
        )

        self.save_format(save_path)

    def combine_audio(self, audio_inputs: list[str], audio_file_base: str) -> None:
        """Combine multiple input audio files into a mixed track."""
        spec_utils.combine_audio(
            audio_inputs,
            os.path.join(self.main_export_path, f"{self.is_testing_audio}{audio_file_base}"),
            self.wav_type_set,
            save_format=self.save_format,
        )

    def pitch_or_time_shift(self, audio_file: str, audio_file_base: str) -> None:
        """Perform pitch shifting or time stretching based on selected tool."""
        is_time_correction = True
        rate = 1.0
        if self.root:
            if self.audio_tool == TIME_STRETCH:
                rate = float(self.root.time_stretch_rate_var.get())
            else:
                rate = float(self.root.pitch_rate_var.get())

        is_pitch = self.audio_tool != TIME_STRETCH
        if is_pitch and self.root:
            is_time_correction = bool(self.root.is_time_correction_var.get())

        file_text = TIME_TEXT if self.audio_tool == TIME_STRETCH else PITCH_TEXT
        save_path = os.path.join(
            self.main_export_path,
            f"{self.is_testing_audio}{audio_file_base}{file_text}.wav",
        )

        save_format_ = lambda p: self.save_format(p, input_file_path=audio_file)
        spec_utils.augment_audio(
            save_path,
            audio_file,
            rate,
            self.is_normalization,
            self.wav_type_set,
            save_format_,
            is_pitch=is_pitch,
            is_time_correction=is_time_correction,
        )
