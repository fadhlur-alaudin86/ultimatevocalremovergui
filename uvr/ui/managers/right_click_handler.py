"""Right-click context menu handler for UVR GUI."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from typing import Any

from gui_data.app_size_values import FONT_SIZE_1
from gui_data.constants import (
    ALIGN_INPUTS,
    ALIGNMENT_TOOL,
    ALL_ARCH_SETTING_LOAD,
    AUDIO_TOOLS,
    DEMUCS_ARCH_TYPE,
    DEMUCS_OPTION,
    DEMUCS_SETTING_LOAD,
    ENSEMBLE_MODE,
    ENSEMBLE_OPTION,
    ERROR_OPTION,
    MDX_ARCH_TYPE,
    MDX_OPTION,
    MDX_SETTING_LOAD,
    SAVE_SET_OPTIONS,
    VR_ARCH_PM,
    VR_ARCH_SETTING_LOAD,
    VR_OPTION,
)
from uvr.constants import MAIN_FONT_NAME

logger = logging.getLogger(__name__)


class RightClickMenuHandler:
    """Manages context menus for text boxes, console, and main window."""

    def __init__(
        self,
        root: Any,
        right_click_release_linux: Callable[..., Any] | None = None,
    ) -> None:
        self.root = root
        self._right_click_release_linux = right_click_release_linux

    def _release_linux(self, menu: Any, top_win: Any = None) -> None:
        if self._right_click_release_linux:
            self._right_click_release_linux(menu, top_win=top_win)
        elif hasattr(self.root, "right_click_release_linux"):
            self.root.right_click_release_linux(menu, top_win=top_win)

    def right_click_select_settings_sub(
        self, parent_menu: tk.Menu, process_method: str | None
    ) -> tk.Menu:
        """Build and return a submenu of saved settings presets."""
        saved_settings_sub_menu = tk.Menu(
            parent_menu, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=False
        )
        settings_options = self.root.last_found_settings + tuple(SAVE_SET_OPTIONS)

        for opt in settings_options:
            opt_label = opt.replace("_", " ")
            saved_settings_sub_menu.add_command(
                label=opt_label,
                command=lambda o=opt_label: self.root.selection_action_saved_settings(
                    o, process_method=process_method
                ),
            )

        saved_settings_sub_menu.insert_separator(len(self.root.last_found_settings))
        return saved_settings_sub_menu

    def right_click_menu_popup(
        self, event: Any, text_box: bool = False, main_menu: bool = False
    ) -> None:
        """Displays the right-click context menu for text fields or the main window."""

        def add_text_edit_options(menu: tk.Menu) -> None:
            menu.add_command(label="Copy", command=self.right_click_menu_copy)
            menu.add_command(
                label="Paste",
                command=lambda: self.right_click_menu_paste(text_box=text_box),
            )
            menu.add_command(
                label="Delete",
                command=lambda: self.right_click_menu_delete(text_box=text_box),
            )

        def add_advanced_settings_options(
            menu: tk.Menu,
            settings_mapper: dict[str, Any],
            var_mapper: dict[str, Any],
        ) -> None:
            current_method = self.root.chosen_process_method_var.get()

            if current_method in settings_mapper and (
                var_mapper[current_method]
                or (
                    current_method == DEMUCS_ARCH_TYPE
                    and self.root.is_demucs_pre_proc_model_activate_var.get()
                )
            ):
                menu.add_cascade(
                    label="Select Saved Settings", menu=saved_settings_sub_load_for_menu
                )
                menu.add_separator()
                for method, option in settings_mapper.items():
                    if method != ENSEMBLE_MODE or current_method == ENSEMBLE_MODE:
                        menu.add_command(label=f"Advanced {method} Settings", command=option)
            elif current_method in settings_mapper:
                menu.add_command(
                    label=f"Advanced {current_method} Settings",
                    command=settings_mapper[current_method],
                )

        right_click_menu = tk.Menu(self.root, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)

        settings_mapper = {
            ENSEMBLE_MODE: lambda: self.root.check_is_menu_open(ENSEMBLE_OPTION),
            VR_ARCH_PM: lambda: self.root.check_is_menu_open(VR_OPTION),
            MDX_ARCH_TYPE: lambda: self.root.check_is_menu_open(MDX_OPTION),
            DEMUCS_ARCH_TYPE: lambda: self.root.check_is_menu_open(DEMUCS_OPTION),
        }

        var_mapper = {
            ENSEMBLE_MODE: True,
            VR_ARCH_PM: self.root.vr_is_secondary_model_activate_var.get(),
            MDX_ARCH_TYPE: self.root.mdx_is_secondary_model_activate_var.get(),
            DEMUCS_ARCH_TYPE: self.root.demucs_is_secondary_model_activate_var.get(),
        }

        saved_settings_sub_load_for_menu = tk.Menu(
            right_click_menu, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=False
        )
        for label, arch_type in [
            (VR_ARCH_SETTING_LOAD, VR_ARCH_PM),
            (MDX_SETTING_LOAD, MDX_ARCH_TYPE),
            (DEMUCS_SETTING_LOAD, DEMUCS_ARCH_TYPE),
            (ALL_ARCH_SETTING_LOAD, None),
        ]:
            submenu = self.right_click_select_settings_sub(
                saved_settings_sub_load_for_menu, arch_type
            )
            saved_settings_sub_load_for_menu.add_cascade(label=label, menu=submenu)

        if not main_menu:
            add_text_edit_options(right_click_menu)
        else:
            if (
                self.root.chosen_process_method_var.get() == AUDIO_TOOLS
                and self.root.chosen_audio_tool_var.get() == ALIGN_INPUTS
            ):
                right_click_menu.add_command(
                    label="Advanced Align Tool Settings",
                    command=lambda: self.root.check_is_menu_open(ALIGNMENT_TOOL),
                )
            else:
                add_advanced_settings_options(right_click_menu, settings_mapper, var_mapper)

            if not self.root.is_menu_settings_open:
                right_click_menu.add_command(
                    label="Additional Settings",
                    command=lambda: self.root.menu_settings(select_tab_2=True),
                )

            help_hints_label = "Enable" if not self.root.help_hints_var.get() else "Disable"
            right_click_menu.add_command(
                label=f"{help_hints_label} Help Hints",
                command=lambda: self.root.help_hints_var.set(not self.root.help_hints_var.get()),
            )

            if self.root.error_log_var.get():
                right_click_menu.add_command(
                    label="Error Log",
                    command=lambda: self.root.check_is_menu_open(ERROR_OPTION),
                )

        try:
            right_click_menu.tk_popup(event.x_root, event.y_root)
            self._release_linux(right_click_menu)
        finally:
            right_click_menu.grab_release()

    def right_click_menu_copy(self) -> None:
        """Copies highlighted text from the active text box to system clipboard."""
        highlighted_text = self.root.current_text_box.selection_get()
        self.root.clipboard_clear()
        self.root.clipboard_append(highlighted_text)

    def right_click_menu_paste(self, text_box: bool = False) -> None:
        """Pastes text from system clipboard into the active text box."""
        clipboard = self.root.clipboard_get()
        if text_box:
            self.right_click_menu_delete(text_box=True)
        else:
            self.right_click_menu_delete()
        self.root.current_text_box.insert(
            self.root.current_text_box.index(tk.INSERT), clipboard
        )

    def right_click_menu_delete(self, text_box: bool = False) -> None:
        """Deletes selected or all text from the active text box."""
        if text_box:
            try:
                s0 = self.root.current_text_box.index("sel.first")
                s1 = self.root.current_text_box.index("sel.last")
                self.root.current_text_box.tag_configure("highlight")
                self.root.current_text_box.tag_add("highlight", s0, s1)
                start_indexes = self.root.current_text_box.tag_ranges("highlight")[0::2]
                end_indexes = self.root.current_text_box.tag_ranges("highlight")[1::2]

                for start, end in zip(start_indexes, end_indexes, strict=False):
                    self.root.current_text_box.tag_remove("highlight", start, end)

                for start, end in zip(start_indexes, end_indexes, strict=False):
                    self.root.current_text_box.delete(start, end)
            except Exception as e:
                logger.error("RIGHT-CLICK-DELETE ERROR: %s", e)
        else:
            self.root.current_text_box.delete(0, tk.END)

    def right_click_console(self, event: Any) -> None:
        """Opens copy / select-all context menu for the console log widget."""
        right_click_menu = tk.Menu(
            self.root, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0
        )
        right_click_menu.add_command(label="Copy", command=self.root.command_Text.copy_text)
        right_click_menu.add_command(
            label="Select All", command=self.root.command_Text.select_all_text
        )

        try:
            right_click_menu.tk_popup(event.x_root, event.y_root)
            self._release_linux(right_click_menu)
        finally:
            right_click_menu.grab_release()
