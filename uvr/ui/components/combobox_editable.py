"""Custom editable Combobox with regex validation and custom tooltip notifications.
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui_data.constants import INVALID_INPUT_E, OPT_SEPARATOR, READ_ONLY, USER_INPUT
from uvr.constants import IS_MACOS
from uvr.ui.components.tooltip import ToolTip


class ComboBoxEditableMenu(ttk.Combobox):
    """Combobox allowing user-entered arbitrary values validated by a regex pattern."""

    def __init__(
        self,
        master: Any = None,
        pattern: str | None = None,
        default: Any = None,
        width: int | None = None,
        is_stay_disabled: bool = False,
        **kw: Any,
    ):
        if "values" in kw:
            kw["values"] = (*tuple(kw["values"]), OPT_SEPARATOR, USER_INPUT)
        else:
            kw["values"] = (USER_INPUT,)

        super().__init__(master, **kw)

        self.textvariable = kw.get("textvariable", tk.StringVar())
        self.pattern = pattern or r".*"
        self.tooltip = ToolTip(self)
        self.is_user_input_var = tk.BooleanVar(value=False)
        self.is_stay_disabled = is_stay_disabled

        if isinstance(default, (str, int)):
            self.default = default
        elif default:
            self.default = default[0]
        else:
            self.default = ""

        self.menu_combobox_configure()
        self.var_validation(is_start_up=True)

        if width:
            self.configure(width=width)

    def menu_combobox_configure(self) -> None:
        self.bind("<<ComboboxSelected>>", self.check_input)
        self.bind("<Button-1>", lambda e: self.focus())
        self.bind("<FocusIn>", self.focusin)
        self.bind("<FocusOut>", lambda e: self.var_validation(is_focus_only=True))

        if IS_MACOS:
            self.bind("<Enter>", lambda e: self.button_released())

        if not self.is_stay_disabled:
            self.configure(state=READ_ONLY)

    def check_input(self, event: Any = None) -> None:
        if self.textvariable.get() == USER_INPUT:
            self.textvariable.set("")
            self.configure(state=tk.NORMAL)
            self.focus()
            self.selection_range(0, 0)
        else:
            self.var_validation()

    def var_validation(self, is_focus_only: bool = False, is_start_up: bool = False) -> None:
        if is_focus_only and not self.is_stay_disabled:
            self.configure(state=READ_ONLY)

        if re.fullmatch(self.pattern, str(self.textvariable.get())) is None:
            if not is_start_up and self.textvariable.get() not in (OPT_SEPARATOR, USER_INPUT):
                self.tooltip.showtip(INVALID_INPUT_E, True)

            self.textvariable.set(self.default)

    def button_released(self, e: Any = None) -> None:
        self.event_generate("<Button-3>")
        self.event_generate("<ButtonRelease-3>")

    def focusin(self, e: Any) -> None:
        self.selection_clear()
        if IS_MACOS:
            self.event_generate("<Leave>")
