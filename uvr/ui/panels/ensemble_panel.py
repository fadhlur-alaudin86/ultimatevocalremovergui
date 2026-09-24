"""Ensemble Mode Options Panel for UVR GUI."""

from __future__ import annotations

import json
import logging
import os
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui_data.app_size_values import (
    ENSEMBLE_LISTBOX_FRAME_HEIGHT,
    ENSEMBLE_LISTBOX_FRAME_WIDTH,
    ENSEMBLE_LISTBOX_FRAME_X,
    ENSEMBLE_LISTBOX_FRAME_Y,
    ENSEMBLE_LISTBOX_SCROLL_HEIGHT,
    ENSEMBLE_LISTBOX_SCROLL_WIDTH,
    ENSEMBLE_LISTBOX_SCROLL_X,
    ENSEMBLE_LISTBOX_SCROLL_Y,
    FONT_SIZE_1,
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
    AVAILABLE_MODELS_MAIN_LABEL,
    CHOOSE_ENSEMBLE_ALGORITHM_MAIN_LABEL,
    CHOOSE_ENSEMBLE_OPTION,
    CHOOSE_MAIN_PAIR_MAIN_LABEL,
    CHOOSE_STEM_PAIR,
    CHOSEN_ENSEMBLE_HELP,
    CLEAR_ENSEMBLE,
    ENSEMBLE_CHECK,
    ENSEMBLE_LISTBOX_HELP,
    ENSEMBLE_MAIN_STEM,
    ENSEMBLE_MAIN_STEM_HELP,
    ENSEMBLE_OPTIONS,
    ENSEMBLE_OPTIONS_MAIN_LABEL,
    ENSEMBLE_TYPE,
    ENSEMBLE_TYPE_HELP,
    FOUR_STEM_ENSEMBLE,
    MULTI_STEM_ENSEMBLE,
    OPT_SEPARATOR_SAVE,
    PRIMARY_STEM,
    SAVE_ENSEMBLE,
    SECONDARY_STEM,
)
from uvr.constants import ENSEMBLE_CACHE_DIR, MAIN_FONT_NAME
from uvr.ui.components import ComboBoxMenu

logger = logging.getLogger(__name__)


