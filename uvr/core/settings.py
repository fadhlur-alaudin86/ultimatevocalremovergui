"""Settings management and persistence module for UVR.
Provides secure JSON-based settings storage with automatic migration from
legacy pickle (data.pkl) files.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
from typing import Any

from gui_data.constants import DEFAULT_DATA
from uvr.constants import OTHER_FONT_PATH

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_JSON = "data.json"
LEGACY_SETTINGS_PKL = "data.pkl"


def migrate_pickle_to_json(
    pkl_path: str = LEGACY_SETTINGS_PKL,
    json_path: str = DEFAULT_SETTINGS_JSON,
) -> dict[str, Any] | None:
    """Safely migrate legacy pickle settings to JSON format.

    Args:
        pkl_path: Path to the legacy data.pkl file.
        json_path: Path to the target data.json file.

    Returns:
        Loaded dictionary if migration succeeded, None otherwise.
    """
    if not os.path.isfile(pkl_path):
        return None

    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
        if isinstance(data, dict):
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info("Migrated legacy %s to %s", pkl_path, json_path)
            return data
    except Exception as exc:
        logger.warning("Failed to migrate %s to JSON: %s", pkl_path, exc)

    return None


def save_data(data: dict[str, Any], file_path: str = DEFAULT_SETTINGS_JSON) -> None:
    """Save application settings dictionary as a JSON file.

    Also synchronizes legacy data.pkl for backward compatibility.

    Args:
        data: Settings dictionary to persist.
        file_path: Target path for the JSON settings file.
    """
    # Save modern JSON format
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as exc:
        logger.error("Failed to save settings to %s: %s", file_path, exc)

    # Maintain legacy pickle file for backward compatibility during migration
    try:
        with open(LEGACY_SETTINGS_PKL, "wb") as f:
            pickle.dump(data, f)
    except Exception as exc:
        logger.debug("Legacy pickle sync failed: %s", exc)


def load_data(file_path: str = DEFAULT_SETTINGS_JSON) -> dict[str, Any]:
    """Load saved settings dictionary, with fallback to legacy pkl or defaults.

    Args:
        file_path: Path to settings file (defaults to data.json).

    Returns:
        Dictionary containing all application configuration settings.
    """
    # 1. Try loading modern JSON format
    if os.path.isfile(file_path):
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            logger.warning("Corrupted settings file %s: %s. Recreating...", file_path, exc)

    # 2. Check for legacy pickle migration
    if os.path.isfile(LEGACY_SETTINGS_PKL):
        migrated = migrate_pickle_to_json(LEGACY_SETTINGS_PKL, file_path)
        if migrated is not None:
            return migrated

    # 3. Fallback to default data
    logger.info("Recreating settings with DEFAULT_DATA")
    save_data(data=DEFAULT_DATA, file_path=file_path)
    return dict(DEFAULT_DATA)


# Modern ergonomic aliases
load_settings = load_data
save_settings = save_data


def load_model_hash_data(dictionary_path: str) -> dict[str, Any]:
    """Load model hash mapping dictionary from a JSON file.

    Args:
        dictionary_path: Path to the JSON hash dictionary.

    Returns:
        Dictionary of model hash definitions.
    """
    try:
        with open(dictionary_path, encoding="utf-8") as d:
            return json.load(d)
    except Exception as exc:
        logger.warning("Error loading model hash data from %s: %s", dictionary_path, exc)
        return {}


def font_checker(
    font_file: str,
    other_font_dir: str = OTHER_FONT_PATH,
) -> tuple[str | None, str | None]:
    """Check custom font configuration and return font name and resolved file path.

    Args:
        font_file: Path to own_font.json configuration file.
        other_font_dir: Base directory containing supplementary fonts.

    Returns:
        Tuple of (font_name, resolved_font_file_path).
    """
    chosen_font_name: str | None = None
    chosen_font_file: str | None = None

    try:
        if os.path.isfile(font_file):
            with open(font_file, encoding="utf-8") as d:
                chosen_font = json.load(d)

            chosen_font_name = chosen_font.get("font_name")
            font_filename = chosen_font.get("font_file")
            if font_filename:
                resolved = os.path.join(other_font_dir, font_filename)
                if os.path.isfile(resolved):
                    chosen_font_file = resolved
    except Exception as exc:
        logger.debug("Font check failed: %s", exc)

    return chosen_font_name, chosen_font_file
