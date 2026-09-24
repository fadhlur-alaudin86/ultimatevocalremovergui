"""Audio playback, alert chimes, and system media integration utilities.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys

from uvr.constants import IS_LINUX, IS_MACOS, IS_WINDOWS

logger = logging.getLogger(__name__)


def play_chime(sound_file: str) -> None:
    """Play a short chime sound file in the background without blocking the UI thread.

    Gracefully falls back between platform tools (aplay, paplay, pw-play, afplay, winsound).
    """
    if not sound_file or not os.path.isfile(sound_file):
        return

    # Linux native audio utilities
    if IS_LINUX or sys.platform.startswith("linux"):
        for player in ["pw-play", "paplay", "aplay"]:
            if shutil.which(player):
                try:
                    subprocess.Popen(
                        [player, sound_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except Exception as exc:
                    logger.debug("Player %s failed: %s", player, exc)
                    continue

    # macOS native afplay
    if IS_MACOS or sys.platform == "darwin":
        if shutil.which("afplay"):
            try:
                subprocess.Popen(
                    ["afplay", sound_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception as exc:
                logger.debug("afplay failed: %s", exc)

    # Windows native winsound
    if IS_WINDOWS or sys.platform.startswith("win"):
        try:
            import winsound

            winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        except Exception as exc:
            logger.debug("winsound failed: %s", exc)

    # Fallback to playsound if available
    try:
        from playsound import playsound as _ps

        _ps(sound_file, block=False)
    except Exception as exc:
        logger.debug("Chime playback fallback failed: %s", exc)


def open_file_or_folder(path: str) -> None:
    """Open a file or folder in the default system file manager."""
    if not path or not os.path.exists(path):
        return

    try:
        if IS_MACOS:
            subprocess.Popen(["open", path])
        elif IS_LINUX:
            subprocess.Popen(["xdg-open", path])
        elif IS_WINDOWS:
            os.startfile(path)
    except Exception as exc:
        logger.warning("Failed to open path %s: %s", path, exc)
