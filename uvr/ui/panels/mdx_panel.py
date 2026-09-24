"""MDX-Net Architecture Options Panel for UVR GUI."""

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
    MENU_COMBOBOX_WIDTH,
    OPTION_HEIGHT,
)
from gui_data.constants import (
    ALL_STEMS,
    CHOOSE_MDX_MODEL_MAIN_LABEL,
    CHOOSE_MODEL,
    CHOOSE_MODEL_HELP,
    CHOOSE_STEMS_MAIN_LABEL,
    DEMUCS_STEMS_HELP,
    DOWNLOAD_MORE,
    MDX23_OVERLAP,
    MDX_OVERLAP,
    MDX_OVERLAP_HELP,
    MDX_SEGMENT_SIZE_HELP,
    MDX_SEGMENTS,
    PRIMARY_STEM,
    REG_MDX_SEG,
    REG_OVERLAP,
    REG_OVERLAP23,
    SEGMENT_MDX_MAIN_LABEL,
    VOCAL_STEM,
)
from uvr.ui.components import ComboBoxEditableMenu, ComboBoxMenu

logger = logging.getLogger(__name__)


class MDXPanel:
    """Manages widgets and layout for the MDX-Net Architecture options."""

    def __init__(self, root: Any, parent_frame: Any) -> None:
        self.root = root
        self.parent = parent_frame

    def setup_ui(self) -> None:
        """Initializes MDX-Net controls on parent frame and attaches to root."""
        # Choose MDX-Net Model
        self.root.mdx_net_model_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_MDX_MODEL_MAIN_LABEL
        )
        self.root.mdx_net_model_Label_place = lambda: self.root.mdx_net_model_Label.place(
            x=0,
            y=LOW_MENU_Y[0],
            width=LEFT_ROW_WIDTH,
            height=LABEL_HEIGHT,
            relx=0,
            rely=6 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.mdx_net_model_Option = ComboBoxMenu(
            self.parent,
            textvariable=self.root.mdx_net_model_var,
            command=lambda event: self.root.selection_action(
                event, self.root.mdx_net_model_var, is_mdx_net=True
            ),
        )
        self.root.mdx_net_model_Option_place = lambda: self.root.mdx_net_model_Option.place(
            x=0,
            y=LOW_MENU_Y[1],
            width=LEFT_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=0,
            rely=7 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL1_ROWS,
        )
        self.root.help_hints(self.root.mdx_net_model_Label, text=CHOOSE_MODEL_HELP)

        # MDX-Overlap
        self.root.overlap_mdx_Label = self.root.main_window_LABEL_SET(self.parent, "OVERLAP")
        self.root.overlap_mdx_Label_place = lambda: self.root.overlap_mdx_Label.place(
            x=MAIN_ROW_2_X[0],
            y=MAIN_ROW_2_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=2 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.overlap_mdx_Option = ComboBoxEditableMenu(
            self.parent,
            values=MDX_OVERLAP,
            width=MENU_COMBOBOX_WIDTH,
            textvariable=self.root.overlap_mdx_var,
            pattern=REG_OVERLAP,
            default=MDX_OVERLAP,
        )
        self.root.overlap_mdx_Option_place = lambda: self.root.overlap_mdx_Option.place(
            x=MAIN_ROW_2_X[1],
            y=MAIN_ROW_2_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=2 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        # MDX23-Overlap
        self.root.overlap_mdx23_Option = ComboBoxEditableMenu(
            self.parent,
            values=MDX23_OVERLAP,
            width=MENU_COMBOBOX_WIDTH,
            textvariable=self.root.overlap_mdx23_var,
            pattern=REG_OVERLAP23,
            default="8",
        )
        self.root.overlap_mdx23_Option_place = lambda: self.root.overlap_mdx23_Option.place(
            x=MAIN_ROW_2_X[1],
            y=MAIN_ROW_2_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=2 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.overlap_mdx_Label, text=MDX_OVERLAP_HELP)

        # Choose MDX-Net Stems
        self.root.mdxnet_stems_Label = self.root.main_window_LABEL_SET(
            self.parent, CHOOSE_STEMS_MAIN_LABEL
        )
        self.root.mdxnet_stems_Label_place = lambda: self.root.mdxnet_stems_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )

        self.root.mdxnet_stems_Option = ComboBoxMenu(
            self.parent, textvariable=self.root.mdxnet_stems_var
        )
        self.root.mdxnet_stems_Option_place = lambda: self.root.mdxnet_stems_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL2_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.mdxnet_stems_Label, text=DEMUCS_STEMS_HELP)

        # MDX-Segment Size
        self.root.mdx_segment_size_Label = self.root.main_window_LABEL_SET(
            self.parent, SEGMENT_MDX_MAIN_LABEL
        )
        self.root.mdx_segment_size_Label_place = lambda: self.root.mdx_segment_size_Label.place(
            x=MAIN_ROW_X[0],
            y=MAIN_ROW_Y[0],
            width=0,
            height=LABEL_HEIGHT,
            relx=1 / 3,
            rely=2 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.mdx_segment_size_Option = ComboBoxEditableMenu(
            self.parent,
            values=MDX_SEGMENTS,
            width=MENU_COMBOBOX_WIDTH,
            textvariable=self.root.mdx_segment_size_var,
            pattern=REG_MDX_SEG,
            default="Default",
        )
        self.root.mdx_segment_size_Option_place = lambda: self.root.mdx_segment_size_Option.place(
            x=MAIN_ROW_X[1],
            y=MAIN_ROW_Y[1],
            width=MAIN_ROW_WIDTH,
            height=OPTION_HEIGHT,
            relx=1 / 3,
            rely=3 / self.root.COL1_ROWS,
            relwidth=1 / 3,
            relheight=1 / self.root.COL2_ROWS,
        )
        self.root.help_hints(self.root.mdx_segment_size_Label, text=MDX_SEGMENT_SIZE_HELP)

    def place_widgets(self) -> None:
        """Places all MDX widgets in the options layout."""
        self.root.mdx_net_model_Label_place()
        self.root.mdx_net_model_Option_place()

    def update_main_widget_states_mdx(self) -> None:
        """Updates main widget states if MDX model selection is not download more."""
        if not self.root.mdx_net_model_var.get() == DOWNLOAD_MORE:
            self.root.update_main_widget_states()

    def update_button_states_mdx(self, model_stems: list[str]) -> None:
        """Updates available stems for selected MDX model."""
        stems_list = list(model_stems)

        if len(stems_list) >= 3:
            stems_list.insert(0, ALL_STEMS)
            self.root.mdxnet_stems_var.set(ALL_STEMS)
        else:
            self.root.mdxnet_stems_var.set(stems_list[0])

        if self.root.mdxnet_stems_var.get() == ALL_STEMS:
            self.root.update_stem_checkbox_labels(PRIMARY_STEM, disable_boxes=True)
        elif self.root.mdxnet_stems_var.get() == VOCAL_STEM:
            self.root.update_stem_checkbox_labels(VOCAL_STEM)
            self.root.is_stem_only_Options_Enable()
        else:
            self.root.update_stem_checkbox_labels(self.root.mdxnet_stems_var.get())
            self.root.is_stem_only_Options_Enable()

        if not self.root.mdx_net_model_var.get() == CHOOSE_MODEL:
            self.root.mdxnet_stems_Option["values"] = stems_list
            self.root.mdxnet_stems_Option.command(
                lambda e: self.root.update_stem_checkbox_labels(self.root.mdxnet_stems_var.get())
            )
