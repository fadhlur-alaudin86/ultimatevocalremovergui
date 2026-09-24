"""File operations, temporary folder cleanup, and directory management utilities.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from collections import Counter

logger = logging.getLogger(__name__)


def ensure_directory(dir_path: str) -> str:
    """Ensure directory exists, creating parents if necessary.

    Returns the directory path.
    """
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def file_check(original_dir: str, new_dir: str) -> None:
    """Migrate contents from legacy directory to new directory, removing legacy folder."""
    if os.path.isdir(original_dir):
        ensure_directory(new_dir)
        for item in os.listdir(original_dir):
            src = os.path.join(original_dir, item)
            dst = os.path.join(new_dir, item)
            try:
                shutil.move(src, dst)
            except Exception as exc:
                logger.debug("Could not move %s to %s: %s", src, dst, exc)

        try:
            if len(os.listdir(original_dir)) == 0:
                shutil.rmtree(original_dir)
        except Exception as exc:
            logger.debug("Could not remove old directory %s: %s", original_dir, exc)


def remove_unneeded_yamls(demucs_dir: str) -> None:
    """Clean unneeded Demucs YAML definition files from model directory."""
    if not os.path.isdir(demucs_dir):
        return

    for item in os.listdir(demucs_dir):
        if item.endswith(".yaml"):
            target = os.path.join(demucs_dir, item)
            if os.path.isfile(target):
                try:
                    os.remove(target)
                except Exception as exc:
                    logger.debug("Failed removing yaml %s: %s", target, exc)


def remove_temps(remove_dir: str) -> None:
    """Clean all contents of temporary directory safely."""
    if os.path.isdir(remove_dir):
        try:
            shutil.rmtree(remove_dir)
        except Exception as exc:
            logger.debug("Could not remove temp directory %s: %s", remove_dir, exc)


def extract_stems(audio_file_base: str, export_path: str) -> list[str]:
    """Parse output directory for exported stem files corresponding to a given base audio."""
    if not os.path.isdir(export_path):
        return []

    filenames = [file for file in os.listdir(export_path) if file.startswith(audio_file_base)]
    pattern = r"\(([^()]+)\)(?=[^()]*\.wav)"
    stem_list: list[str] = []

    for filename in filenames:
        match = re.search(pattern, filename)
        if match:
            stem_list.append(match.group(1))

    counter = Counter(stem_list)
    filtered_list = [item for item in stem_list if counter[item] > 1]
    return list(set(filtered_list))


ensure_dir = ensure_directory


def sanitize_filename(filename: str) -> str:
    """Sanitize string for safe filesystem usage across platforms."""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def get_file_extension(file_path: str) -> str:
    """Extract lowercase file extension with dot (e.g. '.wav')."""
    return os.path.splitext(file_path)[1].lower()


def is_supported_audio(file_path: str) -> bool:
    """Check if file matches supported audio extensions."""
    supported = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".wma"}
    return get_file_extension(file_path) in supported


def clean_empty_dirs(root_dir: str) -> None:
    """Recursively remove empty subdirectories within root_dir."""
    if not os.path.isdir(root_dir):
        return
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        if not dirnames and not filenames and dirpath != root_dir:
            try:
                os.rmdir(dirpath)
            except OSError:
                pass

