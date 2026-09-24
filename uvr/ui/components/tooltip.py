"""Custom tooltip widget for displaying parameter descriptions and error alerts.
"""

from __future__ import annotations

import tkinter as tk

from gui_data.app_size_values import FONT_SIZE_2, FONT_SIZE_3
from uvr.constants import IS_WINDOWS, MAIN_FONT_NAME


class ToolTip:
    """Displays a hover tooltip or transient status popup over a Tk widget."""

    def __init__(self, widget: tk.Widget):
        self.widget = widget
        self.tooltip: tk.Toplevel | None = None

    def showtip(
        self,
        text: str,
        is_message_box: bool = False,
        is_success_message: bool | None = None,
    ) -> None:
        """Display the tooltip message."""
        self.hidetip()

        def create_label_config() -> dict:
            font_size = FONT_SIZE_3 if is_message_box else FONT_SIZE_2
            common_config = {
                "text": text,
                "relief": tk.SOLID,
                "borderwidth": 1,
                "font": (MAIN_FONT_NAME, f"{font_size}", "normal"),
            }
            if is_message_box:
                background_color = "#03692d" if is_success_message else "#8B0000"
                return {**common_config, "background": background_color, "foreground": "#ffffff"}
            else:
                return {
                    **common_config,
                    "background": "#1C1C1C",
                    "foreground": "#ffffff",
                    "highlightcolor": "#898b8e",
                    "justify": tk.LEFT,
                }

        if is_message_box:
            temp_tooltip = tk.Toplevel(self.widget)
            temp_tooltip.wm_overrideredirect(True)
            temp_tooltip.withdraw()
            label = tk.Label(temp_tooltip, **create_label_config())
            label.pack()
            temp_tooltip.update() if IS_WINDOWS else temp_tooltip.update_idletasks()

            x = (
                self.widget.winfo_rootx()
                + (self.widget.winfo_width() // 2)
                - (temp_tooltip.winfo_reqwidth() // 2)
            )
            y = self.widget.winfo_rooty() + self.widget.winfo_height()
            temp_tooltip.destroy()
        else:
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label_config = create_label_config()
        if not is_message_box:
            label_config["padx"] = 10
            label_config["pady"] = 10
            label_config["wraplength"] = 750
        label = tk.Label(self.tooltip, **label_config)
        label.pack()

        if is_message_box:
            delay = 3000 if isinstance(is_success_message, bool) else 2000
            self.tooltip.after(delay, self.hidetip)

    def hidetip(self) -> None:
        """Dismiss active tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
