"""Base modal dialog class with centered positioning and transient hierarchy.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from uvr.constants import (
    ICON_IMG_PATH,
    IS_WINDOWS,
    MAIN_ICON_IMG_PATH,
)


class CTkBaseDialog(ctk.CTkToplevel):
    """CustomTkinter modal and auxiliary dialog with centered positioning."""

    def __init__(
        self,
        parent: Any | None = None,
        title: str = "UVR Dialog",
        close_command: Callable | None = None,
        is_help_hints: bool = False,
        **kwargs: Any,
    ):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.title_text = title
        self.close_command = close_command
        self.is_help_hints = is_help_hints

        self.withdraw()
        self.resizable(False, False)
        if parent:
            self.transient(parent)
        self.title(title)

        # Set platform window icon
        try:
            if IS_WINDOWS:
                self.iconbitmap(ICON_IMG_PATH)
            else:
                self.tk.call("wm", "iconphoto", self._w, tk.PhotoImage(file=MAIN_ICON_IMG_PATH))
        except Exception:
            pass

    def center_and_show(self, parent_window: Any | None = None) -> None:
        """Position window centered over parent and deiconify."""
        ref = parent_window or self.parent
        self.update() if IS_WINDOWS else self.update_idletasks()

        if ref:
            rx = ref.winfo_x()
            ry = ref.winfo_y()
            rw = ref.winfo_width()
            rh = ref.winfo_height()
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            offset_x = (rw - w) // 2
            offset_y = (rh - h) // 2
            self.geometry(f"+{rx + offset_x}+{ry + offset_y}")

        self.deiconify()


class BaseDialog(CTkBaseDialog):
    """Backward-compatible alias for CTkBaseDialog."""
