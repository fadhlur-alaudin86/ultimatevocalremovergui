"""Unified Theme Manager coordinating CustomTkinter and sv_ttk appearance modes.
"""

from __future__ import annotations

import logging

import customtkinter as ctk

try:
    from gui_data import sv_ttk
    SV_TTK_AVAILABLE = True
except Exception:
    SV_TTK_AVAILABLE = False

try:
    import darkdetect
    DARKDETECT_AVAILABLE = True
except Exception:
    DARKDETECT_AVAILABLE = False

from uvr.constants import MAIN_FONT_NAME

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manages application-wide theme states (Dark, Light, System) across both

    CustomTkinter widgets and classic Tkinter / ttk widgets.
    """

    _current_mode: str = "dark"

    @classmethod
    def initialize(cls, mode: str = "dark", font_name: str = MAIN_FONT_NAME, font_size: int = 10) -> None:
        """Initialize the global theme system on application startup."""
        cls.set_mode(mode, font_name=font_name, font_size=font_size)

    @classmethod
    def set_mode(cls, mode: str, font_name: str = MAIN_FONT_NAME, font_size: int = 10) -> None:
        """Set application appearance mode ('dark', 'light', or 'system')."""
        normalized_mode = mode.lower()
        if normalized_mode not in {"dark", "light", "system"}:
            logger.warning("Unrecognized theme mode '%s', defaulting to 'dark'", mode)
            normalized_mode = "dark"

        cls._current_mode = normalized_mode

        # Set CustomTkinter appearance mode
        try:
            ctk.set_appearance_mode(normalized_mode)
        except Exception as exc:
            logger.debug("Failed setting CTk appearance mode: %s", exc)

        # Determine effective dark/light state for ttk
        effective_dark = cls.is_dark()
        ttk_theme = "dark" if effective_dark else "light"

        # Sync classic sv_ttk theme if available
        if SV_TTK_AVAILABLE:
            try:
                fg_color = "#F6F6F7" if effective_dark else "#1A1A1A"
                sv_ttk.set_theme(ttk_theme, font_name=font_name, f_size=font_size, fg_color_set=fg_color)
            except Exception as exc:
                logger.debug("sv_ttk theme sync skipped: %s", exc)

        logger.info("Theme set to %s (effective: %s)", normalized_mode, ttk_theme)

    @classmethod
    def toggle_mode(cls, font_name: str = MAIN_FONT_NAME, font_size: int = 10) -> str:
        """Toggle between dark and light modes. Returns the new mode."""
        new_mode = "light" if cls.is_dark() else "dark"
        cls.set_mode(new_mode, font_name=font_name, font_size=font_size)
        return new_mode

    @classmethod
    def get_mode(cls) -> str:
        """Get the currently configured theme mode."""
        return cls._current_mode

    @classmethod
    def is_dark(cls) -> bool:
        """Check if effective appearance mode is currently dark."""
        if cls._current_mode == "system":
            if DARKDETECT_AVAILABLE and darkdetect.isDark() is not None:
                return bool(darkdetect.isDark())
            ctk_mode = ctk.get_appearance_mode()
            return ctk_mode.lower() == "dark"
        return cls._current_mode == "dark"
