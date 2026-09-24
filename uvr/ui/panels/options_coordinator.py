"""Options Panel Coordinator orchestrating model selection tabs and layout for UVR GUI."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any

import torch

from gui_data.app_size_values import (
    CHECK_BOX_HEIGHT,
    CHECK_BOX_WIDTH,
    CHECK_BOX_X,
    CHECK_BOX_Y,
    LABEL_HEIGHT,
    LEFT_ROW_WIDTH,
    LOW_MENU_Y,
    MAIN_ROW_2_X,
    MAIN_ROW_WIDTH,
    MAIN_ROW_Y,
    OPTION_HEIGHT,
    OPTIONS_FRAME_WIDTH,
    OPTIONS_FRAME_X,
    OPTIONS_FRAME_Y,
    RADIOBUTTON_HEIGHT,
    RADIOBUTTON_WIDTH,
    RADIOBUTTON_X_FLAC,
    RADIOBUTTON_X_MP3,
    RADIOBUTTON_X_WAV,
    RADIOBUTTON_Y,
)
from gui_data.constants import (
    ALL_STEMS,
    AUDIO_TOOLS,
    CHOOSE_ENSEMBLE_OPTION,
    CHOOSE_PROC_METHOD_MAIN_LABEL,
    CHOOSE_STEM_PAIR,
    CHOSEN_PROCESS_METHOD_HELP,
    DEMUCS_ARCH_TYPE,
    ENSEMBLE_MODE,
    FLAC,
    FORMAT_SETTING_HELP,
    FOUR_STEM_ENSEMBLE,
    GPU_CONVERSION_MAIN_LABEL,
    HALF_PRECISION_MAIN_LABEL,
    IS_GPU_CONVERSION_HELP,
    IS_HALF_PRECISION_HELP,
    MDX_ARCH_TYPE,
    MODEL_SAMPLE_MODE_HELP,
    MP3,
    MULTI_STEM_ENSEMBLE,
    PRIMARY_STEM,
    PROCESS_METHODS,
    SAVE_CURRENT_SETTINGS_HELP,
    SAVE_STEM_ONLY_HELP,
    SELECT_SAVED_SETTINGS_MAIN_LABEL,
    VR_ARCH_PM,
    WAV,
    secondary_stem,
)
from uvr.ui.components import ComboBoxMenu
from uvr.ui.panels.audio_tools_panel import AudioToolsPanel
from uvr.ui.panels.demucs_panel import DemucsPanel
from uvr.ui.panels.ensemble_panel import EnsemblePanel
from uvr.ui.panels.mdx_panel import MDXPanel
from uvr.ui.panels.vr_panel import VRPanel

logger = logging.getLogger(__name__)


class OptionsCoordinator:
    """Orchestrates model tab sub-panels and shared settings placement."""

    def __init__(self, root: Any) -> None:
        self.root = root
        self.vr_panel = VRPanel(root, None)
        self.mdx_panel = MDXPanel(root, None)
        self.demucs_panel = DemucsPanel(root, None)
        self.ensemble_panel = EnsemblePanel(root, None)
        self.audio_tools_panel = AudioToolsPanel(root, None)

        self.root.vr_panel = self.vr_panel
        self.root.mdx_panel = self.mdx_panel
        self.root.demucs_panel = self.demucs_panel
        self.root.ensemble_panel = self.ensemble_panel
        self.root.audio_tools_panel = self.audio_tools_panel

    def setup_ui(self) -> None:
        """Constructs all model panels, radio options, and variable change listeners."""
        self.root.options_Frame = ttk.Frame(master=self.root)
        self.root.options_Frame.place(
            x=OPTIONS_FRAME_X,
            y=OPTIONS_FRAME_Y,
            width=OPTIONS_FRAME_WIDTH,
            height=self.root.OPTIONS_HEIGHT,
            relx=0,
            rely=0,
            relwidth=1,
            relheight=0,
        )

        options_frame = self.root.options_Frame

        # Update panel parent references
        self.vr_panel.parent = options_frame
        self.mdx_panel.parent = options_frame
        self.demucs_panel.parent = options_frame
        self.ensemble_panel.parent = options_frame
        self.audio_tools_panel.parent = options_frame

        # Save Format
        self.root.wav_button = ttk.Radiobutton(
            master=options_frame,
            text=WAV,
            variable=self.root.save_format_var,
            value=WAV,
        )
        self.root.wav_button.place(
            x=RADIOBUTTON_X_WAV,
            y=RADIOBUTTON_Y,
            width=RADIOBUTTON_WIDTH,
            height=RADIOBUTTON_HEIGHT,
            relx=0,
            rely=0 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.wav_button, text=f"{FORMAT_SETTING_HELP}{WAV}")

        self.root.flac_button = ttk.Radiobutton(
            master=options_frame,
            text=FLAC,
            variable=self.root.save_format_var,
            value=FLAC,
        )
        self.root.flac_button.place(
            x=RADIOBUTTON_X_FLAC,
            y=RADIOBUTTON_Y,
            width=RADIOBUTTON_WIDTH,
            height=RADIOBUTTON_HEIGHT,
            relx=1 / 3,
            rely=0 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.flac_button, text=f"{FORMAT_SETTING_HELP}{FLAC}")

        self.root.mp3_button = ttk.Radiobutton(
            master=options_frame,
            text=MP3,
            variable=self.root.save_format_var,
            value=MP3,
        )
        self.root.mp3_button.place(
            x=RADIOBUTTON_X_MP3,
            y=RADIOBUTTON_Y,
            width=RADIOBUTTON_WIDTH,
            height=RADIOBUTTON_HEIGHT,
            relx=2 / 3,
            rely=0 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.mp3_button, text=f"{FORMAT_SETTING_HELP}{MP3}")

        # Choose Conversion Method
        self.root.chosen_process_method_Label = self.root.main_window_LABEL_SET(
            options_frame, CHOOSE_PROC_METHOD_MAIN_LABEL
        )
        self.root.chosen_process_method_Label.place(
            x=0,
            y=MAIN_ROW_Y[0],
            width=LEFT_ROW_WIDTH,
            height=LABEL_HEIGHT,
            relx=0,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.chosen_process_method_Option = ComboBoxMenu(
            options_frame,
            textvariable=self.root.chosen_process_method_var,
            values=PROCESS_METHODS,
            command=lambda e: self.root.selection_action_process_method(
                self.root.chosen_process_method_var.get(),
                from_widget=True,
                is_from_conv_menu=True,
            ),
        )
        self.root.chosen_process_method_Option.place(
            x=0,
            y=MAIN_ROW_Y[1],
            width=LEFT_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=0,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(
            self.root.chosen_process_method_Label, text=CHOSEN_PROCESS_METHOD_HELP
        )

        # Choose Settings Option
        self.root.save_current_settings_Label = self.root.main_window_LABEL_SET(
            options_frame, SELECT_SAVED_SETTINGS_MAIN_LABEL
        )
        self.root.save_current_settings_Label_place = (
            lambda: self.root.save_current_settings_Label.place(
                x=MAIN_ROW_2_X[0],
                y=LOW_MENU_Y[0],
                width=0,
                height=LABEL_HEIGHT,
                relx=2 / 3,
                rely=6 / self.root.COL1_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL1_ROWS,
            )
        )
        self.root.save_current_settings_Option = ComboBoxMenu(
            options_frame,
            textvariable=self.root.save_current_settings_var,
            command=lambda e: self.root.selection_action_saved_settings(
                self.root.save_current_settings_var.get()
            ),
        )
        self.root.save_current_settings_Option_place = (
            lambda: self.root.save_current_settings_Option.place(
                x=MAIN_ROW_2_X[1],
                y=LOW_MENU_Y[1],
                width=MAIN_ROW_WIDTH,
                height=OPTION_HEIGHT,
                relx=2 / 3,
                rely=7 / self.root.COL1_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL1_ROWS,
            )
        )
        self.root.help_hints(
            self.root.save_current_settings_Label, text=SAVE_CURRENT_SETTINGS_HELP
        )

        # Initialize sub-panels
        self.mdx_panel.setup_ui()
        self.vr_panel.setup_ui()
        self.demucs_panel.setup_ui()
        self.ensemble_panel.setup_ui()
        self.audio_tools_panel.setup_ui()

        # Shared Settings
        self.root.is_gpu_conversion_Option = ttk.Checkbutton(
            master=options_frame,
            text=GPU_CONVERSION_MAIN_LABEL,
            variable=self.root.is_gpu_conversion_var,
        )
        self.root.is_gpu_conversion_Option_place = (
            lambda: self.root.is_gpu_conversion_Option.place(
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
        self.root.is_gpu_conversion_Disable = lambda: (
            self.root.is_gpu_conversion_Option.configure(state=tk.DISABLED),
            self.root.is_gpu_conversion_var.set(False),
        )
        self.root.is_gpu_conversion_Enable = (
            lambda: self.root.is_gpu_conversion_Option.configure(state=tk.NORMAL)
        )
        self.root.help_hints(self.root.is_gpu_conversion_Option, text=IS_GPU_CONVERSION_HELP)

        self.root.is_half_precision_Option = ttk.Checkbutton(
            master=options_frame,
            text=HALF_PRECISION_MAIN_LABEL,
            variable=self.root.is_half_precision_var,
        )
        self.root.is_half_precision_Option_place = (
            lambda: self.root.is_half_precision_Option.place(
                x=CHECK_BOX_X,
                y=CHECK_BOX_Y,
                width=CHECK_BOX_WIDTH,
                height=CHECK_BOX_HEIGHT,
                relx=1 / 3,
                rely=6 / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.help_hints(self.root.is_half_precision_Option, text=IS_HALF_PRECISION_HELP)

        self.root.is_primary_stem_only_Option = ttk.Checkbutton(
            master=options_frame,
            textvariable=self.root.is_primary_stem_only_Text_var,
            variable=self.root.is_primary_stem_only_var,
            command=lambda: self.root.is_primary_stem_only_Option_toggle(),
        )
        self.root.is_primary_stem_only_Option_place = (
            lambda: self.root.is_primary_stem_only_Option.place(
                x=CHECK_BOX_X,
                y=CHECK_BOX_Y,
                width=CHECK_BOX_WIDTH,
                height=CHECK_BOX_HEIGHT,
                relx=1 / 3,
                rely=7 / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.is_primary_stem_only_Option_toggle = (
            lambda: self.root.is_secondary_stem_only_var.set(False)
            if self.root.is_primary_stem_only_var.get()
            else self.root.is_secondary_stem_only_Option.configure(state=tk.NORMAL)
        )
        self.root.help_hints(self.root.is_primary_stem_only_Option, text=SAVE_STEM_ONLY_HELP)

        self.root.is_secondary_stem_only_Option = ttk.Checkbutton(
            master=options_frame,
            textvariable=self.root.is_secondary_stem_only_Text_var,
            variable=self.root.is_secondary_stem_only_var,
            command=lambda: self.root.is_secondary_stem_only_Option_toggle(),
        )
        self.root.is_secondary_stem_only_Option_place = (
            lambda: self.root.is_secondary_stem_only_Option.place(
                x=CHECK_BOX_X,
                y=CHECK_BOX_Y,
                width=CHECK_BOX_WIDTH,
                height=CHECK_BOX_HEIGHT,
                relx=1 / 3,
                rely=8 / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.is_secondary_stem_only_Option_toggle = (
            lambda: self.root.is_primary_stem_only_var.set(False)
            if self.root.is_secondary_stem_only_var.get()
            else self.root.is_primary_stem_only_Option.configure(state=tk.NORMAL)
        )
        self.root.is_stem_only_Options_Enable = lambda: (
            self.root.is_primary_stem_only_Option.configure(state=tk.NORMAL),
            self.root.is_secondary_stem_only_Option.configure(state=tk.NORMAL),
        )
        self.root.help_hints(self.root.is_secondary_stem_only_Option, text=SAVE_STEM_ONLY_HELP)

        self.root.model_sample_mode_Option = ttk.Checkbutton(
            master=options_frame,
            textvariable=self.root.model_sample_mode_duration_checkbox_var,
            variable=self.root.model_sample_mode_var,
        )
        self.root.model_sample_mode_Option_place = (
            lambda rely=9: self.root.model_sample_mode_Option.place(
                x=CHECK_BOX_X,
                y=CHECK_BOX_Y,
                width=CHECK_BOX_WIDTH,
                height=CHECK_BOX_HEIGHT,
                relx=1 / 3,
                rely=rely / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.help_hints(self.root.model_sample_mode_Option, text=MODEL_SAMPLE_MODE_HELP)

        # Full GUI List for placement toggle
        self.root.GUI_LIST = (
            self.root.vr_model_Label,
            self.root.vr_model_Option,
            self.root.aggression_setting_Label,
            self.root.aggression_setting_Option,
            self.root.window_size_Label,
            self.root.window_size_Option,
            self.root.demucs_model_Label,
            self.root.demucs_model_Option,
            self.root.demucs_stems_Label,
            self.root.demucs_stems_Option,
            self.root.segment_Label,
            self.root.segment_Option,
            self.root.mdx_net_model_Label,
            self.root.mdx_net_model_Option,
            self.root.overlap_mdx_Label,
            self.root.overlap_mdx_Option,
            self.root.overlap_mdx23_Option,
            self.root.mdxnet_stems_Label,
            self.root.mdxnet_stems_Option,
            self.root.mdx_segment_size_Label,
            self.root.mdx_segment_size_Option,
            self.root.chosen_ensemble_Label,
            self.root.chosen_ensemble_Option,
            self.root.save_current_settings_Label,
            self.root.save_current_settings_Option,
            self.root.ensemble_main_stem_Label,
            self.root.ensemble_main_stem_Option,
            self.root.ensemble_type_Label,
            self.root.ensemble_type_Option,
            self.root.ensemble_listbox_Label,
            self.root.ensemble_listbox_Frame,
            self.root.ensemble_listbox_Option,
            self.root.ensemble_listbox_scroll,
            self.root.chosen_audio_tool_Label,
            self.root.chosen_audio_tool_Option,
            self.root.choose_algorithm_Label,
            self.root.choose_algorithm_Option,
            self.root.time_stretch_rate_Label,
            self.root.time_stretch_rate_Option,
            self.root.wav_type_set_Label,
            self.root.wav_type_set_Option,
            self.root.pitch_rate_Label,
            self.root.pitch_rate_Option,
            self.root.fileOne_Label,
            self.root.fileOne_Entry,
            self.root.fileOne_Open,
            self.root.fileTwo_Label,
            self.root.fileTwo_Entry,
            self.root.fileTwo_Open,
            self.root.intro_analysis_Label,
            self.root.intro_analysis_Option,
            self.root.time_window_Label,
            self.root.time_window_Option,
            self.root.db_analysis_Label,
            self.root.db_analysis_Option,
            self.root.is_gpu_conversion_Option,
            self.root.is_primary_stem_only_Option,
            self.root.is_secondary_stem_only_Option,
            self.root.is_primary_stem_only_Demucs_Option,
            self.root.is_secondary_stem_only_Demucs_Option,
            self.root.model_sample_mode_Option,
            self.root.is_time_correction_Option,
            self.root.is_wav_ensemble_Option,
        )

        refresh_vars = (
            self.root.mdx_net_model_var,
            self.root.vr_model_var,
            self.root.demucs_model_var,
            self.root.is_chunk_demucs_var,
            self.root.is_chunk_mdxnet_var,
            self.root.model_download_demucs_var,
            self.root.model_download_mdx_var,
            self.root.model_download_vr_var,
            self.root.select_download_var,
            self.root.chosen_process_method_var,
            self.root.ensemble_main_stem_var,
        )

        for var in refresh_vars:
            var.trace_add("write", lambda *args: self.root.update_button_states())

    def update_main_widget_states(self) -> None:
        """Updates main widget states based on chosen process method."""

        def place_widgets(*widgets: Any) -> None:
            for widget in widgets:
                widget()

        def general_shared_buttons() -> None:
            place_widgets(
                self.root.is_gpu_conversion_Option_place,
                self.root.is_half_precision_Option_place,
                self.root.model_sample_mode_Option_place,
            )

        def stem_save_options() -> None:
            place_widgets(
                self.root.is_primary_stem_only_Option_place,
                self.root.is_secondary_stem_only_Option_place,
            )

        def stem_save_demucs_options() -> None:
            place_widgets(
                self.root.is_primary_stem_only_Demucs_Option_place,
                self.root.is_secondary_stem_only_Demucs_Option_place,
            )

        def no_ensemble_shared() -> None:
            place_widgets(
                self.root.save_current_settings_Label_place,
                self.root.save_current_settings_Option_place,
            )

        process_method = self.root.chosen_process_method_var.get()
        audio_tool = self.root.chosen_audio_tool_var.get()

        for widget in self.root.GUI_LIST:
            widget.place(x=-1000, y=-1000)

        if process_method == MDX_ARCH_TYPE:
            place_widgets(
                self.mdx_panel.place_widgets,
                general_shared_buttons,
                stem_save_options,
                no_ensemble_shared,
            )
        elif process_method == VR_ARCH_PM:
            place_widgets(
                self.vr_panel.place_widgets,
                general_shared_buttons,
                stem_save_options,
                no_ensemble_shared,
            )
        elif process_method == DEMUCS_ARCH_TYPE:
            place_widgets(
                self.demucs_panel.place_widgets,
                general_shared_buttons,
                stem_save_demucs_options,
                no_ensemble_shared,
            )
        elif process_method == AUDIO_TOOLS:
            self.audio_tools_panel.place_widgets(audio_tool)
        elif process_method == ENSEMBLE_MODE:
            place_widgets(
                self.ensemble_panel.place_widgets,
                general_shared_buttons,
                stem_save_options,
            )

        if not self.root.is_gpu_available:
            self.root.is_gpu_conversion_Disable()
            self.root.is_half_precision_Option.configure(state=tk.DISABLED)
            self.root.is_half_precision_var.set(False)
        else:
            try:
                cap = torch.cuda.get_device_capability()
                if cap[0] < 7:
                    self.root.is_half_precision_Option.configure(state=tk.DISABLED)
                    self.root.is_half_precision_var.set(False)
                    self.root.help_hints(
                        self.root.is_half_precision_Option,
                        text="Half-Precision disabled: GPU does not support Tensor Cores well (Compute Capability < 7.0).",
                    )
            except Exception:
                pass

        self.root.update_inputPaths()

    def update_stem_checkbox_labels(
        self,
        selection: str,
        demucs: bool = False,
        disable_boxes: bool = False,
        is_disable_demucs_boxes: bool = True,
    ) -> None:
        """Updates the 'save only' checkboxes based on the model selected."""
        stem_text = (
            self.root.is_primary_stem_only_Text_var,
            self.root.is_secondary_stem_only_Text_var,
        )

        if selection == ALL_STEMS:
            selection = PRIMARY_STEM
        else:
            self.root.is_stem_only_Options_Enable()

        if disable_boxes or selection == PRIMARY_STEM:
            self.root.is_primary_stem_only_Option.configure(state=tk.DISABLED)
            self.root.is_secondary_stem_only_Option.configure(state=tk.DISABLED)
            self.root.is_primary_stem_only_var.set(False)
            self.root.is_secondary_stem_only_var.set(False)
        else:
            self.root.is_primary_stem_only_Option.configure(state=tk.NORMAL)
            self.root.is_secondary_stem_only_Option.configure(state=tk.NORMAL)

        if demucs:
            stem_text = (
                self.root.is_primary_stem_only_Demucs_Text_var,
                self.root.is_secondary_stem_only_Demucs_Text_var,
            )

            if is_disable_demucs_boxes:
                self.root.is_primary_stem_only_Demucs_Option.configure(state=tk.DISABLED)
                self.root.is_secondary_stem_only_Demucs_Option.configure(state=tk.DISABLED)
                self.root.is_primary_stem_only_Demucs_var.set(False)
                self.root.is_secondary_stem_only_Demucs_var.set(False)

            if selection != PRIMARY_STEM:
                self.root.is_primary_stem_only_Demucs_Option.configure(state=tk.NORMAL)
                self.root.is_secondary_stem_only_Demucs_Option.configure(state=tk.NORMAL)

        def format_stem(s: str) -> str:
            if s == "noreverb":
                return "No Reverb"
            if s == "reverb":
                return "Reverb"
            if s == "dry":
                return "Dry"
            if s == "other":
                return "Other"
            return s

        stem_text[0].set(f"{format_stem(selection)} Only")
        stem_text[1].set(f"{format_stem(secondary_stem(selection))} Only")

    def selection_action_process_method(
        self, selection: str, from_widget: bool = False, is_from_conv_menu: bool = False
    ) -> None:
        """Checks model and variable status when toggling between process methods."""
        if is_from_conv_menu:
            self.root.update_main_widget_states()

        if from_widget:
            self.root.save_current_settings_var.set(CHOOSE_ENSEMBLE_OPTION)

        if selection == ENSEMBLE_MODE:
            ensemble_choice = self.root.ensemble_main_stem_var.get()
            if ensemble_choice in [CHOOSE_STEM_PAIR, FOUR_STEM_ENSEMBLE, MULTI_STEM_ENSEMBLE]:
                self.root.update_stem_checkbox_labels(PRIMARY_STEM, disable_boxes=True)
            else:
                self.root.update_stem_checkbox_labels(
                    self.root.return_ensemble_stems(is_primary=True)
                )
                self.root.is_stem_only_Options_Enable()
            return

        for method_type, model_var in self.root.method_mapper.items():
            if method_type in selection:
                self.root.selection_action_models(model_var.get())
                break
