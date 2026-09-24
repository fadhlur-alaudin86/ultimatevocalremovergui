"""UI Manager modules for UVR.
"""

from __future__ import annotations

from uvr.ui.managers.download_manager import DownloadManager
from uvr.ui.managers.process_controller import ProcessController
from uvr.ui.managers.queue_ui import QueueUI
from uvr.ui.managers.right_click_handler import RightClickMenuHandler
from uvr.ui.managers.settings_ui import SettingsManager

__all__ = [
    "DownloadManager",
    "ProcessController",
    "QueueUI",
    "RightClickMenuHandler",
    "SettingsManager",
]

