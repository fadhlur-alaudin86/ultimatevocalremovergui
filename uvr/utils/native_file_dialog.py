"""Native desktop file dialog manager for Linux (KDE kdialog / GTK zenity),

Windows, and macOS.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from tkinter import filedialog
from typing import Any

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = (
    "*.wav *.mp3 *.flac *.ogg *.m4a *.aac *.wma *.opus *.aiff *.alac"
)
DEFAULT_AUDIO_FILTER_LABEL = "Audio Files (*.wav, *.mp3, *.flac, ...)"


def is_linux() -> bool:
    """Check if current operating system is Linux or BSD."""
    return sys.platform.startswith("linux") or "bsd" in sys.platform


def is_kde() -> bool:
    """Detect if current desktop session is KDE Plasma."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    session = os.environ.get("DESKTOP_SESSION", "").upper()
    return "KDE" in desktop or "PLASMA" in desktop or "KDE" in session


def get_native_dialog_backend() -> str:
    """Determine the optimal file dialog backend: 'kdialog', 'zenity', or 'tk'."""
    if not is_linux():
        return "tk"

    if is_kde() and shutil.which("kdialog"):
        return "kdialog"

    if shutil.which("zenity"):
        return "zenity"

    if shutil.which("kdialog"):
        return "kdialog"

    return "tk"


def _run_kdialog(args: list[str]) -> tuple[int, str]:
    """Execute kdialog command safely."""
    try:
        proc = subprocess.run(["kdialog", *args], capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip()
    except (subprocess.SubprocessError, OSError) as exc:
        logger.debug("kdialog execution failed: %s", exc)
        return 1, ""


def _run_zenity(args: list[str]) -> tuple[int, str]:
    """Execute zenity command safely."""
    try:
        proc = subprocess.run(["zenity", *args], capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip()
    except (subprocess.SubprocessError, OSError) as exc:
        logger.debug("zenity execution failed: %s", exc)
        return 1, ""


def ask_open_filenames(
    title: str = "Select Audio files",
    initial_dir: str | None = None,
    parent: Any | None = None,
) -> tuple[str, ...]:
    """Prompt user to select one or multiple audio files using the native desktop dialog."""
    backend = get_native_dialog_backend()
    start_dir = (
        initial_dir
        if (initial_dir and os.path.isdir(initial_dir))
        else os.path.expanduser("~")
    )

    if backend == "kdialog":
        args = ["--multiple", "--separate-output", "--title", title]
        if parent and hasattr(parent, "winfo_id"):
            try:
                args.extend(["--attach", str(parent.winfo_id())])
            except (AttributeError, RuntimeError) as exc:
                logger.debug("Attach to parent winfo_id skipped: %s", exc)
        kdialog_filter = (
            f"{AUDIO_EXTENSIONS}|{DEFAULT_AUDIO_FILTER_LABEL}\n*|All Files (*)"
        )
        args.extend(["--getopenfilename", start_dir, kdialog_filter])
        rc, out = _run_kdialog(args)
        if rc == 0 and out:
            lines = [line.strip() for line in out.splitlines() if line.strip()]
            return tuple(lines)
        return ()

    if backend == "zenity":
        args = [
            "--file-selection",
            "--multiple",
            "--separator=\n",
            f"--title={title}",
            f"--filename={os.path.join(start_dir, '')}",
            f"--file-filter={DEFAULT_AUDIO_FILTER_LABEL} | {AUDIO_EXTENSIONS}",
            "--file-filter=All Files | *",
            "--modal",
        ]
        rc, out = _run_zenity(args)
        if rc == 0 and out:
            lines = [line.strip() for line in out.splitlines() if line.strip()]
            return tuple(lines)
        return ()

    # Fallback to Tkinter filedialog
    types = [("Audio Files", AUDIO_EXTENSIONS), ("All Files", "*.*")]
    return tuple(
        filedialog.askopenfilenames(
            parent=parent,
            title=title,
            initialdir=initial_dir,
            filetypes=types,
        )
    )


def ask_open_filename(
    title: str = "Select Audio file",
    initial_dir: str | None = None,
    parent: Any | None = None,
) -> str:
    """Prompt user to select a single audio file using the native desktop dialog."""
    backend = get_native_dialog_backend()
    start_dir = (
        initial_dir
        if (initial_dir and os.path.isdir(initial_dir))
        else os.path.expanduser("~")
    )

    if backend == "kdialog":
        args = ["--title", title]
        if parent and hasattr(parent, "winfo_id"):
            try:
                args.extend(["--attach", str(parent.winfo_id())])
            except (AttributeError, RuntimeError) as exc:
                logger.debug("Attach to parent winfo_id skipped: %s", exc)
        kdialog_filter = (
            f"{AUDIO_EXTENSIONS}|{DEFAULT_AUDIO_FILTER_LABEL}\n*|All Files (*)"
        )
        args.extend(["--getopenfilename", start_dir, kdialog_filter])
        rc, out = _run_kdialog(args)
        return out if (rc == 0 and out) else ""

    if backend == "zenity":
        args = [
            "--file-selection",
            f"--title={title}",
            f"--filename={os.path.join(start_dir, '')}",
            f"--file-filter={DEFAULT_AUDIO_FILTER_LABEL} | {AUDIO_EXTENSIONS}",
            "--file-filter=All Files | *",
            "--modal",
        ]
        rc, out = _run_zenity(args)
        return out if (rc == 0 and out) else ""

    # Fallback to Tkinter filedialog
    types = [("Audio Files", AUDIO_EXTENSIONS), ("All Files", "*.*")]
    return filedialog.askopenfilename(
        parent=parent,
        title=title,
        initialdir=initial_dir,
        filetypes=types,
    )


def ask_directory(
    title: str = "Select Folder",
    initial_dir: str | None = None,
    parent: Any | None = None,
) -> str:
    """Prompt user to select an existing directory using the native desktop dialog."""
    backend = get_native_dialog_backend()
    start_dir = (
        initial_dir
        if (initial_dir and os.path.isdir(initial_dir))
        else os.path.expanduser("~")
    )

    if backend == "kdialog":
        args = ["--title", title]
        if parent and hasattr(parent, "winfo_id"):
            try:
                args.extend(["--attach", str(parent.winfo_id())])
            except (AttributeError, RuntimeError) as exc:
                logger.debug("Attach to parent winfo_id skipped: %s", exc)
        args.extend(["--getexistingdirectory", start_dir])
        rc, out = _run_kdialog(args)
        return out if (rc == 0 and out) else ""

    if backend == "zenity":
        args = [
            "--file-selection",
            "--directory",
            f"--title={title}",
            f"--filename={os.path.join(start_dir, '')}",
            "--modal",
        ]
        rc, out = _run_zenity(args)
        return out if (rc == 0 and out) else ""

    # Fallback to Tkinter filedialog
    return filedialog.askdirectory(
        parent=parent,
        title=title,
        initialdir=initial_dir,
    )
