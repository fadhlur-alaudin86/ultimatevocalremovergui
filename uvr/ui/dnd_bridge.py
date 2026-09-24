"""CustomTkinter and TkinterDnD2 integration bridge.
"""

from __future__ import annotations

import logging
from typing import Any

import customtkinter as ctk

try:
    from gui_data.tkinterdnd2.TkinterDnD import DnDWrapper, _require
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False
    DnDWrapper = object
    _require = None

logger = logging.getLogger(__name__)


class CTkDnD(ctk.CTk, DnDWrapper):
    """CustomTkinter CTk root window augmented with TkinterDnD2 drag-and-drop capability."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ctk.CTk.__init__(self, *args, **kwargs)
        if DND_AVAILABLE and _require is not None:
            try:
                self.TkdndVersion = _require(self)
            except Exception as exc:
                logger.warning("Failed to initialize TkDnD in CTk root: %s", exc)


class CTkToplevelDnD(ctk.CTkToplevel, DnDWrapper):
    """CustomTkinter CTkToplevel dialog window augmented with TkinterDnD2 drag-and-drop capability."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ctk.CTkToplevel.__init__(self, *args, **kwargs)
        if DND_AVAILABLE and _require is not None:
            try:
                self.TkdndVersion = _require(self)
            except Exception as exc:
                logger.warning("Failed to initialize TkDnD in CTkToplevel: %s", exc)
