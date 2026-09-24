"""VR Architecture Options Panel for UVR GUI."""

from __future__ import annotations

import logging
from typing import Any

from gui_data.app_size_values import (
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
    AGGRESSION_SETTING_HELP,
    AGGRESSION_SETTING_MAIN_LABEL,
    CHOOSE_MODEL_HELP,
    REG_AGGRESSION,
    REG_WINDOW,
    SELECT_VR_MODEL_MAIN_LABEL,
    VR_AGGRESSION,
    VR_WINDOW,
    WINDOW_SIZE_HELP,
    WINDOW_SIZE_MAIN_LABEL,
)
from uvr.ui.components import ComboBoxEditableMenu, ComboBoxMenu

logger = logging.getLogger(__name__)


class VRPanel:
    """Manages widgets and layout for the VR Architecture model options."""

    def __init__(self, root: Any, parent_frame: Any) -> None:
        self.root = root
        self.parent = parent_frame

    def setup_ui(self) -> None:
        """Initializes VR Architecture controls on parent frame and attaches to root."""
        # Choose VR Model
        self.root.vr_model_Label = self.root.main_window_LABEL_SET(
            self.parent, SELECT_VR_MODEL_MAIN_LABEL
        )
        self.root.vr_model_Label_place = lambda: self.root.vr_model_Label.place(
            x=0,
            y=LOW_MENU_Y[0],
            width=LEFT_ROW_WIDTH,
            height=LABEL_HEIGHT,
            relx=0,
            rely=6 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.vr_model_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.vr_model_var,
            command=lambda event: self.root.selection_action(event, self.root.vr_model_var),
        )
        self.root.vr_model_Option_place = lambda: self.root.vr_model_Option.place(
            x=0,
            y=LOW_MENU_Y[1],
            width=LEFT_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=0,
            rely=7 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(self.root.vr_model_Label, text=CHOOSE_MODEL_HELP)

        # Aggression Setting
        self.root.aggression_setting_Label = self.root.main_window_LABEL_SET(
            self.parent, AGGRESSION_SETTING_MAIN_LABEL
        )
        self.root.aggression_setting_Label_place = (
            lambda: self.root.aggression_setting_Label.place(
                x=MAIN_ROW_2_X[0],
                y=MAIN_ROW_2_Y[0],
                width=0,
                height=LABEL_HEIGHT,
                relx=2 / 3,
                rely=2 / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.aggression_setting_Option = ComboBoxEditableMenu(
            self.parent,
            values=VR_AGGRESSION,
            textvariable=self.root.aggression_setting_var,
            pattern=REG_AGGRESSION,
            default=VR_AGGRESSION[5],
        )
        self.root.aggression_setting_Option_place = (
            lambda: self.root.aggression_setting_Option.place(
                x=MAIN_ROW_2_X[1],
                y=MAIN_ROW_2_Y[1],
                width=MAIN_ROW_WIDTH,
                height=OPTION_HEIGHT,
                relx=2 / 3,
                rely=3 / self.root.COL2_ROWS,
                relwidth=1 / 3,
                relheight=1 / self.root.COL2_ROWS,
            )
        )
        self.root.help_hints(self.root.aggression_setting_Label, text=AGGRESSION_SETTING_HELP)

        # Window Size
        self.root.window_size_Label = self.root.main_window_LABEL_SET(
            self.parent, WINDOW_SIZE_MAIN_LABEL
        )
        self.root.window_size_Label_place = lambda: self.root.window_size_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.window_size_Option = ComboBoxEditableMenu(
            self.parent,
            values=VR_WINDOW,
            textvariable=self.root.window_size_var,
            pattern=REG_WINDOW,
            default=VR_WINDOW[1],
        )
        self.root.window_size_Option_place = lambda: self.root.window_size_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.window_size_Label, text=WINDOW_SIZE_HELP)

    def place_widgets(self) -> None:
        """Places all VR widgets in the options layout."""
        self.root.vr_model_Label_place()
        self.root.vr_model_Option_place()
        self.root.aggression_setting_Label_place()
        self.root.aggression_setting_Option_place()
        self.root.window_size_Label_place()
        self.root.window_size_Option_place()
