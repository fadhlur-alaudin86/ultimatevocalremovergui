"""Preset and user profile management system for UVR configurations.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_PRESET_DIR = os.path.join("gui_data", "saved_settings", "presets")


class PresetManager:
    """Manages creation, retrieval, and persistence of model & audio processing presets."""

    def __init__(self, preset_dir: str = DEFAULT_PRESET_DIR) -> None:
        self.preset_dir = preset_dir
        os.makedirs(self.preset_dir, exist_ok=True)
        self._ensure_built_in_presets()

    def _ensure_built_in_presets(self) -> None:
        """Seed default recommended presets if they do not yet exist."""
        built_ins = {
            "Default Vocal Extraction": {
                "process_method": "VR Architecture",
                "save_format": "WAV",
                "wav_type_set": "PCM_16",
                "is_normalization": True,
                "is_secondary_stem_only": False,
                "is_primary_stem_only": False,
            },
            "High Quality Separation": {
                "process_method": "MDX-Net",
                "save_format": "FLAC",
                "wav_type_set": "PCM_24",
                "is_normalization": True,
                "is_secondary_stem_only": False,
                "is_primary_stem_only": False,
            },
            "Fast Preview": {
                "process_method": "VR Architecture",
                "save_format": "MP3",
                "mp3_bit_set": "192k",
                "is_model_sample_mode": True,
                "model_sample_mode_duration": 30,
            },
        }
        for name, cfg in built_ins.items():
            preset_file = os.path.join(self.preset_dir, f"{name}.json")
            if not os.path.isfile(preset_file):
                try:
                    with open(preset_file, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, indent=4)
                except Exception as exc:
                    logger.debug("Failed saving built-in preset %s: %s", name, exc)

    def list_presets(self) -> list[str]:
        """List all available preset profile names."""
        if not os.path.isdir(self.preset_dir):
            return []
        presets = []
        for file in sorted(os.listdir(self.preset_dir)):
            if file.endswith(".json"):
                presets.append(os.path.splitext(file)[0])
        return presets

    def save_preset(self, name: str, settings: dict[str, Any]) -> bool:
        """Save given settings dictionary under the specified preset name."""
        try:
            target_path = os.path.join(self.preset_dir, f"{name}.json")
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as exc:
            logger.error("Failed saving preset %s: %s", name, exc)
            return False

    def load_preset(self, name: str) -> dict[str, Any] | None:
        """Load settings dictionary for given preset name."""
        target_path = os.path.join(self.preset_dir, f"{name}.json")
        if not os.path.isfile(target_path):
            logger.warning("Preset not found: %s", name)
            return None
        try:
            with open(target_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Failed loading preset %s: %s", name, exc)
            return None

    def delete_preset(self, name: str) -> bool:
        """Delete an existing preset file."""
        target_path = os.path.join(self.preset_dir, f"{name}.json")
        if os.path.isfile(target_path):
            try:
                os.remove(target_path)
                return True
            except Exception as exc:
                logger.error("Failed deleting preset %s: %s", name, exc)
        return False
