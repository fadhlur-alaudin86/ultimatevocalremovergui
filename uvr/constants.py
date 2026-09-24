"""Application-wide path constants and platform detection for UVR.
"""

from __future__ import annotations

import os
import platform
import sys

# Platform detection
OPERATING_SYSTEM = platform.system()
IS_WINDOWS = OPERATING_SYSTEM == "Windows"
IS_MACOS = OPERATING_SYSTEM == "Darwin"
IS_LINUX = OPERATING_SYSTEM == "Linux"

# Base repository directory
if getattr(sys, "frozen", False):
    BASE_PATH = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Splash doc
SPLASH_DOC = os.path.join(BASE_PATH, "tmp", "splash.txt")

# Models directories
MODELS_DIR = os.path.join(BASE_PATH, "models")
VR_MODELS_DIR = os.path.join(MODELS_DIR, "VR_Models")
MDX_MODELS_DIR = os.path.join(MODELS_DIR, "MDX_Net_Models")
DEMUCS_MODELS_DIR = os.path.join(MODELS_DIR, "Demucs_Models")
DEMUCS_NEWER_REPO_DIR = os.path.join(DEMUCS_MODELS_DIR, "v3_v4_repo")
MDX_MIXER_PATH = os.path.join(BASE_PATH, "lib_v5", "mixer.ckpt")

# Cache & Parameters
VR_HASH_DIR = os.path.join(VR_MODELS_DIR, "model_data")
VR_HASH_JSON = os.path.join(VR_MODELS_DIR, "model_data", "model_data.json")
MDX_HASH_DIR = os.path.join(MDX_MODELS_DIR, "model_data")
MDX_HASH_JSON = os.path.join(MDX_HASH_DIR, "model_data.json")
MDX_C_CONFIG_PATH = os.path.join(MDX_HASH_DIR, "mdx_c_configs")

DEMUCS_MODEL_NAME_SELECT = os.path.join(DEMUCS_MODELS_DIR, "model_data", "model_name_mapper.json")
MDX_MODEL_NAME_SELECT = os.path.join(MDX_MODELS_DIR, "model_data", "model_name_mapper.json")
ENSEMBLE_CACHE_DIR = os.path.join(BASE_PATH, "gui_data", "saved_ensembles")
SETTINGS_CACHE_DIR = os.path.join(BASE_PATH, "gui_data", "saved_settings")
VR_PARAM_DIR = os.path.join(BASE_PATH, "lib_v5", "vr_network", "modelparams")
SAMPLE_CLIP_PATH = os.path.join(BASE_PATH, "temp_sample_clips")
ENSEMBLE_TEMP_PATH = os.path.join(BASE_PATH, "ensemble_temps")
DOWNLOAD_MODEL_CACHE = os.path.join(BASE_PATH, "gui_data", "model_manual_download.json")

# Text resources
CR_TEXT = os.path.join(BASE_PATH, "gui_data", "cr_text.txt")
CHANGE_LOG = os.path.join(BASE_PATH, "gui_data", "change_log.txt")

# Image & Icon assets
ICON_IMG_PATH = os.path.join(BASE_PATH, "gui_data", "img", "GUI-Icon.ico")
MAIN_ICON_IMG_PATH = os.path.join(BASE_PATH, "gui_data", "img", "GUI-Icon.png")

# Font assets
OWN_FONT_PATH = os.path.join(BASE_PATH, "gui_data", "own_font.json")
MAIN_FONT_NAME = "Montserrat"
SEC_FONT_NAME = "Century Gothic"
FONT_PATH = os.path.join(BASE_PATH, "gui_data", "fonts", "Montserrat", "Montserrat.ttf")
SEC_FONT_PATH = os.path.join(BASE_PATH, "gui_data", "fonts", "centurygothic", "GOTHIC.ttf")
OTHER_FONT_PATH = os.path.join(BASE_PATH, "gui_data", "fonts", "other")
FONT_MAPPER = {
    MAIN_FONT_NAME: FONT_PATH,
    SEC_FONT_NAME: SEC_FONT_PATH,
}

# Audio chime alerts
COMPLETE_CHIME = os.path.join(BASE_PATH, "gui_data", "complete_chime.wav")
FAIL_CHIME = os.path.join(BASE_PATH, "gui_data", "fail_chime.wav")

# Default model weights
DENOISER_MODEL_PATH = os.path.join(VR_MODELS_DIR, "UVR-DeNoise-Lite.pth")
DEVERBER_MODEL_PATH = os.path.join(VR_MODELS_DIR, "UVR-DeEcho-DeReverb.pth")
