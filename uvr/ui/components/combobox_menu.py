"""Dropdown combobox with dynamic popup width calculation and platform mouse binds.
"""

from __future__ import annotations

from collections.abc import Callable
from tkinter import ttk
from tkinter.font import Font
from typing import Any

from gui_data.constants import READ_ONLY
from uvr.constants import IS_MACOS


class ComboBoxMenu(ttk.Combobox):
    """Combobox with automatic width adjustment for dropdown popup items."""

    def __init__(
        self,
        master: Any = None,
        dropdown_name: str | None = None,
        offset: int = 185,
        is_download_menu: bool = False,
        command: Callable | None = None,
        width: int | None = None,
        **kw: Any,
    ):
        super().__init__(master, **kw)
        self.menu_combobox_configure(is_download_menu, width=width)

        if dropdown_name and "values" in kw:
            self.update_dropdown_size(kw["values"], dropdown_name, offset)

        if command:
            self.command(command)

    def menu_combobox_configure(
        self,
        is_download_menu: bool = False,
        command: Callable | None = None,
        width: int | None = None,
    ) -> None:
        self.bind("<FocusIn>", self.focusin)
        self.bind("<MouseWheel>", lambda e: "break")

        if IS_MACOS:
            self.bind("<Enter>", lambda e: self.button_released())

        if not is_download_menu:
            self.configure(state=READ_ONLY)

        if command:
            self.command(command)

        if width:
            self.configure(width=width)

    def button_released(self, e: Any = None) -> None:
        self.event_generate("<Button-3>")
        self.event_generate("<ButtonRelease-3>")

    def command(self, command: Callable) -> None:
        if not self.bind("<<ComboboxSelected>>"):
            self.bind("<<ComboboxSelected>>", command)

    def focusin(self, e: Any) -> None:
        self.selection_clear()
        if IS_MACOS:
            self.event_generate("<Leave>")

    def update_dropdown_size(
        self,
        option_list: list[str],
        dropdown_name: str,
        offset: int = 185,
        command: Callable | None = None,
    ) -> None:
        dropdown_style = f"{dropdown_name}.TCombobox"
        if option_list:
            max_string = max(option_list, key=len)
            font = Font(font=self.cget("font"))
            width_in_pixels = font.measure(max_string) - offset
            width_in_pixels = max(width_in_pixels, 0)
        else:
            width_in_pixels = 0

        style = ttk.Style(self)
        style.configure(dropdown_style, padding=(0, 0, 0, 0), postoffset=(0, 0, width_in_pixels, 0))
        self.configure(style=dropdown_style)

        if command:
            self.command(command)
