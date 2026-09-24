"""Application entrypoint and lifecycle orchestrator for Ultimate Vocal Remover (UVR).
"""

from __future__ import annotations

import logging
import os
import sys

from filelock import FileLock, Timeout

from gui_data.constants import BG_COLOR
from uvr.constants import BASE_PATH, IS_WINDOWS
from uvr.core.model_data import set_app_root
from uvr.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Launch the Ultimate Vocal Remover desktop application."""
    setup_logging()

    # Prevent multiple concurrent instances to avoid OOM
    lock_path = os.path.join(BASE_PATH, "UVR.lock")
    lock = FileLock(lock_path, timeout=1)

    try:
        with lock:
            if IS_WINDOWS:
                try:
                    from ctypes import windll, wintypes

                    windll.user32.SetThreadDpiAwarenessContext(wintypes.HANDLE(-1))
                except Exception as exc:
                    logger.debug("DPI awareness setup error: %s", exc)

            # Lazy import to ensure splash/environment is ready
            import UVR
            from UVR import MainWindow

            root = MainWindow()
            UVR.root = root
            set_app_root(root)

            root.update_checkbox_text()
            root.is_root_defined_var.set(True)
            root.is_check_splash = True

            root.update() if IS_WINDOWS else root.update_idletasks()
            root.deiconify()
            root.configure(bg=BG_COLOR)
            root.mainloop()
    except Timeout:
        print("Another instance of UVR is already running. Exiting to prevent Out of Memory (OOM) errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
