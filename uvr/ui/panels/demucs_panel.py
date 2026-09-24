"""Demucs Architecture Options Panel for UVR GUI."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui_data.app_size_values import (
    CHECK_BOX_HEIGHT,
    CHECK_BOX_WIDTH,
    CHECK_BOX_X,
    CHECK_BOX_Y,
    LABEL_HEIGHT,
    LEFT_ROW_WIDTH,
    LOW_MENU_Y,
    MAIN_ROW_2_X,
    MAIN_ROW_2_Y,
    MAIN_ROW_WIDTH,
    MAIN_ROW_X,
    MAIN_ROW_Y,
    OPTION_HEIGHT,
)
from gui_data.constants import (
    ALL_STEMS,
    CHOOSE_DEMUCS_MODEL_MAIN_LABEL,
    CHOOSE_MODEL,
    CHOOSE_MODEL_HELP,
    CHOOSE_SEGMENT_MAIN_LABEL,
    CHOOSE_STEMS_MAIN_LABEL,
    DEMUCS_2_STEM_OPTIONS,
    DEMUCS_4_STEM_OPTIONS,
    DEMUCS_6_STEM_MODEL,
    DEMUCS_6_STEM_OPTIONS,
    DEMUCS_ARCH_TYPE,
    DEMUCS_SEGMENTS,
    DEMUCS_STEMS_HELP,
    DEMUCS_UVR_MODEL,
    PRIMARY_STEM,
    REG_SEGMENTS,
    SAVE_STEM_ONLY_HELP,
    SEGMENT_HELP,
    VOCAL_STEM,
)
from uvr.ui.components import ComboBoxEditableMenu, ComboBoxMenu

logger = logging.getLogger(__name__)


class DemucsPanel:
    """Manages widgets and layout for the Demucs Architecture options."""

    def __init__(self, root: Any, parent_frame: Any) -> None:
        self.root = root
        self.parent = parent_frame

    def setup_ui(self) -> None:
        """Initializes Demucs controls on parent frame and attaches to root."""
        # Choose Demucs Models
        self.root.demucs_model_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_DEMUCS_MODEL_MAIN_LABEL
        )
        self.root.demucs_model_Label_place = lambda: self.root.demucs_model_Label.place(
            x=0,
            y=LOW_MENU_Y[0],
            width=LEFT_ROW_WIDTH,
            height=LABEL_HEIGHT,
            relx=0,
            rely=6 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.demucs_model_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.demucs_model_var,
            command=lambda event: self.root.selection_action(event, self.root.demucs_model_var),
        )
        self.root.demucs_model_Option_place = lambda: self.root.demucs_model_Option.place(
            x=0,
            y=LOW_MENU_Y[1],
            width=LEFT_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=0,
            rely=7 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(self.root.demucs_model_Label, text=CHOOSE_MODEL_HELP)

        # Choose Demucs Stems
        self.root.demucs_stems_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_STEMS_MAIN_LABEL
        )
        self.root.demucs_stems_Label_place = lambda: self.root.demucs_stems_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.demucs_stems_Option = ComboBoxMenu(
            self.parent, textvariable=self.root.demucs_stems_var
        )
        self.root.demucs_stems_Option_place = lambda: self.root.demucs_stems_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.demucs_stems_Label, text=DEMUCS_STEMS_HELP)

        # Demucs-Segment
        self.root.segment_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_SEGMENT_MAIN_LABEL
        )
        self.root.segment_Label_place = lambda: self.root.segment_Label.place(
            x=MAIN_ROW_2_X[0],
            y=MAIN_ROW_2_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=2 / 3,
            rely=2 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.segment_Option = ComboBoxEditableMenu(
            self.parent,
            values=DEMUCS_SEGMENTS,
            textvariable=self.root.segment_var,
            pattern=REG_SEGMENTS,
            default=DEMUCS_SEGMENTS,
        )
        self.root.segment_Option_place = lambda: self.root.segment_Option.place(
            x=MAIN_ROW_2_X[1],
            y=MAIN_ROW_2_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=2 / 3,
            rely=3 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.segment_Label, text=SEGMENT_HELP)

        # Stem A
        self.root.is_primary_stem_only_Demucs_Option = ttk.Checkbutton(
            master=self.parent,
            textvariable=self.root.is_primary_stem_only_Demucs_Text_var,
            variable=self.root.is_primary_stem_only_Demucs_var,
            command=lambda: self.root.is_primary_stem_only_Demucs_Option_toggle(),
        )
        self.root.is_primary_stem_only_Demucs_Option_place = (
            lambda: self.root.is_primary_stem_only_Demucs_Option.place(
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
        self.root.is_primary_stem_only_Demucs_Option_toggle = (
            lambda: self.root.is_secondary_stem_only_Demucs_var.set(False)
            if self.root.is_primary_stem_only_Demucs_var.get()
            else self.root.is_secondary_stem_only_Demucs_Option.configure(state=tk.NORMAL)
        )
        self.root.help_hints(self.root.is_primary_stem_only_Demucs_Option, text=SAVE_STEM_ONLY_HELP)

        # Stem B
        self.root.is_secondary_stem_only_Demucs_Option = ttk.Checkbutton(
            master=self.parent,
            textvariable=self.root.is_secondary_stem_only_Demucs_Text_var,
            variable=self.root.is_secondary_stem_only_Demucs_var,
            command=lambda: self.root.is_secondary_stem_only_Demucs_Option_toggle(),
        )
        self.root.is_secondary_stem_only_Demucs_Option_place = (
            lambda: self.root.is_secondary_stem_only_Demucs_Option.place(
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
        self.root.is_secondary_stem_only_Demucs_Option_toggle = (
            lambda: self.root.is_primary_stem_only_Demucs_var.set(False)
            if self.root.is_secondary_stem_only_Demucs_var.get()
            else self.root.is_primary_stem_only_Demucs_Option.configure(state=tk.NORMAL)
        )
        self.root.is_stem_only_Demucs_Options_Enable = lambda: (
            self.root.is_primary_stem_only_Demucs_Option.configure(state=tk.NORMAL),
            self.root.is_secondary_stem_only_Demucs_Option.configure(state=tk.NORMAL),
        )
        self.root.help_hints(
            self.root.is_secondary_stem_only_Demucs_Option, text=SAVE_STEM_ONLY_HELP
        )

    def place_widgets(self) -> None:
        """Places all Demucs widgets in the options layout."""
        self.root.demucs_model_Label_place()
        self.root.demucs_model_Option_place()
        self.root.demucs_stems_Label_place()
        self.root.demucs_stems_Option_place()
        self.root.segment_Label_place()
        self.root.segment_Option_place()

    def update_button_states(self) -> None:
        """Updates available stems and selection handlers for chosen Demucs model."""
        if self.root.chosen_process_method_var.get() == DEMUCS_ARCH_TYPE:
            if self.root.demucs_stems_var.get() == ALL_STEMS:
                self.root.update_stem_checkbox_labels(PRIMARY_STEM, demucs=True)
            elif self.root.demucs_stems_var.get() == VOCAL_STEM:
                self.root.update_stem_checkbox_labels(
                    VOCAL_STEM, demucs=True, is_disable_demucs_boxes=False
                )
                self.root.is_stem_only_Demucs_Options_Enable()
            else:
                self.root.is_stem_only_Demucs_Options_Enable()

            if not self.root.demucs_model_var.get() == CHOOSE_MODEL:
                if DEMUCS_UVR_MODEL in self.root.demucs_model_var.get():
                    stems = DEMUCS_2_STEM_OPTIONS
                elif DEMUCS_6_STEM_MODEL in self.root.demucs_model_var.get():
                    stems = DEMUCS_6_STEM_OPTIONS
                else:
                    stems = DEMUCS_4_STEM_OPTIONS

                self.root.demucs_stems_Option["values"] = stems
                self.root.demucs_stems_Option.command(
                    lambda e: self.root.update_stem_checkbox_labels(
                        self.root.demucs_stems_var.get(), demucs=True
                    )
                )