class EnsemblePanel:
    """Manages widgets and model stem selection logic for Ensemble Mode."""

    def __init__(self, root: Any, parent_frame: Any) -> None:
        self.root = root
        self.parent = parent_frame

    def setup_ui(self) -> None:
        """Initializes Ensemble Mode controls on parent frame and attaches to root."""
        # Ensemble Mode
        self.root.chosen_ensemble_Label = self.root.main_window_LABEL_SET(
            self.parent, ENSEMBLE_OPTIONS_MAIN_LABEL
        )
        self.root.chosen_ensemble_Label_place = lambda: self.root.chosen_ensemble_Label.place(
            x=0,
            y=LOW_MENU_Y[0],
            width=LEFT_ROW_WIDTH,
            height=LABEL_HEIGHT,
            relx=0,
            rely=6 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.chosen_ensemble_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.chosen_ensemble_var,
            command=lambda e: self.selection_action_chosen_ensemble(
                self.root.chosen_ensemble_var.get()
            ),
        )
        self.root.chosen_ensemble_Option_place = lambda: self.root.chosen_ensemble_Option.place(
            x=0,
            y=LOW_MENU_Y[1],
            width=LEFT_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=0,
            rely=7 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(self.root.chosen_ensemble_Label, text=CHOSEN_ENSEMBLE_HELP)

        # Ensemble Main Stems
        self.root.ensemble_main_stem_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_MAIN_PAIR_MAIN_LABEL
        )
        self.root.ensemble_main_stem_Label_place = lambda: self.root.ensemble_main_stem_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.ensemble_main_stem_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.ensemble_main_stem_var,
            values=ENSEMBLE_MAIN_STEM,
            command=lambda e: self.selection_action_ensemble_stems(
                self.root.ensemble_main_stem_var.get()
            ),
        )
        self.root.ensemble_main_stem_Option_place = (
            lambda: self.root.ensemble_main_stem_Option.place(
                x=MAIN_ROW_X[1],
                y=MAIN_ROW_Y[1],
                width=MAIN_ROW_WIDTH,
                height=OPTION_HEIGHT,
                relx=1 / 3,
                rely=3 / self.root.COL1_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL1_ROWS,
            )
        )
        self.root.help_hints(self.root.ensemble_main_stem_Label, text=ENSEMBLE_MAIN_STEM_HELP)

        # Ensemble Algorithm
        self.root.ensemble_type_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_ENSEMBLE_ALGORITHM_MAIN_LABEL
        )
        self.root.ensemble_type_Label_place = lambda: self.root.ensemble_type_Label.place(
            x=MAIN_ROW_2_X[0],
            y=MAIN_ROW_2_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=2 / 3,
            rely=2 / 11,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.ensemble_type_Option = ComboBoxMenu(
            self.parent, textvariable=self.root.ensemble_type_var, values=ENSEMBLE_TYPE
        )
        self.root.ensemble_type_Option_place = lambda: self.root.ensemble_type_Option.place(
            x=MAIN_ROW_2_X[1],
            y=MAIN_ROW_2_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=2 / 3,
            rely=3 / 11,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(self.root.ensemble_type_Label, text=ENSEMBLE_TYPE_HELP)

        # Ensemble Save Ensemble Outputs
        self.root.ensemble_listbox_Label = self.root.main_window_LABEL_SET(
            self.parent, AVAILABLE_MODELS_MAIN_LABEL
        )
        self.root.ensemble_listbox_Label_place = lambda: self.root.ensemble_listbox_Label.place(
            x=MAIN_ROW_2_X[0],
            y=MAIN_ROW_2_Y[1],
            width=-35,
            height=LABEL_HEIGHT,
            relx=2 / 3,
            rely=5 / 11,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.ensemble_model_settings_button = ttk.Button(
            self.parent,
            image=self.root.help_img,
            command=self.root.open_ensemble_model_settings,
        )
        self.root.ensemble_model_settings_button_place = (
            lambda: self.root.ensemble_model_settings_button.place(
                x=MAIN_ROW_2_X[0] + 4,
                y=MAIN_ROW_2_Y[1],
                width=30,
                height=LABEL_HEIGHT,
                relx=1.0,
                rely=5 / 11,
                relwidth=0,
                relheight=1 / self.root.COL1_ROWS,
                anchor=tk.NE,
            )
        )
        self.root.ensemble_listbox_Frame = tk.Frame(
            self.parent,
            highlightbackground="#04332c",
            highlightcolor="#04332c",
            highlightthickness=1,
        )
        self.root.ensemble_listbox_Option = tk.Listbox(
            self.root.ensemble_listbox_Frame,
            selectmode=tk.MULTIPLE,
            activestyle="dotbox",
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
            background="#070708",
            exportselection=0,
            relief=tk.SOLID,
            borderwidth=0,
        )
        self.root.ensemble_listbox_scroll = ttk.Scrollbar(self.parent, orient=tk.VERTICAL)
        self.root.ensemble_listbox_Option.config(
            yscrollcommand=self.root.ensemble_listbox_scroll.set
        )
        self.root.ensemble_listbox_scroll.configure(
            command=self.root.ensemble_listbox_Option.yview
        )
        self.root.ensemble_listbox_Option_place = lambda: (
            self.root.ensemble_listbox_Frame.place(
                x=ENSEMBLE_LISTBOX_FRAME_X,
                y=ENSEMBLE_LISTBOX_FRAME_Y,
                width=ENSEMBLE_LISTBOX_FRAME_WIDTH,
                height=ENSEMBLE_LISTBOX_FRAME_HEIGHT,
                relx=2 / 3,
                rely=6 / 11,
                relwidth=1 / 3,
                relheight=1 / self.root.COL1_ROWS,
            ),
            self.root.ensemble_listbox_scroll.place(
                x=ENSEMBLE_LISTBOX_SCROLL_X,
                y=ENSEMBLE_LISTBOX_SCROLL_Y,
                width=ENSEMBLE_LISTBOX_SCROLL_WIDTH,
                height=ENSEMBLE_LISTBOX_SCROLL_HEIGHT,
                relx=2 / 3,
                rely=6 / 11,
                relwidth=1 / 10,
                relheight=1 / self.root.COL1_ROWS,
            ),
        )
        self.root.ensemble_listbox_Option_pack = (
            lambda: self.root.ensemble_listbox_Option.pack(fill=tk.BOTH, expand=1)
        )
        self.root.help_hints(self.root.ensemble_listbox_Label, text=ENSEMBLE_LISTBOX_HELP)

    def place_widgets(self) -> None:
        """Places all Ensemble Mode widgets in the options layout."""
        self.root.chosen_ensemble_Label_place()
        self.root.chosen_ensemble_Option_place()
        self.root.ensemble_main_stem_Label_place()
        self.root.ensemble_main_stem_Option_place()
        self.root.ensemble_type_Label_place()
        self.root.ensemble_type_Option_place()
        self.root.ensemble_listbox_Label_place()
        self.root.ensemble_model_settings_button_place()
        self.root.ensemble_listbox_Option_place()
        self.root.ensemble_listbox_Option_pack()

    def selection_action_chosen_ensemble(self, selection: str) -> None:
        """Activates specific actions depending on selected ensemble option."""
        if selection not in ENSEMBLE_OPTIONS:
            self.selection_action_chosen_ensemble_load_saved(selection)
        elif selection == SAVE_ENSEMBLE:
            self.root.chosen_ensemble_var.set(CHOOSE_ENSEMBLE_OPTION)
            self.root.pop_up_save_ensemble()
        elif selection == OPT_SEPARATOR_SAVE:
            self.root.chosen_ensemble_var.set(CHOOSE_ENSEMBLE_OPTION)
        elif selection == CLEAR_ENSEMBLE:
            self.root.ensemble_listbox_Option.selection_clear(0, "end")
            self.root.chosen_ensemble_var.set(CHOOSE_ENSEMBLE_OPTION)

    def selection_action_chosen_ensemble_load_saved(self, saved_ensemble: str) -> None:
        """Loads data from selected saved ensemble preset."""
        saved_data = None
        original_saved_ensemble = saved_ensemble
        saved_ensemble = saved_ensemble.replace(" ", "_")
        saved_ensemble_path = os.path.join(ENSEMBLE_CACHE_DIR, f"{saved_ensemble}.json")

        if os.path.isfile(saved_ensemble_path):
            with open(saved_ensemble_path, encoding="utf-8") as f:
                saved_data = json.load(f)

        if saved_data:
            self.root.last_loaded_ensemble = original_saved_ensemble
            self.selection_action_ensemble_stems(
                saved_data["ensemble_main_stem"], from_menu=False
            )
            self.root.ensemble_main_stem_var.set(saved_data["ensemble_main_stem"])
            self.root.ensemble_type_var.set(saved_data["ensemble_type"])

            if "is_save_all_outputs_ensemble" in saved_data:
                self.root.is_save_all_outputs_ensemble_var.set(
                    saved_data["is_save_all_outputs_ensemble"]
                )
            if "is_append_ensemble_name" in saved_data:
                self.root.is_append_ensemble_name_var.set(saved_data["is_append_ensemble_name"])
            if "is_wav_ensemble" in saved_data:
                self.root.is_wav_ensemble_var.set(saved_data["is_wav_ensemble"])
            if "is_gpu_conversion" in saved_data:
                self.root.is_gpu_conversion_var.set(saved_data["is_gpu_conversion"])
            if "is_half_precision" in saved_data:
                self.root.is_half_precision_var.set(saved_data["is_half_precision"])
            if "is_primary_stem_only" in saved_data:
                self.root.is_primary_stem_only_var.set(saved_data["is_primary_stem_only"])
            if "is_secondary_stem_only" in saved_data:
                self.root.is_secondary_stem_only_var.set(saved_data["is_secondary_stem_only"])

            self.root.saved_model_list = saved_data["selected_models"]

            for saved_model in list(self.root.saved_model_list):
                status = self.root.assemble_model_data(saved_model, ENSEMBLE_CHECK)[0].model_status
                if not status:
                    self.root.saved_model_list.remove(saved_model)

            indexes = self.root.ensemble_listbox_get_indexes_for_files(
                self.root.model_stems_list, self.root.saved_model_list
            )

            for i in indexes:
                self.root.ensemble_listbox_Option.selection_set(i)

        self.root.update_checkbox_text()

    def selection_action_ensemble_stems(
        self, selection: str, from_menu: bool = True, auto_update: Any = None
    ) -> None:
        """Filters models from ensemble listbox incompatible with selected ensemble stem."""
        is_multi_stem = False

        if selection != CHOOSE_STEM_PAIR:
            if selection in [FOUR_STEM_ENSEMBLE, MULTI_STEM_ENSEMBLE]:
                self.root.update_stem_checkbox_labels(PRIMARY_STEM, disable_boxes=True)
                self.root.update_ensemble_algorithm_menu(is_4_stem=True)
                self.root.ensemble_primary_stem = PRIMARY_STEM
                self.root.ensemble_secondary_stem = SECONDARY_STEM
                is_4_stem_check = True
                if selection == MULTI_STEM_ENSEMBLE:
                    is_multi_stem = True
            else:
                self.root.update_ensemble_algorithm_menu()
                self.root.is_stem_only_Options_Enable()
                stems = selection.partition("/")
                self.root.update_stem_checkbox_labels(stems[0])
                self.root.ensemble_primary_stem = stems[0]
                self.root.ensemble_secondary_stem = stems[2]
                is_4_stem_check = False

            self.root.model_stems_list = self.root.model_list(
                self.root.ensemble_primary_stem,
                self.root.ensemble_secondary_stem,
                is_4_stem_check=is_4_stem_check,
                is_multi_stem=is_multi_stem,
            )
            self.root.ensemble_listbox_Option.configure(state=tk.NORMAL)
            self.root.ensemble_listbox_clear_and_insert_new(self.root.model_stems_list)

            if auto_update:
                indexes = self.root.ensemble_listbox_get_indexes_for_files(
                    self.root.model_stems_list, auto_update
                )
                self.root.ensemble_listbox_select_from_indexs(indexes)
        else:
            self.root.ensemble_listbox_Option.configure(state=tk.DISABLED)
            self.root.update_stem_checkbox_labels(PRIMARY_STEM, disable_boxes=True)
            self.root.model_stems_list = ()

        if from_menu:
            self.root.chosen_ensemble_var.set(CHOOSE_ENSEMBLE_OPTION)
