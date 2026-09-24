"""Audio Tools Options Panel for UVR GUI."""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui_data.app_size_values import (
    CHECK_BOX_HEIGHT,
    CHECK_BOX_WIDTH,
    CHECK_BOX_X,
    CHECK_BOX_Y,
    DB_ANALYSIS_LABEL_WIDTH,
    DB_ANALYSIS_LABEL_X,
    DB_ANALYSIS_OPTION_X,
    ENTRY_OPEN_BUTT_WIDTH,
    ENTRY_OPEN_BUTT_X_OFF,
    ENTRY_WIDTH,
    ENTRY_Y,
    FILEONE_LABEL_WIDTH,
    FILEONE_LABEL_X,
    FILETWO_LABEL_WIDTH,
    FILETWO_LABEL_X,
    INTRO_ANALYSIS_LABEL_WIDTH,
    INTRO_ANALYSIS_LABEL_X,
    INTRO_ANALYSIS_OPTION_X,
    LABEL_HEIGHT,
    LABEL_Y,
    LEFT_ROW_WIDTH,
    LOW_MENU_Y,
    MAIN_ROW_WIDTH,
    MAIN_ROW_X,
    MAIN_ROW_Y,
    OPTION_HEIGHT,
    OPTION_WIDTH,
    SUB_ENT_ROW_X,
    TIME_WINDOW_LABEL_WIDTH,
    TIME_WINDOW_LABEL_X,
    WAV_TYPE_SET_LABEL_WIDTH,
    WAV_TYPE_SET_LABEL_X,
)
from gui_data.constants import (
    ALIGN_INPUTS,
    AUDIO_TOOL_OPTIONS,
    AUDIO_TOOLS_HELP,
    CHANGE_PITCH,
    CHOOSE_AUDIO_TOOLS_MAIN_LABEL,
    CHOOSE_MANUAL_ALGORITHM_MAIN_LABEL,
    CHOOSE_RATE_MAIN_LABEL,
    CHOOSE_SEMITONES_MAIN_LABEL,
    ENSEMBLE_WAVFORMS_TEXT,
    FILE_ONE_MAIN_LABEL,
    FILE_ONE_MATCH_MAIN_LABEL,
    FILE_TWO_MAIN_LABEL,
    FILE_TWO_MATCH_MAIN_LABEL,
    INPUT_FOLDER_BUTTON_HELP,
    INPUT_SEC_FIELDS_HELP,
    INTRO_ANALYSIS_ALIGN_HELP,
    INTRO_ANALYSIS_MAIN_LABEL,
    INTRO_MAPPER,
    IS_TIME_CORRECTION_HELP,
    IS_WAV_ENSEMBLE_HELP,
    MANUAL_ENSEMBLE,
    MANUAL_ENSEMBLE_OPTIONS,
    MATCH_INPUTS,
    REG_PITCH,
    REG_TIME,
    TIME_CORRECTION_TEXT,
    TIME_PITCH,
    TIME_STRETCH,
    TIME_WINDOW_ALIGN_HELP,
    TIME_WINDOW_MAIN_LABEL,
    TIME_WINDOW_MAPPER,
    VOLUME_ADJUSTMENT_MAIN_LABEL,
    VOLUME_ANALYSIS_ALIGN_HELP,
    VOLUME_MAPPER,
    WAV_TYPE,
    WAVE_TYPE_TEXT,
)
from uvr.ui.components import ComboBoxEditableMenu, ComboBoxMenu
from uvr.utils.file_utils import open_file_or_folder

logger = logging.getLogger(__name__)


class AudioToolsPanel:
    """Manages widgets and layout for Audio Tools (Align, Pitch, Time Stretch, Manual Ensemble)."""

    def __init__(self, root: Any, parent_frame: Any) -> None:
        self.root = root
        self.parent = parent_frame

    def setup_ui(self) -> None:
        """Initializes Audio Tools controls on parent frame and attaches to root."""
        # Chosen Audio Tool
        self.root.chosen_audio_tool_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_AUDIO_TOOLS_MAIN_LABEL
        )
        self.root.chosen_audio_tool_Label_place = lambda: self.root.chosen_audio_tool_Label.place(
            x=0,
            y=LOW_MENU_Y[0],
            width=LEFT_ROW_WIDTH,
            height=LABEL_HEIGHT,
            relx=0,
            rely=6 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.chosen_audio_tool_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.chosen_audio_tool_var,
            values=AUDIO_TOOL_OPTIONS,
            command=lambda e: self.root.update_main_widget_states(),
        )
        self.root.chosen_audio_tool_Option_place = lambda: self.root.chosen_audio_tool_Option.place(
            x=0,
            y=LOW_MENU_Y[1],
            width=LEFT_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=0,
            rely=7 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(self.root.chosen_audio_tool_Label, text=AUDIO_TOOLS_HELP)

        # Choose Algorithm
        self.root.choose_algorithm_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_MANUAL_ALGORITHM_MAIN_LABEL
        )
        self.root.choose_algorithm_Label_place = lambda: self.root.choose_algorithm_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.choose_algorithm_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.choose_algorithm_var,
            values=MANUAL_ENSEMBLE_OPTIONS,
        )
        self.root.choose_algorithm_Option_place = lambda: self.root.choose_algorithm_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        # Time Stretch
        self.root.time_stretch_rate_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_RATE_MAIN_LABEL
        )
        self.root.time_stretch_rate_Label_place = lambda: self.root.time_stretch_rate_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.time_stretch_rate_Option = ComboBoxEditableMenu(
            self.parent,
            values=TIME_PITCH,
            textvariable=self.root.time_stretch_rate_var,
            pattern=REG_TIME,
            default=TIME_PITCH,
        )
        self.root.time_stretch_rate_Option_place = lambda: self.root.time_stretch_rate_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        # Pitch Rate
        self.root.pitch_rate_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_SEMITONES_MAIN_LABEL
        )
        self.root.pitch_rate_Label_place = lambda: self.root.pitch_rate_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.pitch_rate_Option = ComboBoxEditableMenu(
            self.parent,
            values=TIME_PITCH,
            textvariable=self.root.pitch_rate_var,
            pattern=REG_PITCH,
            default=TIME_PITCH,
        )
        self.root.pitch_rate_Option_place = lambda: self.root.pitch_rate_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        # Is Time Correction
        self.root.is_time_correction_Option = ttk.Checkbutton(
            master=self.parent,
            text=TIME_CORRECTION_TEXT,
            variable=self.root.is_time_correction_var,
        )
        self.root.is_time_correction_Option_place = (
            lambda: self.root.is_time_correction_Option.place(
                x=CHECK_BOX_X,
                y=CHECK_BOX_Y,
                width=CHECK_BOX_WIDTH,
                height=CHECK_BOX_HEIGHT,
                relx=1 / 3,
                rely=5 / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.help_hints(self.root.is_time_correction_Option, text=IS_TIME_CORRECTION_HELP)

        # Is Wav Ensemble
        self.root.is_wav_ensemble_Option = ttk.Checkbutton(
            master=self.parent,
            text=ENSEMBLE_WAVFORMS_TEXT,
            variable=self.root.is_wav_ensemble_var,
        )
        self.root.is_wav_ensemble_Option_place = lambda: self.root.is_wav_ensemble_Option.place(
            x=CHECK_BOX_X,
            y=CHECK_BOX_Y,
            width=CHECK_BOX_WIDTH,
            height=CHECK_BOX_HEIGHT,
            relx=1 / 3,
            rely=5 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.is_wav_ensemble_Option, text=IS_WAV_ENSEMBLE_HELP)

        # Track 1
        self.root.fileOne_Label = self.root.main_window_LABEL_SUB_SET(
            self.parent, self.root.file_one_sub_var
        )
        self.root.fileOne_Label_place = lambda: self.root.fileOne_Label.place(
            x=FILEONE_LABEL_X,
            y=LABEL_Y,
            width=FILEONE_LABEL_WIDTH,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        self.root.fileOne_Entry = ttk.Entry(
            master=self.parent,
            textvariable=self.root.fileOneEntry_var,
            font=self.root.font_entry,
            state=tk.DISABLED,
        )
        self.root.fileOne_Entry_place = lambda: self.root.fileOne_Entry.place(
            x=SUB_ENT_ROW_X,
            y=ENTRY_Y,
            width=ENTRY_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.fileOne_Entry, text=INPUT_SEC_FIELDS_HELP)
        self.root.fileOne_Entry.configure(cursor="hand2")

        self.root.fileOne_Open = ttk.Button(
            master=self.parent,
            image=self.root.efile_img,
            command=lambda: open_file_or_folder(
                os.path.dirname(self.root.fileOneEntry_Full_var.get())
            ),
        )
        self.root.fileOne_Open_place = lambda: self.root.fileOne_Open.place(
            x=ENTRY_OPEN_BUTT_X_OFF,
            y=ENTRY_Y,
            width=ENTRY_OPEN_BUTT_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.fileOne_Open, text=INPUT_FOLDER_BUTTON_HELP)

        # Track 2
        self.root.fileTwo_Label = self.root.main_window_LABEL_SUB_SET(
            self.parent, self.root.file_two_sub_var
        )
        self.root.fileTwo_Label_place = lambda: self.root.fileTwo_Label.place(
            x=FILETWO_LABEL_X,
            y=LABEL_Y,
            width=FILETWO_LABEL_WIDTH,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=4.5 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        self.root.fileTwo_Entry = ttk.Entry(
            master=self.parent,
            textvariable=self.root.fileTwoEntry_var,
            font=self.root.font_entry,
            state=tk.DISABLED,
        )
        self.root.fileTwo_Entry_place = lambda: self.root.fileTwo_Entry.place(
            x=SUB_ENT_ROW_X,
            y=ENTRY_Y,
            width=ENTRY_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=5.5 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.fileTwo_Entry, text=INPUT_SEC_FIELDS_HELP)
        self.root.fileTwo_Entry.configure(cursor="hand2")

        self.root.fileTwo_Open = ttk.Button(
            master=self.parent,
            image=self.root.efile_img,
            command=lambda: open_file_or_folder(
                os.path.dirname(self.root.fileTwoEntry_Full_var.get())
            ),
        )
        self.root.fileTwo_Open_place = lambda: self.root.fileTwo_Open.place(
            x=ENTRY_OPEN_BUTT_X_OFF,
            y=ENTRY_Y,
            width=ENTRY_OPEN_BUTT_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=5.5 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.fileTwo_Open, text=INPUT_FOLDER_BUTTON_HELP)

        # Time Window
        self.root.time_window_Label = self.root.main_window_LABEL_SET(
            self.parent, TIME_WINDOW_MAIN_LABEL
        )
        self.root.time_window_Label_place = lambda: self.root.time_window_Label.place(
            x=TIME_WINDOW_LABEL_X,
            y=LABEL_Y,
            width=TIME_WINDOW_LABEL_WIDTH,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=7.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.time_window_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.time_window_var,
            values=tuple(TIME_WINDOW_MAPPER.keys()),
        )
        self.root.time_window_Option_place = lambda: self.root.time_window_Option.place(
            x=SUB_ENT_ROW_X,
            y=ENTRY_Y,
            width=OPTION_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=8.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.time_window_Label, text=TIME_WINDOW_ALIGN_HELP)

        # Align Shifts
        self.root.intro_analysis_Label = self.root.main_window_LABEL_SET(
            self.parent, INTRO_ANALYSIS_MAIN_LABEL
        )
        self.root.intro_analysis_Label_place = lambda: self.root.intro_analysis_Label.place(
            x=INTRO_ANALYSIS_LABEL_X,
            y=LABEL_Y,
            width=INTRO_ANALYSIS_LABEL_WIDTH,
            height=LABEL_HEIGHT,
            relx=2 / 3,
            rely=7.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.intro_analysis_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.intro_analysis_var,
            values=tuple(INTRO_MAPPER.keys()),
        )
        self.root.intro_analysis_Option_place = lambda: self.root.intro_analysis_Option.place(
            x=INTRO_ANALYSIS_OPTION_X,
            y=ENTRY_Y,
            width=OPTION_WIDTH,
            height=OPTION_HEIGHT,
            relx=2 / 3,
            rely=8.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.intro_analysis_Label, text=INTRO_ANALYSIS_ALIGN_HELP)

        # Volume Adjustment
        self.root.db_analysis_Label = self.root.main_window_LABEL_SET(
            self.parent, VOLUME_ADJUSTMENT_MAIN_LABEL
        )
        self.root.db_analysis_Label_place = lambda: self.root.db_analysis_Label.place(
            x=DB_ANALYSIS_LABEL_X,
            y=LABEL_Y,
            width=DB_ANALYSIS_LABEL_WIDTH,
            height=LABEL_HEIGHT,
            relx=2 / 3,
            rely=7.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.db_analysis_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.db_analysis_var,
            values=tuple(VOLUME_MAPPER.keys()),
        )
        self.root.db_analysis_Option_place = lambda: self.root.db_analysis_Option.place(
            x=DB_ANALYSIS_OPTION_X,
            y=ENTRY_Y,
            width=OPTION_WIDTH,
            height=OPTION_HEIGHT,
            relx=2 / 3,
            rely=8.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.db_analysis_Label, text=VOLUME_ANALYSIS_ALIGN_HELP)

        # Wav-Type
        self.root.wav_type_set_Label = self.root.main_window_LABEL_SET(self.parent, WAVE_TYPE_TEXT)
        self.root.wav_type_set_Label_place = lambda: self.root.wav_type_set_Label.place(
            x=WAV_TYPE_SET_LABEL_X,
            y=LABEL_Y,
            width=WAV_TYPE_SET_LABEL_WIDTH,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=7.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.wav_type_set_Option = ComboBoxMenu(
            self.parent, textvariable=self.root.wav_type_set_var, values=WAV_TYPE
        )
        self.root.wav_type_set_Option_place = lambda: self.root.wav_type_set_Option.place(
            x=SUB_ENT_ROW_X,
            y=ENTRY_Y,
            width=OPTION_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=8.37 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

    def place_widgets(self, audio_tool: str) -> None:
        """Places Audio Tools widgets according to the active tool option."""
        self.root.chosen_audio_tool_Label_place()
        self.root.chosen_audio_tool_Option_place()

        if audio_tool == ALIGN_INPUTS:
            self.root.file_one_sub_var.set(FILE_ONE_MAIN_LABEL)
            self.root.file_two_sub_var.set(FILE_TWO_MAIN_LABEL)
        elif audio_tool == MATCH_INPUTS:
            self.root.file_one_sub_var.set(FILE_ONE_MATCH_MAIN_LABEL)
            self.root.file_two_sub_var.set(FILE_TWO_MATCH_MAIN_LABEL)

        audio_tool_options: dict[str, list[Any]] = {
            MANUAL_ENSEMBLE: [
                self.root.choose_algorithm_Label_place,
                self.root.choose_algorithm_Option_place,
                self.root.is_wav_ensemble_Option_place,
            ],
            TIME_STRETCH: [
                lambda: self.root.model_sample_mode_Option_place(rely=5),
                self.root.time_stretch_rate_Label_place,
                self.root.time_stretch_rate_Option_place,
            ],
            CHANGE_PITCH: [
                self.root.is_time_correction_Option_place,
                lambda: self.root.model_sample_mode_Option_place(rely=6),
                self.root.pitch_rate_Label_place,
                self.root.pitch_rate_Option_place,
            ],
            ALIGN_INPUTS: [
                self.root.fileOne_Label_place,
                self.root.fileOne_Entry_place,
                self.root.fileTwo_Label_place,
                self.root.fileTwo_Entry_place,
                self.root.fileOne_Open_place,
                self.root.fileTwo_Open_place,
                self.root.intro_analysis_Label_place,
                self.root.intro_analysis_Option_place,
                self.root.db_analysis_Label_place,
                self.root.db_analysis_Option_place,
                self.root.time_window_Label_place,
                self.root.time_window_Option_place,
            ],
            MATCH_INPUTS: [
                self.root.fileOne_Label_place,
                self.root.fileOne_Entry_place,
                self.root.fileTwo_Label_place,
                self.root.fileTwo_Entry_place,
                self.root.fileOne_Open_place,
                self.root.fileTwo_Open_place,
                self.root.wav_type_set_Label_place,
                self.root.wav_type_set_Option_place,
            ],
        }

        for placer in audio_tool_options.get(audio_tool, []):
            placer()
