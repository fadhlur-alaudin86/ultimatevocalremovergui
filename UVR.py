# GUI modules
import hashlib
import json
import math
import os
import time

#start_time = time.time()
import audioread
import librosa
import natsort

import gui_data.sv_ttk

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import base64
import pickle
import queue
import shutil
import subprocess
import threading
import tkinter as tk
import tkinter.ttk as ttk
import traceback
import urllib.request
import webbrowser
from collections import Counter
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter.font import Font

import matchering as match
import psutil
import pyperclip
import soundfile as sf
import torch
import wget
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from kthread import KThread
from playsound import playsound as _playsound_original
from pyglet import font as pyglet_font

from __version__ import PATCH, PATCH_LINUX, PATCH_MAC, VERSION
from gui_data.app_size_values import *
from gui_data.constants import *
from gui_data.error_handling import error_dialouge, error_text
from gui_data.old_data_check import file_check, remove_temps, remove_unneeded_yamls
from gui_data.tkinterdnd2 import DND_FILES, TkinterDnD
from lib_v5 import spec_utils
from lib_v5.vr_network.model_param_init import ModelParameters
from separate import (
    SeperateDemucs,  # Model-related
    SeperateMDX,
    SeperateMDXC,
    SeperateVR,
    clear_gpu_cache,
    cuda_available,
    mps_available,
    save_format,  # Utility functions
)


def playsound(sound_file, *args, **kwargs):
    if sys.platform.startswith('linux'):
        for player in ['aplay', 'paplay', 'pw-play']:
            if shutil.which(player):
                try:
                    subprocess.Popen([player, sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except Exception:
                    continue
    try:
        _playsound_original(sound_file, *args, **kwargs)
    except Exception as e:
        print(f"Chime sound playback skipped/failed: {e}")
import re
import sys

import onnx
import yaml
from ml_collections import ConfigDict

is_gpu_available = cuda_available or mps_available
root = None

# Change the current working directory to the directory
# this file sits in
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_PATH)  # Change the current working directory to the base path

SPLASH_DOC = os.path.join(BASE_PATH, 'tmp', 'splash.txt')

if os.path.isfile(SPLASH_DOC):
    os.remove(SPLASH_DOC)

def get_execution_time(function, name):
    start = time.time()
    function()
    end = time.time()
    time_difference = end - start
    print(f'{name} Execution Time: ', time_difference)

PREVIOUS_PATCH_WIN = 'UVR_Patch_10_6_23_4_27'

is_dnd_compatible = False
banner_placement = -2

if OPERATING_SYSTEM=="Darwin":
    OPEN_FILE_func = lambda input_string:subprocess.Popen(["open", input_string])
    dnd_path_check = MAC_DND_CHECK
    banner_placement = -8
    current_patch = PATCH_MAC
    is_windows = False
    is_macos = True
    right_click_button = '<Button-2>'
    application_extension = ".dmg"
elif OPERATING_SYSTEM=="Linux":
    OPEN_FILE_func = lambda input_string:subprocess.Popen(["xdg-open", input_string])
    dnd_path_check = LINUX_DND_CHECK
    current_patch = PATCH_LINUX
    is_windows = False
    is_macos = False
    right_click_button = '<Button-3>'
    application_extension = ".zip"
elif OPERATING_SYSTEM=="Windows":
    OPEN_FILE_func = lambda input_string:os.startfile(input_string)
    dnd_path_check = WINDOWS_DND_CHECK
    current_patch = PATCH
    is_windows = True
    is_macos = False
    right_click_button = '<Button-3>'
    application_extension = ".exe"

def right_click_release_linux(window, top_win=None):
    if OPERATING_SYSTEM=="Linux":
        root.bind('<Button-1>', lambda e:window.destroy())
        if top_win:
            top_win.bind('<Button-1>', lambda e:window.destroy())

import ssl

try:
    import certifi
    ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
except Exception:
    pass
if is_windows:
    try:
        from ctypes import windll, wintypes
    except ImportError:
        pass
    
def close_process(q:queue.Queue):
    def close_splash():
        name = "UVR_Launcher.exe"
        for process in psutil.process_iter(attrs=["name"]):
            process_name = process.info.get("name")
            
            if process_name == name:
                try:
                    process.terminate()
                    q.put(f"{name} terminated.")  # Push message to queue
                    break
                except psutil.NoSuchProcess as e:
                    q.put(f"Error terminating {name}: {e}")  # Push error to queue
                    
                    try:
                        with open(SPLASH_DOC, 'w') as f:
                            f.write('1')
                    except Exception:
                        print('No splash screen.')

    thread = KThread(target=close_splash)
    thread.start()

# Settings utilities — now provided by uvr.core.settings
from uvr.core.settings import (
    font_checker,
    load_data,
    load_model_hash_data,
    save_data,
)

debugger = []

#--Constants--
#Models
MODELS_DIR = os.path.join(BASE_PATH, 'models')
VR_MODELS_DIR = os.path.join(MODELS_DIR, 'VR_Models')
MDX_MODELS_DIR = os.path.join(MODELS_DIR, 'MDX_Net_Models')
DEMUCS_MODELS_DIR = os.path.join(MODELS_DIR, 'Demucs_Models')
DEMUCS_NEWER_REPO_DIR = os.path.join(DEMUCS_MODELS_DIR, 'v3_v4_repo')
MDX_MIXER_PATH = os.path.join(BASE_PATH, 'lib_v5', 'mixer.ckpt')

#Cache & Parameters
VR_HASH_DIR = os.path.join(VR_MODELS_DIR, 'model_data')
VR_HASH_JSON = os.path.join(VR_MODELS_DIR, 'model_data', 'model_data.json')
MDX_HASH_DIR = os.path.join(MDX_MODELS_DIR, 'model_data')
MDX_HASH_JSON = os.path.join(MDX_HASH_DIR, 'model_data.json')
MDX_C_CONFIG_PATH = os.path.join(MDX_HASH_DIR, 'mdx_c_configs')

DEMUCS_MODEL_NAME_SELECT = os.path.join(DEMUCS_MODELS_DIR, 'model_data', 'model_name_mapper.json')
MDX_MODEL_NAME_SELECT = os.path.join(MDX_MODELS_DIR, 'model_data', 'model_name_mapper.json')
ENSEMBLE_CACHE_DIR = os.path.join(BASE_PATH, 'gui_data', 'saved_ensembles')
SETTINGS_CACHE_DIR = os.path.join(BASE_PATH, 'gui_data', 'saved_settings')
VR_PARAM_DIR = os.path.join(BASE_PATH, 'lib_v5', 'vr_network', 'modelparams')
SAMPLE_CLIP_PATH = os.path.join(BASE_PATH, 'temp_sample_clips')
ENSEMBLE_TEMP_PATH = os.path.join(BASE_PATH, 'ensemble_temps')
DOWNLOAD_MODEL_CACHE = os.path.join(BASE_PATH, 'gui_data', 'model_manual_download.json')

#CR Text
CR_TEXT = os.path.join(BASE_PATH, 'gui_data', 'cr_text.txt')

#Style
ICON_IMG_PATH = os.path.join(BASE_PATH, 'gui_data', 'img', 'GUI-Icon.ico')
if not is_windows:
    MAIN_ICON_IMG_PATH = os.path.join(BASE_PATH, 'gui_data', 'img', 'GUI-Icon.png')

OWN_FONT_PATH = os.path.join(BASE_PATH, 'gui_data', 'own_font.json')

MAIN_FONT_NAME = 'Montserrat'
SEC_FONT_NAME = 'Century Gothic'
FONT_PATH = os.path.join(BASE_PATH, 'gui_data', 'fonts', 'Montserrat', 'Montserrat.ttf')#
SEC_FONT_PATH = os.path.join(BASE_PATH, 'gui_data', 'fonts', 'centurygothic', 'GOTHIC.ttf')#
OTHER_FONT_PATH = os.path.join(BASE_PATH, 'gui_data', 'fonts', 'other')#

FONT_MAPPER = {MAIN_FONT_NAME:FONT_PATH,
               SEC_FONT_NAME:SEC_FONT_PATH}

#Other
COMPLETE_CHIME = os.path.join(BASE_PATH, 'gui_data', 'complete_chime.wav')
FAIL_CHIME = os.path.join(BASE_PATH, 'gui_data', 'fail_chime.wav')
CHANGE_LOG = os.path.join(BASE_PATH, 'gui_data', 'change_log.txt')

DENOISER_MODEL_PATH = os.path.join(VR_MODELS_DIR, 'UVR-DeNoise-Lite.pth')
DEVERBER_MODEL_PATH = os.path.join(VR_MODELS_DIR, 'UVR-DeEcho-DeReverb.pth')

MODEL_DATA_URLS = [VR_MODEL_DATA_LINK, MDX_MODEL_DATA_LINK, MDX_MODEL_NAME_DATA_LINK, DEMUCS_MODEL_NAME_DATA_LINK]
MODEL_DATA_FILES = [VR_HASH_JSON, MDX_HASH_JSON, MDX_MODEL_NAME_SELECT, DEMUCS_MODEL_NAME_SELECT]

file_check(os.path.join(MODELS_DIR, 'Main_Models'), VR_MODELS_DIR)
file_check(os.path.join(DEMUCS_MODELS_DIR, 'v3_repo'), DEMUCS_NEWER_REPO_DIR)
remove_unneeded_yamls(DEMUCS_MODELS_DIR)

remove_temps(ENSEMBLE_TEMP_PATH)
remove_temps(SAMPLE_CLIP_PATH)
remove_temps(os.path.join(BASE_PATH, 'img'))

if not os.path.isdir(ENSEMBLE_TEMP_PATH):
    os.mkdir(ENSEMBLE_TEMP_PATH)
    
if not os.path.isdir(SAMPLE_CLIP_PATH):
    os.mkdir(SAMPLE_CLIP_PATH)

model_hash_table = {}
data = load_data()

def drop(event, accept_mode: str = 'files'):
    path = event.data
    if accept_mode == 'folder':
        path = path.replace('{', '').replace('}', '')
        if not os.path.isdir(path):
            messagebox.showerror(parent=root,
                                    title=INVALID_FOLDER_ERROR_TEXT[0],
                                    message=INVALID_FOLDER_ERROR_TEXT[1])
            return
        root.export_path_var.set(path)
    elif accept_mode in ['files', FILE_1, FILE_2, FILE_1_LB, FILE_2_LB]:
        path = path.replace("{", "").replace("}", "")
        for dnd_file in dnd_path_check:
            path = path.replace(f" {dnd_file}", f";{dnd_file}")
        path = path.split(';')
        path[-1] = path[-1].replace(';', '')
        
        if accept_mode == 'files':
            root.inputPaths = tuple(path)
            root.process_input_selections()
            root.update_inputPaths()
        elif accept_mode in [FILE_1, FILE_2]:
            if len(path) == 2:
                root.select_audiofile(path[0])
                root.select_audiofile(path[1], is_primary=False)
                root.DualBatch_inputPaths = []
                root.check_dual_paths()
            elif len(path) == 1:
                if accept_mode == FILE_1:
                    root.select_audiofile(path[0])
                else:
                    root.select_audiofile(path[0], is_primary=False)

        elif accept_mode in [FILE_1_LB, FILE_2_LB]:
            return path
    else:
        return    

# --- Component classes now live in the uvr/ package ---
import customtkinter as ctk

from uvr.core.audio_tools import AudioTools
from uvr.core.ensembler import Ensembler
from uvr.core.history import HistoryManager
from uvr.core.model_data import ModelData, get_app_root, set_app_root
from uvr.core.presets import PresetManager
from uvr.core.queue_manager import QueueTask
from uvr.ui.components.combobox_editable import ComboBoxEditableMenu
from uvr.ui.components.combobox_menu import ComboBoxMenu
from uvr.ui.components.console import ThreadSafeConsole
from uvr.ui.components.listbox_batch import ListboxBatchFrame
from uvr.ui.components.tooltip import ToolTip
from uvr.ui.dialogs import (
    build_preproc_model_tab,
    build_secondary_model_tab,
    open_advanced_align_options,
    open_advanced_demucs_options,
    open_advanced_ensemble_options,
    open_advanced_mdx_options,
    open_advanced_vr_options,
    open_batch_dual,
    open_ensemble_model_settings,
    open_error_log,
    open_help_menu,
    open_manual_downloads,
    open_settings_menu,
    open_view_inputs,
    pop_up_change_model_defaults,
    pop_up_ensemble_model_settings,
    pop_up_input_stem_name,
    pop_up_mdx_c_param,
    pop_up_mdx_model,
    pop_up_mdx_model_sub_json_dump,
    pop_up_save_ensemble,
    pop_up_save_ensemble_sub_json_dump,
    pop_up_set_vocal_splitter,
    pop_up_vr_param,
    pop_up_vr_param_sub_json_dump,
)
from uvr.ui.dialogs import (
    check_dual_paths as _check_dual_paths,
)
from uvr.ui.dnd_bridge import CTkDnD
from uvr.ui.managers import (
    DownloadManager,
    ProcessController,
    QueueUI,
    RightClickMenuHandler,
    SettingsManager,
)
from uvr.ui.managers.download_manager import (
    read_bulliten_text_mac,
    vip_downloads,
)
from uvr.ui.panels import OptionsCoordinator
from uvr.ui.theme_manager import ThemeManager
from uvr.utils.native_file_dialog import (
    ask_directory,
    ask_open_filename,
    ask_open_filenames,
)
from uvr.utils.notifications import send_notification


class MainWindow(CTkDnD if is_dnd_compatible else ctk.CTk):
    # --Constants--
    # Layout

    IMAGE_HEIGHT = IMAGE_HEIGHT
    FILEPATHS_HEIGHT = FILEPATHS_HEIGHT
    OPTIONS_HEIGHT = OPTIONS_HEIGHT
    CONVERSIONBUTTON_HEIGHT = CONVERSIONBUTTON_HEIGHT
    COMMAND_HEIGHT = COMMAND_HEIGHT
    PROGRESS_HEIGHT = PROGRESS_HEIGHT
    QUEUE_HEIGHT = QUEUE_HEIGHT
    PADDING = PADDING
    WIDTH = WIDTH
    COL1_ROWS = 11
    COL2_ROWS = 11
    
    def __init__(self):
        global root
        root = self
        set_app_root(self)
        #Run the __init__ method on the tk.Tk class
        super().__init__()
        
        self.set_app_font()

        style = ttk.Style(self)
        style.map('TCombobox', selectbackground=[('focus', '#0c0c0c')], selectforeground=[('focus', 'white')])
        style.configure('TCombobox', selectbackground='#0c0c0c')
        #style.configure('TCheckbutton', indicatorsize=30)
        
        # Calculate window height
        height = self.IMAGE_HEIGHT + self.FILEPATHS_HEIGHT + self.OPTIONS_HEIGHT
        height += self.CONVERSIONBUTTON_HEIGHT + self.COMMAND_HEIGHT + self.PROGRESS_HEIGHT + self.QUEUE_HEIGHT + 27
        height += self.PADDING * 5  # Padding
        width = self.WIDTH
        self.main_window_width = width
        self.main_window_height = height

        # --Window Settings--
        self.withdraw()
        self.title('Ultimate Vocal Remover')
        # Set Geometry and Center Window
        self.geometry(f'{self.main_window_width}x{height}+{int(self.winfo_screenwidth()/2 - width/2)}+{int(self.winfo_screenheight()/2 - height/2 - 30)}')
 
        self.iconbitmap(ICON_IMG_PATH) if is_windows else self.tk.call('wm', 'iconphoto', self._w, tk.PhotoImage(file=MAIN_ICON_IMG_PATH))
        self.protocol("WM_DELETE_WINDOW", self.save_values)
        self.resizable(False, False)
        
        self.msg_queue = queue.Queue()
        # Create a custom style that inherits from the original Combobox style.
        
        if not is_windows:
            self.update()

        #Load Images
        img = ImagePath(BASE_PATH)
        self.logo_img = img.open_image(path=img.banner_path, size=(width, height))
        self.efile_img = img.efile_img
        self.stop_img = img.stop_img
        self.help_img = img.help_img
        self.download_img = img.download_img
        self.donate_img = img.donate_img
        self.key_img = img.key_img
        self.credits_img = img.credits_img
        self.play_img = img.play_img
        self.pause_img = img.pause_img
        self.up_img = img.up_img
        self.down_img = img.down_img
        
        self.right_img = img.right_img
        self.left_img = img.left_img
        self.img_mapper = {
            "down":img.down_img,
            "up":img.up_img,
            "copy":img.copy_img,
            "clear":img.clear_img
        }

        #Placeholders
        self.right_click_button = right_click_button
        self.error_log_var = tk.StringVar(value='')
        self.vr_secondary_model_names = []
        self.mdx_secondary_model_names = []
        self.demucs_secondary_model_names = []
        self.vr_primary_model_names = []
        self.mdx_primary_model_names = []
        self.demucs_primary_model_names = []
        
        self.vr_cache_source_mapper = {}
        self.mdx_cache_source_mapper = {}
        self.demucs_cache_source_mapper = {}
        
        # -Tkinter Value Holders-
        self.settings_manager = SettingsManager(self)
        self.download_manager = DownloadManager(self)
        self.process_controller = ProcessController(self)
        self.right_click_handler = RightClickMenuHandler(
            self, right_click_release_linux=right_click_release_linux
        )
        
        try:
            self.load_saved_vars(data)
        except Exception as e:
            self.error_log_var.set(error_text('Loading Saved Variables', e))
            self.load_saved_vars(DEFAULT_DATA)
            
        self.cached_sources_clear()
        
        self.method_mapper = {
            VR_ARCH_PM: self.vr_model_var,
            MDX_ARCH_TYPE: self.mdx_net_model_var,
            DEMUCS_ARCH_TYPE: self.demucs_model_var}

        self.vr_secondary_model_vars = {'voc_inst_secondary_model': self.vr_voc_inst_secondary_model_var,
                                        'other_secondary_model': self.vr_other_secondary_model_var,
                                        'bass_secondary_model': self.vr_bass_secondary_model_var,
                                        'drums_secondary_model': self.vr_drums_secondary_model_var,
                                        'is_secondary_model_activate': self.vr_is_secondary_model_activate_var,
                                        'voc_inst_secondary_model_scale': self.vr_voc_inst_secondary_model_scale_var,
                                        'other_secondary_model_scale': self.vr_other_secondary_model_scale_var,
                                        'bass_secondary_model_scale': self.vr_bass_secondary_model_scale_var,
                                        'drums_secondary_model_scale': self.vr_drums_secondary_model_scale_var}
        
        self.demucs_secondary_model_vars = {'voc_inst_secondary_model': self.demucs_voc_inst_secondary_model_var,
                                        'other_secondary_model': self.demucs_other_secondary_model_var,
                                        'bass_secondary_model': self.demucs_bass_secondary_model_var,
                                        'drums_secondary_model': self.demucs_drums_secondary_model_var,
                                        'is_secondary_model_activate': self.demucs_is_secondary_model_activate_var,
                                        'voc_inst_secondary_model_scale': self.demucs_voc_inst_secondary_model_scale_var,
                                        'other_secondary_model_scale': self.demucs_other_secondary_model_scale_var,
                                        'bass_secondary_model_scale': self.demucs_bass_secondary_model_scale_var,
                                        'drums_secondary_model_scale': self.demucs_drums_secondary_model_scale_var}
        
        self.mdx_secondary_model_vars = {'voc_inst_secondary_model': self.mdx_voc_inst_secondary_model_var,
                                        'other_secondary_model': self.mdx_other_secondary_model_var,
                                        'bass_secondary_model': self.mdx_bass_secondary_model_var,
                                        'drums_secondary_model': self.mdx_drums_secondary_model_var,
                                        'is_secondary_model_activate': self.mdx_is_secondary_model_activate_var,
                                        'voc_inst_secondary_model_scale': self.mdx_voc_inst_secondary_model_scale_var,
                                        'other_secondary_model_scale': self.mdx_other_secondary_model_scale_var,
                                        'bass_secondary_model_scale': self.mdx_bass_secondary_model_scale_var,
                                        'drums_secondary_model_scale': self.mdx_drums_secondary_model_scale_var}

        #Main Application Vars
        self.progress_bar_main_var = tk.IntVar(value=0)
        self.inputPathsEntry_var = tk.StringVar(value='')
        self.conversion_Button_Text_var = tk.StringVar(value=START_PROCESSING)
        self.last_loaded_ensemble = ''
        self.chosen_ensemble_var = tk.StringVar(value=CHOOSE_ENSEMBLE_OPTION)
        self.ensemble_main_stem_var = tk.StringVar(value=CHOOSE_STEM_PAIR)
        self.ensemble_type_var = tk.StringVar(value=MAX_MIN)
        self.save_current_settings_var = tk.StringVar(value=SELECT_SAVED_SET)
        self.demucs_stems_var = tk.StringVar(value=ALL_STEMS)
        self.mdxnet_stems_var = tk.StringVar(value=ALL_STEMS)
        self.is_primary_stem_only_Text_var = tk.StringVar(value='')
        self.is_secondary_stem_only_Text_var = tk.StringVar(value='')
        self.is_primary_stem_only_Demucs_Text_var = tk.StringVar(value='')
        self.is_secondary_stem_only_Demucs_Text_var = tk.StringVar(value='')
        self.scaling_var = tk.DoubleVar(value=1.0)
        self.active_processing_thread = None
        self.verification_thread = None
        self.is_menu_settings_open = False
        self.is_root_defined_var = tk.BooleanVar(value=False)
        self.is_check_splash = False
        
        self.is_open_menu_advanced_vr_options = tk.BooleanVar(value=False)
        self.is_open_menu_advanced_demucs_options = tk.BooleanVar(value=False)
        self.is_open_menu_advanced_mdx_options = tk.BooleanVar(value=False)
        self.is_open_menu_advanced_ensemble_options = tk.BooleanVar(value=False)
        self.is_open_menu_view_inputs = tk.BooleanVar(value=False)
        self.is_open_menu_help = tk.BooleanVar(value=False)
        self.is_open_menu_error_log = tk.BooleanVar(value=False)
        self.is_open_menu_advanced_align_options = tk.BooleanVar(value=False)

        self.menu_advanced_vr_options_close_window = None
        self.menu_advanced_demucs_options_close_window = None
        self.menu_advanced_mdx_options_close_window = None
        self.menu_advanced_ensemble_options_close_window = None
        self.menu_help_close_window = None
        self.menu_error_log_close_window = None
        self.menu_view_inputs_close_window = None
        self.menu_advanced_align_options_close_window = None

        self.mdx_model_params = None
        self.vr_model_params = None
        self.current_text_box = None
        self.wav_type_set = None
        self.is_online_model_menu = None
        self.progress_bar_var = tk.IntVar(value=0)
        self.is_confirm_error_var = tk.BooleanVar(value=False)
        self.clear_cache_torch = False
        self.vr_hash_MAPPER = load_model_hash_data(VR_HASH_JSON)
        self.mdx_hash_MAPPER = load_model_hash_data(MDX_HASH_JSON)
        self.mdx_name_select_MAPPER = load_model_hash_data(MDX_MODEL_NAME_SELECT)
        self.demucs_name_select_MAPPER = load_model_hash_data(DEMUCS_MODEL_NAME_SELECT)
        self._inject_community_name_mappings()
        self.is_gpu_available = is_gpu_available
        self.is_process_stopped = False
        self.inputs_from_dir = []
        self.iteration = 0
        self.true_model_count = 0
        self.vr_primary_source = None
        self.vr_secondary_source = None
        self.mdx_primary_source = None
        self.mdx_secondary_source = None
        self.demucs_primary_source = None
        self.demucs_secondary_source = None
        self.toplevels = []

        #Download Center Vars
        self.online_data = {}
        self.bulletin_data = INFO_UNAVAILABLE_TEXT
        self.is_online = False
        self.lastest_version = ''
        self.model_download_demucs_var = tk.StringVar(value='')
        self.model_download_mdx_var = tk.StringVar(value='')
        self.model_download_vr_var = tk.StringVar(value='')
        self.selected_download_var = tk.StringVar(value=NO_MODEL)
        self.select_download_var = tk.StringVar(value='')
        self.download_progress_info_var = tk.StringVar(value='')
        self.download_progress_percent_var = tk.StringVar(value='')
        self.download_progress_bar_var = tk.IntVar(value=0)
        self.download_stop_var = tk.StringVar(value='') 
        self.app_update_status_Text_var = tk.StringVar(value=LOADING_VERSION_INFO_TEXT)
        self.app_update_button_Text_var = tk.StringVar(value=CHECK_FOR_UPDATES_TEXT)
        
        self.user_code_validation_var = tk.StringVar(value='')
        self.download_link_path_var = tk.StringVar(value='') 
        self.download_save_path_var = tk.StringVar(value='')
        self.download_update_link_var = tk.StringVar(value='') 
        self.download_update_path_var = tk.StringVar(value='') 
        self.download_demucs_models_list = []
        self.download_demucs_newer_models = []
        self.refresh_list_Button = None
        self.stop_download_Button_DISABLE = None
        self.enable_tabs = None
        self.is_download_thread_active = False
        self.is_process_thread_active = False
        self.is_active_processing_thread = False
        self.active_download_thread = None
        self.pre_proc_model_toggle = None
        self.change_state_lambda = None
        self.file_one_sub_var = tk.StringVar(value=FILE_ONE_MAIN_LABEL) 
        self.file_two_sub_var = tk.StringVar(value=FILE_TWO_MAIN_LABEL) 
        self.cuda_device_list = GPU_DEVICE_NUM_OPTS
        self.opencl_list = GPU_DEVICE_NUM_OPTS
        
        #Model Update
        self.last_found_ensembles = ENSEMBLE_OPTIONS
        self.last_found_settings = ENSEMBLE_OPTIONS
        self.last_found_models = ()
        self.model_data_table = ()
        self.ensemble_model_list = ()
        self.default_change_model_list = ()
        
        # --Queue State--
        self.queue_lock = threading.RLock()
        self.processing_queue = []
        self.queue_task_counter = 0
        self.is_queue_worker_running = False
        self.active_queue_task = None
        self.file_progress_var = tk.StringVar(value="")
        


        self.history_manager = HistoryManager()
        self.preset_manager = PresetManager()
                
        # --Widgets--
        self.fill_main_frame()
        self.bind_widgets()
        
        # --Update Widgets--
        self.update_available_models()
        if self.active_custom_config_name:
            selection_file = self.active_custom_config_name.replace(" ", "_")
            if os.path.isfile(os.path.join(SETTINGS_CACHE_DIR, f'{selection_file}.json')):
                self.save_current_settings_var.set(self.active_custom_config_name)
        self.update_main_widget_states()
        self.update_loop()
        self.update_button_states()
        self.download_validate_code()
        self.delete_temps(is_start_up=True)
        self.ensemble_listbox_Option.configure(state=tk.DISABLED)
        self.command_Text.write(f'Ultimate Vocal Remover {VERSION} [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]')
        self.update_checkbox_text = lambda:self.selection_action_process_method(self.chosen_process_method_var.get())
        self.check_dual_paths()
        if not is_windows:
            self.update_idletasks()
        self.fill_gpu_list()
        self.online_data_refresh(user_refresh=False, is_start_up=True)
        
    # Menu Functions
    def main_window_LABEL_SET(self, master, text):return ttk.Label(master=master, text=text, background=BG_COLOR, font=self.font_set, foreground=FG_COLOR, anchor=tk.CENTER)
    def main_window_LABEL_SUB_SET(self, master, text_var):return ttk.Label(master=master, textvariable=text_var, background=BG_COLOR, font=self.font_set, foreground=FG_COLOR, anchor=tk.CENTER)
    def menu_title_LABEL_SET(self, frame, text, width=35):return ttk.Label(master=frame, text=text, font=(SEC_FONT_NAME, f"{FONT_SIZE_5}", "underline"), justify="center", foreground="#13849f", width=width, anchor=tk.CENTER)
    def menu_sub_LABEL_SET(self, frame, text, font_size=FONT_SIZE_2):return ttk.Label(master=frame, text=text, font=(MAIN_FONT_NAME, f"{font_size}"), foreground=FG_COLOR, anchor=tk.CENTER)
    def menu_FRAME_SET(self, frame, thickness=20):return tk.Frame(frame, highlightbackground=BG_COLOR, highlightcolor=BG_COLOR, highlightthicknes=thickness)
    def check_is_menu_settings_open(self):self.menu_settings() if not self.is_menu_settings_open else None
    def spacer_label(self, frame): return tk.Label(frame, text='', font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground='#868687', justify="left").grid()

    #Ensemble Listbox Functions
    def ensemble_listbox_get_all_selected_models(self):return [self.ensemble_listbox_Option.get(i) for i in self.ensemble_listbox_Option.curselection()]
    def ensemble_listbox_select_from_indexs(self, indexes):return [self.ensemble_listbox_Option.selection_set(i) for i in indexes]
    def ensemble_listbox_clear_and_insert_new(self, model_ensemble_updated):return (self.ensemble_listbox_Option.delete(0, 'end'), [self.ensemble_listbox_Option.insert(tk.END, models) for models in model_ensemble_updated])
    def ensemble_listbox_get_indexes_for_files(self, updated, selected):return [updated.index(model) for model in selected if model in updated]
    
    def set_app_font(self):
        chosen_font_name, _chosen_font_file = font_checker(OWN_FONT_PATH)

        if chosen_font_name:
            ThemeManager.set_mode("dark", chosen_font_name, 10)
            self.font_set = Font(family=chosen_font_name, size=FONT_SIZE_F2)
            self.font_entry = Font(family=chosen_font_name, size=FONT_SIZE_F2)
        else:
            ThemeManager.set_mode("dark", MAIN_FONT_NAME, 10)
            self.font_set = Font(family=SEC_FONT_NAME, size=FONT_SIZE_F2)
            self.font_entry = Font(family=MAIN_FONT_NAME, size=FONT_SIZE_F2)

    def toggle_theme_mode(self):
        """Toggle between Dark and Light appearance modes."""
        new_mode = ThemeManager.toggle_mode()
        if hasattr(self, 'command_Text'):
            self.command_Text.write(f"Appearance theme changed to {new_mode.capitalize()} mode.\n")
        return new_mode

    
    def process_iteration(self):
        self.iteration = self.iteration + 1
    
    def assemble_model_data(self, model=None, arch_type=ENSEMBLE_MODE, is_dry_check=False, is_change_def=False, is_get_hash_dir_only=False):

        if arch_type == ENSEMBLE_STEM_CHECK:
            
            model_data = self.model_data_table
            missing_models = [model.model_status for model in model_data if not model.model_status]
            
            if missing_models or not model_data:
                model_data: list[ModelData] = [ModelData(model_name, is_dry_check=is_dry_check, root=self) for model_name in self.ensemble_model_list]
                self.model_data_table = model_data

        if arch_type == KARAOKEE_CHECK:
            model_list = []
            model_data: list[ModelData] = [ModelData(model_name, is_dry_check=is_dry_check, root=self) for model_name in self.default_change_model_list]
            for model in model_data:
                if (model.model_status and model.is_karaoke) or model.is_bv_model:
                    model_list.append(model.model_and_process_tag)
            
            return model_list

        if arch_type == ENSEMBLE_MODE:
            model_data: list[ModelData] = [ModelData(model_name, root=self) for model_name in self.ensemble_listbox_get_all_selected_models()]
        if arch_type == ENSEMBLE_CHECK:
            model_data: list[ModelData] = [ModelData(model, is_change_def=is_change_def, is_get_hash_dir_only=is_get_hash_dir_only, root=self)]
        if arch_type == VR_ARCH_TYPE or arch_type == VR_ARCH_PM:
            model_data: list[ModelData] = [ModelData(model, VR_ARCH_TYPE, root=self)]
        if arch_type == MDX_ARCH_TYPE:
            model_data: list[ModelData] = [ModelData(model, MDX_ARCH_TYPE, root=self)]
        if arch_type == DEMUCS_ARCH_TYPE:
            model_data: list[ModelData] = [ModelData(model, DEMUCS_ARCH_TYPE, root=self)]#

        return model_data
        
    def clear_cache(self, network):
        
        if network == VR_ARCH_TYPE:
            dir = VR_HASH_DIR
        if network == MDX_ARCH_TYPE:
            dir = MDX_HASH_DIR     
        
        for filename in os.listdir(dir):
            filepath = os.path.join(dir, filename)
            if filename not in ['model_data.json', 'model_name_mapper.json', 'mdx_c_configs'] and not os.path.isdir(filepath):
                os.remove(filepath)
        
        self.vr_model_var.set(CHOOSE_MODEL)
        self.mdx_net_model_var.set(CHOOSE_MODEL)
        self.model_data_table.clear()
        self.chosen_ensemble_var.set(CHOOSE_ENSEMBLE_OPTION)
        self.ensemble_main_stem_var.set(CHOOSE_STEM_PAIR)
        self.ensemble_listbox_Option.configure(state=tk.DISABLED)
        self.update_checkbox_text()
    
    def thread_check(self, thread_to_check):
        '''Checks if thread is alive'''
        
        is_running = False
        
        if type(thread_to_check) is KThread:
            if thread_to_check.is_alive():
                is_running = True
                
        return is_running

    # -Widget Methods--

    def fill_main_frame(self):
        """Creates root window widgets"""
        
        self.title_Label = tk.Label(master=self, image=self.logo_img, compound=tk.TOP)
        self.title_Label.place(x=-2, y=banner_placement)

        self.fill_filePaths_Frame()
        self.fill_options_Frame()
        
        self.conversion_Button = ttk.Button(master=self, textvariable=self.conversion_Button_Text_var, command=self.process_initialize)
        self.conversion_Button.place(x=X_CONVERSION_BUTTON_1080P, y=BUTTON_Y_1080P, width=WIDTH_CONVERSION_BUTTON_1080P, height=HEIGHT_GENERIC_BUTTON_1080P,
                                    relx=0, rely=0, relwidth=1, relheight=0)
        
        self.conversion_Button_enable = lambda:(self.conversion_Button_Text_var.set(START_PROCESSING), self.conversion_Button.configure(state=tk.NORMAL))
        self.conversion_Button_disable = lambda message:(self.conversion_Button_Text_var.set(message), self.conversion_Button.configure(state=tk.DISABLED))
        
        self.stop_Button = ttk.Button(master=self, image=self.stop_img, command=lambda: self.confirm_stop_process(stop_all=False))
        self.stop_Button.place(x=X_STOP_BUTTON_1080P, y=BUTTON_Y_1080P, width=HEIGHT_GENERIC_BUTTON_1080P, height=HEIGHT_GENERIC_BUTTON_1080P,
                            relx=1, rely=0, relwidth=0, relheight=0)
        self.help_hints(self.stop_Button, text=STOP_HELP)
        
        self.stop_expand_Button = ttk.Button(master=self, text="▼", command=self.show_stop_menu)
        self.stop_expand_Button.place(x=X_STOP_MENU_BUTTON_1080P, y=BUTTON_Y_1080P, width=20, height=HEIGHT_GENERIC_BUTTON_1080P,
                            relx=1, rely=0, relwidth=0, relheight=0)
        
        self.stop_menu = tk.Menu(self, tearoff=0)
        self.stop_menu.add_command(label="Stop Active Queue", command=lambda: self.confirm_stop_process(stop_all=False))
        self.stop_menu.add_command(label="Stop All Queue", command=lambda: self.confirm_stop_process(stop_all=True))
        
        self.settings_Button = ttk.Button(master=self, image=self.help_img, command=self.check_is_menu_settings_open)
        self.settings_Button.place(x=X_SETTINGS_BUTTON_1080P, y=BUTTON_Y_1080P, width=HEIGHT_GENERIC_BUTTON_1080P, height=HEIGHT_GENERIC_BUTTON_1080P,
                                relx=1, rely=0, relwidth=0, relheight=0)
        self.help_hints(self.settings_Button, text=SETTINGS_HELP)
    
        self.progressbar = ttk.Progressbar(master=self, variable=self.progress_bar_main_var)
        self.progressbar.place(x=X_PROGRESSBAR_1080P, y=Y_OFFSET_PROGRESS_BAR_1080P, width=WIDTH_PROGRESSBAR_1080P, height=HEIGHT_PROGRESSBAR_1080P,
                            relx=0, rely=0, relwidth=1, relheight=0)

        self.progress_text_var = tk.StringVar(value="No Active Processing")
        self.progress_text_Label = tk.Label(master=self, textvariable=self.progress_text_var, font=(MAIN_FONT_NAME, FONT_SIZE_F1, "bold"), fg="#11cf7b", bg="#101014")
        self.progress_text_Label.place(x=X_PROGRESSBAR_1080P, y=Y_OFFSET_PROGRESS_TEXT_1080P, width=WIDTH_PROGRESSBAR_1080P, height=25,
                            relx=0, rely=0, relwidth=1, relheight=0)

        # Separator to separate process progress and start button
        self.separator = ttk.Separator(master=self, orient='horizontal')
        self.separator.place(x=15, y=Y_OFFSET_SEPARATOR_1080P, width=-30, height=2, relx=0, rely=0, relwidth=1, relheight=0)

        # Processing Queue on Main window
        self.queue_ui = QueueUI(self)
        self.queue_ui.setup_ui()

         # Select Music Files Option
        self.console_Frame = ttk.Frame(master=self)
        self.console_Frame.place(x=15, y=Y_OFFSET_CONSOLE_FRAME_1080P, width=-30, height=self.COMMAND_HEIGHT+7,
                                 relx=0, rely=0, relwidth=1, relheight=0)


        self.command_Text = ThreadSafeConsole(master=self.console_Frame, background='#0c0c0d',fg='#898b8e', highlightcolor="#0c0c0d",  font=(MAIN_FONT_NAME, FONT_SIZE_4), borderwidth=0)
        self.command_Text.pack(fill=tk.BOTH, expand=1)
        self.command_Text.bind(right_click_button, lambda e:self.right_click_console(e))
            
    def fill_filePaths_Frame(self):
        """Fill Frame with neccessary widgets"""

        # Select Music Files Option
        self.filePaths_Frame = ttk.Frame(master=self)
        self.filePaths_Frame.place(x=FILEPATHS_FRAME_X, y=FILEPATHS_FRAME_Y, width=FILEPATHS_FRAME_WIDTH, height=self.FILEPATHS_HEIGHT, relx=0, rely=0, relwidth=1, relheight=0)

        self.filePaths_musicFile_Button = ttk.Button(master=self.filePaths_Frame, text=SELECT_INPUT_TEXT, command=self.input_select_filedialog)
        self.filePaths_musicFile_Button.place(x=MUSICFILE_BUTTON_X, y=MUSICFILE_BUTTON_Y, width=MUSICFILE_BUTTON_WIDTH, height=MUSICFILE_BUTTON_HEIGHT, relx=0, rely=0, relwidth=0.3, relheight=0.5)
        self.filePaths_musicFile_Entry = ttk.Entry(master=self.filePaths_Frame, textvariable=self.inputPathsEntry_var, font=self.font_entry, state=tk.DISABLED)
        self.filePaths_musicFile_Entry.place(x=MUSICFILE_ENTRY_X, y=MUSICFILE_BUTTON_Y, width=MUSICFILE_ENTRY_WIDTH, height=MUSICFILE_ENTRY_HEIGHT, relx=0.3, rely=0, relwidth=0.7, relheight=0.5)                                   
        self.filePaths_musicFile_Open = ttk.Button(master=self.filePaths_Frame, image=self.efile_img, command=lambda:OPEN_FILE_func(os.path.dirname(self.inputPaths[0])) if self.inputPaths and os.path.isdir(os.path.dirname(self.inputPaths[0])) else self.error_dialoge(INVALID_INPUT))
        self.filePaths_musicFile_Open.place(x=OPEN_BUTTON_X, y=MUSICFILE_BUTTON_Y, width=OPEN_BUTTON_WIDTH, height=MUSICFILE_ENTRY_HEIGHT, relx=0.3, rely=0, relwidth=0.7, relheight=0.5)   

        # Add any additional configurations or method calls here
        self.filePaths_musicFile_Entry.configure(cursor="hand2")
        self.help_hints(self.filePaths_musicFile_Button, text=INPUT_FOLDER_ENTRY_HELP) 
        self.help_hints(self.filePaths_musicFile_Entry, text=INPUT_FOLDER_ENTRY_HELP_2)
        self.help_hints(self.filePaths_musicFile_Open, text=INPUT_FOLDER_BUTTON_HELP)     

        # Save To Option
        self.filePaths_saveTo_Button = ttk.Button(master=self.filePaths_Frame, text=SELECT_OUTPUT_TEXT, command=self.export_select_filedialog)
        self.filePaths_saveTo_Button.place(x=SAVETO_BUTTON_X, y=SAVETO_BUTTON_Y, width=SAVETO_BUTTON_WIDTH, height=SAVETO_BUTTON_HEIGHT, relx=0, rely=0.5, relwidth=0.3, relheight=0.5)
        self.filePaths_saveTo_Entry = ttk.Entry(master=self.filePaths_Frame, textvariable=self.export_path_var, font=self.font_entry, state=tk.DISABLED)
        self.filePaths_saveTo_Entry.place(x=SAVETO_ENTRY_X, y=SAVETO_BUTTON_Y, width=SAVETO_ENTRY_WIDTH, height=SAVETO_ENTRY_HEIGHT, relx=0.3, rely=0.5, relwidth=0.7, relheight=0.5)
        self.filePaths_saveTo_Open = ttk.Button(master=self.filePaths_Frame, image=self.efile_img, command=lambda:OPEN_FILE_func(Path(self.export_path_var.get())) if os.path.isdir(self.export_path_var.get()) else self.error_dialoge(INVALID_EXPORT))
        self.filePaths_saveTo_Open.place(x=OPEN_BUTTON_X, y=SAVETO_BUTTON_Y, width=OPEN_BUTTON_WIDTH, height=SAVETO_ENTRY_HEIGHT, relx=0.3, rely=0.5, relwidth=0.7, relheight=0.5)
        self.help_hints(self.filePaths_saveTo_Button, text=OUTPUT_FOLDER_ENTRY_HELP) 
        self.help_hints(self.filePaths_saveTo_Open, text=OUTPUT_FOLDER_BUTTON_HELP)     

    def fill_options_Frame(self):
        """Fill Frame with neccessary widgets"""
        self.options_coordinator = OptionsCoordinator(self)
        self.options_coordinator.setup_ui()
    
    def combo_box_selection_clear(self, frame:tk.Frame):
        for option in frame.winfo_children():
            if type(option) is ttk.Combobox or type(option) is ComboBoxEditableMenu:
                option.selection_clear()

    def focus_out_widgets(self, all_widgets, frame):
        for option in all_widgets:
            if type(option) is not ComboBoxEditableMenu:
                option.bind('<Button-1>', lambda e, opt=option:(opt.focus(), self.combo_box_selection_clear(frame)))

    def bind_widgets(self):
        """Bind widgets to the drag & drop mechanic"""
        
        self.chosen_audio_tool_align = tk.BooleanVar(value=True)        
        other_items = [self.options_Frame, self.filePaths_Frame, self.title_Label, self.progressbar, self.conversion_Button, self.settings_Button, self.stop_Button, self.command_Text]
        all_widgets = self.options_Frame.winfo_children() + self.filePaths_Frame.winfo_children() + other_items
        self.focus_out_widgets(all_widgets, self.options_Frame)
        
        if is_dnd_compatible:
            self.filePaths_saveTo_Button.drop_target_register(DND_FILES)
            self.filePaths_saveTo_Entry.drop_target_register(DND_FILES)
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', lambda e: drop(e, accept_mode='files'))
            self.filePaths_saveTo_Button.dnd_bind('<<Drop>>', lambda e: drop(e, accept_mode='folder'))
            self.filePaths_saveTo_Entry.dnd_bind('<<Drop>>', lambda e: drop(e, accept_mode='folder'))    
            
            self.fileOne_Entry.drop_target_register(DND_FILES)
            self.fileTwo_Entry.drop_target_register(DND_FILES)
            self.fileOne_Entry.dnd_bind('<<Drop>>', lambda e: drop(e, accept_mode=FILE_1))
            self.fileTwo_Entry.dnd_bind('<<Drop>>', lambda e: drop(e, accept_mode=FILE_2))    
            
        self.ensemble_listbox_Option.bind('<<ListboxSelect>>', lambda e: self.chosen_ensemble_var.set(CHOOSE_ENSEMBLE_OPTION))
        self.ensemble_listbox_Option.bind('<Double-1>', self.open_ensemble_model_settings)
        self.options_Frame.bind(right_click_button, lambda e:(self.right_click_menu_popup(e, main_menu=True), self.options_Frame.focus()))
        self.filePaths_musicFile_Entry.bind(right_click_button, lambda e:(self.input_right_click_menu(e), self.filePaths_musicFile_Entry.focus()))
        self.filePaths_musicFile_Entry.bind('<Button-1>', lambda e:(self.check_is_menu_open(INPUTS_MENU), self.filePaths_musicFile_Entry.focus()))

        self.fileOne_Entry.bind('<Button-1>', lambda e:self.menu_batch_dual())
        self.fileTwo_Entry.bind('<Button-1>', lambda e:self.menu_batch_dual())
        self.fileOne_Entry.bind(right_click_button, lambda e:self.input_dual_right_click_menu(e, is_primary=True))
        self.fileTwo_Entry.bind(right_click_button, lambda e:self.input_dual_right_click_menu(e, is_primary=False))
        if not is_macos:
            self.bind("<Configure>", self.adjust_toplevel_positions)
        
    def auto_save(self):
        return self.settings_manager.auto_save()

    #--Input/Export Methods--
    
    def linux_filebox_fix(self, is_on=True):
        fg_color_set = '#575757' if is_on else "#F6F6F7"
        style = ttk.Style(self)
        style.configure('TButton', foreground='#F6F6F7')
        style.configure('TCheckbutton', foreground='#F6F6F7')
        style.configure('TCombobox', foreground='#F6F6F7')
        style.configure('TEntry', foreground='#F6F6F7')
        style.configure('TLabel', foreground='#F6F6F7')
        style.configure('TMenubutton', foreground='#F6F6F7')
        style.configure('TRadiobutton', foreground='#F6F6F7')
        gui_data.sv_ttk.set_theme("dark", MAIN_FONT_NAME, 10, fg_color_set=fg_color_set)

    def show_file_dialog(self, text='Select Audio files', dialoge_type=None, parent_win=None):
        if parent_win is None:
            parent_win = root
        
        initial_dir = self.lastDir if (self.lastDir and os.path.isdir(self.lastDir)) else None

        if dialoge_type in [MULTIPLE_FILE, MAIN_MULTIPLE_FILE]:
            filenames = ask_open_filenames(title=text, initial_dir=initial_dir, parent=parent_win)
        elif dialoge_type == SINGLE_FILE:
            filenames = ask_open_filename(title=text, initial_dir=initial_dir, parent=parent_win)
        elif dialoge_type == CHOOSE_EXPORT_FIR:
            filenames = ask_directory(title='Select Folder', initial_dir=initial_dir, parent=parent_win)
        else:
            filenames = ask_open_filenames(title=text, initial_dir=initial_dir, parent=parent_win)
            
        if filenames:
            if isinstance(filenames, (list, tuple)):
                if len(filenames) > 0 and filenames[0]:
                    self.lastDir = os.path.dirname(filenames[0])
            elif isinstance(filenames, str) and filenames:
                if dialoge_type == CHOOSE_EXPORT_FIR:
                    self.lastDir = filenames
                else:
                    self.lastDir = os.path.dirname(filenames)
            self.auto_save()
            
        return filenames

    def input_select_filedialog(self, parent_win=None, is_append=False):
        """Make user select music files"""

        if self.lastDir is not None:
            if not os.path.isdir(self.lastDir):
                self.lastDir = None

        paths = self.show_file_dialog(dialoge_type=MAIN_MULTIPLE_FILE, parent_win=parent_win)

        if paths:  # Path selected
            if is_append:
                self.inputPaths = tuple(list(self.inputPaths) + list(paths))
            else:
                self.inputPaths = paths
            
            self.process_input_selections()
            self.update_inputPaths()

    def export_select_filedialog(self):
        """Make user select a folder to export the converted files in"""

        export_path = None
        
        path = self.show_file_dialog(dialoge_type=CHOOSE_EXPORT_FIR)

        if path:  # Path selected
            self.export_path_var.set(path)
            export_path = self.export_path_var.get()
            
        return export_path
     
    def update_inputPaths(self):
        """Update the music file entry"""
        
        if self.inputPaths:
            if len(self.inputPaths) == 1:
                text = self.inputPaths[0]
            else:
                count = len(self.inputPaths) - 1
                file_text = 'file' if len(self.inputPaths) == 2 else 'files'
                text = f"{self.inputPaths[0]}, +{count} {file_text}"
        else:
            # Empty Selection
            text = ''
            
        self.inputPathsEntry_var.set(text)

    def select_audiofile(self, path=None, is_primary=True): 
        """Make user select music files"""
            
        vars = {
            True: (self.fileOneEntry_Full_var, self.fileOneEntry_var, self.fileTwoEntry_Full_var, self.fileTwoEntry_var),
            False: (self.fileTwoEntry_Full_var, self.fileTwoEntry_var, self.fileOneEntry_Full_var, self.fileOneEntry_var)
        }

        file_path_var, file_basename_var, file_path_2_var, file_basename_2_var = vars[is_primary]
            
        if not path:
            path = self.show_file_dialog(text='Select Audio file', dialoge_type=SINGLE_FILE)

        if path:  # Path selected
            file_path_var.set(path)
            file_basename_var.set(os.path.basename(path))
            
            if BATCH_MODE_DUAL in file_path_2_var.get():
                file_path_2_var.set("")
                file_basename_2_var.set("")

            self.DualBatch_inputPaths = []
            self.check_dual_paths()
            
    #--Utility Methods--

    def restart(self):
        """Restart the application after asking for confirmation"""
        
        confirm = messagebox.askyesno(parent=root,
                                         title=CONFIRM_RESTART_TEXT[0],
                                         message=CONFIRM_RESTART_TEXT[1])
        
        if confirm:
            self.save_values(app_close=True, is_restart=True)
        
    def delete_temps(self, is_start_up=False):  
        """Deletes temp files"""
        
        DIRECTORIES = (BASE_PATH, VR_MODELS_DIR, MDX_MODELS_DIR, DEMUCS_MODELS_DIR, DEMUCS_NEWER_REPO_DIR)
        EXTENSIONS = (('.aes', '.txt', '.tmp'))
        
        try:
            if os.path.isfile(f"{current_patch}{application_extension}"):
                os.remove(f"{current_patch}{application_extension}")
            
            if not is_start_up:
                if os.path.isfile(SPLASH_DOC):
                    os.remove(SPLASH_DOC)
            
            EXCLUDE_FILES = ('requirements.txt', 'demucs_models.txt', 'error-log.txt')
            for dir in DIRECTORIES:
                for temp_file in os.listdir(dir):
                    if temp_file in EXCLUDE_FILES:
                        continue
                    if temp_file.endswith(EXTENSIONS):
                        if os.path.isfile(os.path.join(dir, temp_file)):
                            os.remove(os.path.join(dir, temp_file))
        except Exception as e:
            self.error_log_var.set(error_text(TEMP_FILE_DELETION_TEXT, e))
        
    def get_files_from_dir(self, directory, ext, is_mdxnet=False):
        """Gets files from specified directory that ends with specified extention"""
        if not os.path.isdir(directory):
            return ()
        return tuple(
            x if is_mdxnet and (x.endswith(CKPT) or x.endswith('.safetensors') or x.endswith('.pth')) else os.path.splitext(x)[0]
            for x in os.listdir(directory)
            if x.endswith(ext)
        )
        
    def return_ensemble_stems(self, is_primary=False): 
        """Grabs and returns the chosen ensemble stems."""
        
        ensemble_stem = self.ensemble_main_stem_var.get().partition("/")
        
        if is_primary:
            return ensemble_stem[0]
        else:
            return ensemble_stem[0], ensemble_stem[2]

    def message_box(self, message):
        """Template for confirmation box"""
        
        confirm = messagebox.askyesno(title=message[0],
                                         message=message[1],
                                         parent=root)
        
        return confirm

    def error_dialoge(self, message):
        """Template for messagebox that informs user of error"""

        messagebox.showerror(master=self,
                                  title=message[0],
                                  message=message[1],
                                  parent=root) 
      
    def model_list(self, primary_stem: str, secondary_stem: str, is_4_stem_check=False, is_multi_stem=False, is_dry_check=False, is_no_demucs=False, is_check_vocal_split=False):
        
        stem_check = self.assemble_model_data(arch_type=ENSEMBLE_STEM_CHECK, is_dry_check=is_dry_check)
        
        def matches_stem(model: ModelData):
            primary_match = model.primary_stem in {primary_stem, secondary_stem}
            mdx_stem_match = primary_stem in model.mdx_model_stems and model.mdx_stem_count <= 2
            return primary_match or mdx_stem_match if is_no_demucs else primary_match or primary_stem in model.mdx_model_stems

        result = []

        for model in stem_check:
            if is_multi_stem:
                result.append(model.model_and_process_tag)
            elif is_4_stem_check and (model.demucs_stem_count == 4 or model.mdx_stem_count == 4):
                result.append(model.model_and_process_tag)
            elif matches_stem(model) or (not is_no_demucs and primary_stem.lower() in model.demucs_source_list):
                if is_check_vocal_split:
                    model_name = None if model.is_karaoke or not model.vocal_split_model else model.model_basename
                else: 
                    model_name = model.model_and_process_tag
                    
                result.append(model_name)

        return result

    def help_hints(self, widget, text):
        toolTip = ToolTip(widget)
        def enter(event):
            if self.help_hints_var.get():
                toolTip.showtip(text)
        def leave(event):
            toolTip.hidetip()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
        widget.bind(right_click_button, lambda e:copy_help_hint(e))

        def copy_help_hint(event):
            if self.help_hints_var.get():
                right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
                right_click_menu.add_command(label='Copy Help Hint Text', command=right_click_menu_copy_hint)
                
                try:
                    right_click_menu.tk_popup(event.x_root,event.y_root)
                    right_click_release_linux(right_click_menu)
                finally:
                    right_click_menu.grab_release()
            else:
                if widget.winfo_toplevel() == root:
                    self.right_click_menu_popup(event, main_menu=True)

        def right_click_menu_copy_hint():
            pyperclip.copy(text)

    def check_is_menu_open(self, menu):
        try:
            menu_mapping = {
                VR_OPTION: (self.is_open_menu_advanced_vr_options, self.menu_advanced_vr_options, self.menu_advanced_vr_options_close_window),
                DEMUCS_OPTION: (self.is_open_menu_advanced_demucs_options, self.menu_advanced_demucs_options, self.menu_advanced_demucs_options_close_window),
                MDX_OPTION: (self.is_open_menu_advanced_mdx_options, self.menu_advanced_mdx_options, self.menu_advanced_mdx_options_close_window),
                ENSEMBLE_OPTION: (self.is_open_menu_advanced_ensemble_options, self.menu_advanced_ensemble_options, self.menu_advanced_ensemble_options_close_window),
                HELP_OPTION: (self.is_open_menu_help, self.menu_help, self.menu_help_close_window),
                ERROR_OPTION: (self.is_open_menu_error_log, self.menu_error_log, self.menu_error_log_close_window),
                INPUTS_MENU: (self.is_open_menu_view_inputs, self.menu_view_inputs, self.menu_view_inputs_close_window),
                ALIGNMENT_TOOL: (self.is_open_menu_advanced_align_options, self.menu_advanced_align_options, self.menu_advanced_align_options_close_window)
            }

            is_open, open_method, close_method = menu_mapping.get(menu, (None, None, None))
            if is_open and is_open.get():
                close_method()
            open_method()
        except Exception as e:
            self.error_log_var.set(f"{error_text(menu, e)}")

    def input_right_click_menu(self, event):

        right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
        right_click_menu.add_command(label='See All Inputs', command=lambda:self.check_is_menu_open(INPUTS_MENU))
        
        try:
            right_click_menu.tk_popup(event.x_root,event.y_root)
            right_click_release_linux(right_click_menu)
        finally:
            right_click_menu.grab_release()

    def input_dual_right_click_menu(self, event, is_primary:bool):
        input_path = self.fileOneEntry_Full_var.get() if is_primary else self.fileTwoEntry_Full_var.get()
        right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
        right_click_menu.add_command(label=CHOOSE_INPUT_TEXT, command=lambda:self.select_audiofile(is_primary=is_primary))
        if input_path and os.path.isdir(os.path.dirname(input_path)):
            right_click_menu.add_command(label=OPEN_INPUT_DIR_TEXT, command=lambda:OPEN_FILE_func(os.path.dirname(input_path)))
        right_click_menu.add_command(label=BATCH_PROCESS_MENU_TEXT, command=self.menu_batch_dual)
        
        try:
            right_click_menu.tk_popup(event.x_root,event.y_root)
            right_click_release_linux(right_click_menu)
        finally:
            right_click_menu.grab_release()

    def cached_sources_clear(self):

        self.vr_cache_source_mapper = {}
        self.mdx_cache_source_mapper = {}
        self.demucs_cache_source_mapper = {}

    def cached_source_callback(self, process_method, model_name=None):
        
        model, sources = None, None
        
        if process_method == VR_ARCH_TYPE:
            mapper = self.vr_cache_source_mapper
        if process_method == MDX_ARCH_TYPE:
            mapper = self.mdx_cache_source_mapper
        if process_method == DEMUCS_ARCH_TYPE:
            mapper = self.demucs_cache_source_mapper
        
        for key, value in mapper.items():
            if model_name in key:
                model = key
                sources = value
        
        return model, sources

    def cached_model_source_holder(self, process_method, sources, model_name=None):
        
        if process_method == VR_ARCH_TYPE:
            self.vr_cache_source_mapper = {**self.vr_cache_source_mapper, **{model_name: sources}}
        if process_method == MDX_ARCH_TYPE:
            self.mdx_cache_source_mapper = {**self.mdx_cache_source_mapper, **{model_name: sources}}
        if process_method == DEMUCS_ARCH_TYPE:
            self.demucs_cache_source_mapper = {**self.demucs_cache_source_mapper, **{model_name: sources}}
  
    def cached_source_model_list_check(self, model_list: list[ModelData]):

        model: ModelData
        primary_model_names = lambda process_method:[model.model_basename if model.process_method == process_method else None for model in model_list]
        secondary_model_names = lambda process_method:[model.secondary_model.model_basename if model.is_secondary_model_activated and model.process_method == process_method else None for model in model_list]

        self.vr_primary_model_names = primary_model_names(VR_ARCH_TYPE)
        self.mdx_primary_model_names = primary_model_names(MDX_ARCH_TYPE)
        self.demucs_primary_model_names = primary_model_names(DEMUCS_ARCH_TYPE)
        self.vr_secondary_model_names = secondary_model_names(VR_ARCH_TYPE)
        self.mdx_secondary_model_names = secondary_model_names(MDX_ARCH_TYPE)
        self.demucs_secondary_model_names = [model.secondary_model.model_basename if model.is_secondary_model_activated and model.process_method == DEMUCS_ARCH_TYPE and model.secondary_model is not None else None for model in model_list]
        self.demucs_pre_proc_model_name = [model.pre_proc_model.model_basename if model.pre_proc_model else None for model in model_list]#list(dict.fromkeys())
        
        for model in model_list:
            if model.process_method == DEMUCS_ARCH_TYPE and model.is_demucs_4_stem_secondaries:
                if not model.is_4_stem_ensemble:
                    self.demucs_secondary_model_names = model.secondary_model_4_stem_model_names_list
                    break
                else:
                    for i in model.secondary_model_4_stem_model_names_list:
                        self.demucs_secondary_model_names.append(i)
        
        self.all_models = self.vr_primary_model_names + self.mdx_primary_model_names + self.demucs_primary_model_names + self.vr_secondary_model_names + self.mdx_secondary_model_names + self.demucs_secondary_model_names + self.demucs_pre_proc_model_name
      
    def verify_audio(self, audio_file, is_process=True, sample_path=None):
        is_good = False
        error_data = ''
        
        if type(audio_file) is not tuple:
            audio_file = [audio_file]

        for i in audio_file:
            if os.path.isfile(i):
                try:
                    librosa.load(i, duration=3, mono=False, sr=44100) if type(sample_path) is not str else self.create_sample(i, sample_path)
                    is_good = True
                except Exception as e:
                    error_name = f'{type(e).__name__}'
                    traceback_text = ''.join(traceback.format_tb(e.__traceback__))
                    message = f'{error_name}: "{e}"\n{traceback_text}"'
                    if is_process:
                        audio_base_name = os.path.basename(i)
                        self.error_log_var.set(f'{ERROR_LOADING_FILE_TEXT[0]}:\n\n\"{audio_base_name}\"\n\n{ERROR_LOADING_FILE_TEXT[1]}:\n\n{message}')
                    else:
                        error_data = AUDIO_VERIFICATION_CHECK(i, message)

        if is_process:
            return is_good
        else:
            return is_good, error_data
      
    def create_sample(self, audio_file, sample_path=SAMPLE_CLIP_PATH):
        try:
            with audioread.audio_open(audio_file) as f:
                track_length = int(f.duration)
        except Exception as e:
            print('Audioread failed to get duration. Trying Librosa...')
            y, sr = librosa.load(audio_file, mono=False, sr=44100)
            track_length = int(librosa.get_duration(y=y, sr=sr))
        
        clip_duration = int(self.model_sample_mode_duration_var.get())
        
        if track_length >= clip_duration:
            offset_cut = track_length//3
            off_cut = offset_cut + track_length
            if not off_cut >= clip_duration:
                offset_cut = 0
            name_apped = f'{clip_duration}_second_'
        else:
            offset_cut, clip_duration = 0, track_length
            name_apped = ''

        sample = librosa.load(audio_file, offset=offset_cut, duration=clip_duration, mono=False, sr=44100)[0].T
        audio_sample = os.path.join(sample_path, f'{os.path.splitext(os.path.basename(audio_file))[0]}_{name_apped}sample.wav')
        sf.write(audio_sample, sample, 44100)
        
        return audio_sample

    #--Right Click Menu Pop-Ups--

    def right_click_select_settings_sub(self, parent_menu, process_method):
        return self.right_click_handler.right_click_select_settings_sub(parent_menu, process_method)

    def right_click_menu_popup(self, event, text_box=False, main_menu=False):
        return self.right_click_handler.right_click_menu_popup(event, text_box=text_box, main_menu=main_menu)

    def right_click_menu_copy(self):
        return self.right_click_handler.right_click_menu_copy()

    def right_click_menu_paste(self, text_box=False):
        return self.right_click_handler.right_click_menu_paste(text_box=text_box)

    def right_click_menu_delete(self, text_box=False):
        return self.right_click_handler.right_click_menu_delete(text_box=text_box)

    def right_click_console(self, event):
        return self.right_click_handler.right_click_console(event)

    #--Secondary Window Methods--

    def vocal_splitter_Button_opt(self, top_window, frame, pady, width=15):
        vocal_splitter_Button = ttk.Button(frame, text=VOCAL_SPLITTER_OPTIONS_TEXT, command=lambda:self.pop_up_set_vocal_splitter(top_window), width=width)#
        vocal_splitter_Button.grid(pady=pady)

    def adjust_toplevel_positions(self, event):
        # Copy the list to avoid modifying while iterating
        for toplevel in self.toplevels.copy():
            # Check if the toplevel window is still alive
            if not toplevel.winfo_exists():
                self.toplevels.remove(toplevel)
            else:
                menu_offset_x = (root.winfo_width() - toplevel.winfo_width()) // 2
                menu_offset_y = (root.winfo_height() - toplevel.winfo_height()) // 2
                toplevel.geometry(f"+{root.winfo_x() + menu_offset_x}+{root.winfo_y() + menu_offset_y}")

    def menu_placement(self, window: tk.Toplevel, title, pop_up=False, is_help_hints=False, close_function=None, frame_list=None, top_window=None):
        """Prepares and centers each secondary window relative to the main window"""
        
        top_window = top_window if top_window else root
        window.withdraw()
        window.resizable(False, False)
        window.wm_transient(top_window)
        window.title(title)
        window.iconbitmap(ICON_IMG_PATH) if is_windows else self.tk.call('wm', 'iconphoto', window._w, tk.PhotoImage(file=MAIN_ICON_IMG_PATH))
        
        root_location_x = root.winfo_x()
        root_location_y = root.winfo_y()
        root_x = root.winfo_width() 
        root_y = root.winfo_height()
        window.update() if is_windows else window.update_idletasks()
        sub_menu_x = window.winfo_reqwidth() 
        sub_menu_y = window.winfo_reqheight()
        menu_offset_x = (root_x - sub_menu_x) // 2
        menu_offset_y = (root_y - sub_menu_y) // 2
        window.geometry(f"+{root_location_x + menu_offset_x}+{root_location_y + menu_offset_y}")
        
        window.deiconify()
        window.configure(bg=BG_COLOR)

        if not is_macos:
            self.toplevels.append(window)
        
        def right_click_menu(event):
            help_hints_label = 'Enable' if not self.help_hints_var.get() else 'Disable'
            help_hints_bool = not self.help_hints_var.get()
            right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
            if is_help_hints:
                right_click_menu.add_command(label=f'{help_hints_label} Help Hints', command=lambda:self.help_hints_var.set(help_hints_bool))
            right_click_menu.add_command(label='Exit Window', command=close_function)
            
            try:
                right_click_menu.tk_popup(event.x_root,event.y_root)
                right_click_release_linux(right_click_menu, window)
            finally:
                right_click_menu.grab_release()
        
        if close_function:
            window.bind(right_click_button, lambda e:right_click_menu(e))

        if frame_list:
            for frame in frame_list:
                #self.adjust_widget_widths(frame)
                self.focus_out_widgets(frame.winfo_children() + [frame], frame)
 
        if pop_up:
            window.attributes('-topmost', 'true') if OPERATING_SYSTEM == "Linux" else None
            window.grab_set()
            root.wait_window(window)
            
    def adjust_widget_widths(self, frame):

        def resize_widget(widgets):
            max_width = max(wid.winfo_width() for wid in widgets)
            for wid in widgets:
                if isinstance(wid, (tk.Button, ttk.Combobox)):
                    # For widgets where width represents characters, not pixels
                    wid.configure(width=int(max_width / wid.winfo_pixels('1c')))
                else:
                    # For widgets where width represents pixels
                    wid.configure(width=max_width)

        resize_widget([widget for widget in frame.winfo_children() if isinstance(widget, tk.Button)])
        resize_widget([widget for widget in frame.winfo_children() if isinstance(widget, ttk.Combobox)])

    def menu_move_tab(notebook: ttk.Notebook, tab_text, new_position):
        # Get the tab ID
        tab_id = None
        for tab in notebook.tabs():
            if notebook.tab(tab, "text") == tab_text:
                tab_id = tab
                break

        if tab_id is None:
            print(f"No tab named '{tab_text}'")
            return

        # remove the tab
        notebook.forget(tab_id)
        
        # add it back in new position
        notebook.insert(new_position, tab_id)
          
    def menu_tab_control(self, toplevel, ai_network_vars, is_demucs=False, is_mdxnet=False):
        """Prepares the tabs setup for some windows"""

        tabControl = ttk.Notebook(toplevel)

        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)

        tabControl.add(tab1, text=SETTINGS_GUIDE_TEXT)
        tabControl.add(tab2, text=SECONDARY_MODEL_TEXT)

        tab1.grid_rowconfigure(0, weight=1)
        tab1.grid_columnconfigure(0, weight=1)

        tab2.grid_rowconfigure(0, weight=1)
        tab2.grid_columnconfigure(0, weight=1)

        if is_demucs or is_mdxnet:
            tab3 = ttk.Frame(tabControl)
            tabControl.add(tab3, text=PREPROCESS_MODEL_CHOOSE_TEXT if is_demucs else MDX23C_ONLY_OPTIONS_TEXT)
            tab3.grid_rowconfigure(0, weight=1)
            tab3.grid_columnconfigure(0, weight=1)

        tabControl.pack(expand=1, fill=tk.BOTH)
        
        self.tab2_loaded = False
        self.tab3_loaded = False

        def on_tab_selected(event):
            # Check if it's tab2 (by tab id or tab title) and if it hasn't been loaded before
            load_screen = False
            if event.widget.tab('current', option='text') == 'Secondary Model' and not self.tab2_loaded:
                tab = tab2
                self.tab2_loaded = True
                tab_load = lambda:self.menu_secondary_model(tab, ai_network_vars)
                load_screen = True
            elif event.widget.tab('current', option='text') == PREPROCESS_MODEL_CHOOSE_TEXT and not self.tab3_loaded:
                tab = tab3
                self.tab3_loaded = True
                tab_load = lambda:self.menu_preproc_model(tab)
                load_screen = True
                
            if load_screen:
                # Step 1: Add "Loading..." label
                loading_label = ttk.Label(tab, text="Updating model lists...", font=Font(family=MAIN_FONT_NAME, size=14))
                loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # Assuming you want to center it
                
                # Step 2: Update the UI to show the label
                tab.update_idletasks()

                # Load the content
                tab_load()
                
                # Step 3: Remove or update the "Loading..." label
                loading_label.destroy()  # Remove the label. Or you can update its text if desired.
                
            #self.on_tab_changed(tabControl)

        tabControl.bind("<<NotebookTabChanged>>", on_tab_selected)

        if is_demucs or is_mdxnet:
            return tab1, tab3
        else:
            return tab1

    def menu_view_inputs(self):
        """Open the Selected Inputs window."""
        open_view_inputs(
            self,
            right_click_button=right_click_button,
            right_click_release_linux=right_click_release_linux,
            open_file_func=OPEN_FILE_func,
            drop_func=drop,
            is_dnd_compatible=is_dnd_compatible,
        )

    def menu_batch_dual(self):
        """Open Dual Audio Batch Processing dialog."""
        open_batch_dual(
            self,
            right_click_button=right_click_button,
            right_click_release_linux=right_click_release_linux,
            open_file_func=OPEN_FILE_func,
            drop_func=drop,
        )

    def check_dual_paths(self, is_fill_menu=False):
        """Validate and update dual batch input paths state."""
        return _check_dual_paths(self, is_fill_menu=is_fill_menu)

    def fill_gpu_list(self):
        try:
            if cuda_available:
                self.cuda_device_list = [f"{torch.cuda.get_device_properties(i).name}:{i}" for i in range(torch.cuda.device_count())]
                self.cuda_device_list.insert(0, DEFAULT)
                #print(self.cuda_device_list)
            
        except Exception as e:
            print(e)
            
        check_gpu_list = self.cuda_device_list
        if self.device_set_var.get() not in check_gpu_list:
            self.device_set_var.set(DEFAULT)

    def loop_gpu_list(self, option_menu:ComboBoxMenu, menu_name, option_list):
        option_menu['values'] = option_list
        option_menu.update_dropdown_size(option_list, menu_name)

    def menu_settings(self, select_tab_2=False, select_tab_3=False):
        return open_settings_menu(self, select_tab_2=select_tab_2, select_tab_3=select_tab_3)

    def menu_advanced_vr_options(self):
        return open_advanced_vr_options(self)

    def menu_advanced_demucs_options(self):
        return open_advanced_demucs_options(self)

    def menu_advanced_mdx_options(self):
        return open_advanced_mdx_options(self)

    def menu_advanced_ensemble_options(self):
        return open_advanced_ensemble_options(self)

    def menu_advanced_align_options(self):
        return open_advanced_align_options(self)
 
    def menu_help(self):  # **
        """Open Help Guide."""
        open_help_menu(
            self,
            right_click_button=right_click_button,
            right_click_release_linux=right_click_release_linux,
            is_macos=is_macos,
            current_patch=current_patch,
            auto_hyperlink=auto_hyperlink,
        )

    def menu_error_log(self):
        """Open Error Log."""
        open_error_log(self, right_click_button=right_click_button)

    def menu_secondary_model(self, tab, ai_network_vars: dict):
        """Build Secondary Model tab widgets."""
        build_secondary_model_tab(self, tab, ai_network_vars)

    def menu_preproc_model(self, tab):
        """Build Pre-process Model tab widgets."""
        build_preproc_model_tab(self, tab)

    def menu_manual_downloads(self):
        """Open Manual Downloads dialog."""
        open_manual_downloads(self, OPEN_FILE_func)

    def invalid_tooltip(self, widget, pattern=None):
        tooltip = ToolTip(widget)
        invalid_message = lambda:tooltip.showtip(INVALID_INPUT_E, True)
        
        def invalid_message_():
            tooltip.showtip(INVALID_INPUT_E, True)
        
        def validation(value):
            if re.fullmatch(modified_pattern, value) is None:
                return False
            else:
                return True
        
        if not pattern:
            pattern = r'^[a-zA-Z0-9 -]{0,25}$'

        modified_pattern = f"({pattern}|)"

        widget.configure(
            validate='key', 
            validatecommand=(self.register(validation), '%P'),
            invalidcommand=(self.register(invalid_message))
        )
        
        return invalid_message_
        
    def pop_up_save_current_settings(self):
        return self.settings_manager.pop_up_save_current_settings()

    def pop_up_save_current_settings_sub_json_dump(self, settings_save_name: str):
        return self.settings_manager.pop_up_save_current_settings_sub_json_dump(settings_save_name)

    def pop_up_update_confirmation(self):
        """Ask user if they want to update."""
        return self.download_manager.pop_up_update_confirmation()

    def pop_up_user_code_input(self):
        """Input VIP Code dialog."""
        return self.download_manager.pop_up_user_code_input()

    # --Model Parameter and Ensemble Dialog Delegates--

    def pop_up_change_model_defaults(self, top_window):
        return pop_up_change_model_defaults(self, top_window)

    def pop_up_set_vocal_splitter(self, top_window):
        return pop_up_set_vocal_splitter(self, top_window)

    def pop_up_mdx_model(self, mdx_model_hash, model_path):
        return pop_up_mdx_model(self, mdx_model_hash, model_path)

    def pop_up_mdx_model_sub_json_dump(self, mdx_model_params, mdx_model_hash):
        return pop_up_mdx_model_sub_json_dump(self, mdx_model_params, mdx_model_hash)

    def pop_up_mdx_c_param(self, mdx_model_hash):
        return pop_up_mdx_c_param(self, mdx_model_hash)

    def pop_up_vr_param(self, vr_model_hash):
        return pop_up_vr_param(self, vr_model_hash)

    def pop_up_vr_param_sub_json_dump(self, vr_model_params, vr_model_hash):
        return pop_up_vr_param_sub_json_dump(self, vr_model_params, vr_model_hash)

    def pop_up_input_stem_name(self, stem_var, parent_window):
        return pop_up_input_stem_name(self, stem_var, parent_window)

    def pop_up_save_ensemble(self):
        return pop_up_save_ensemble(self)

    def pop_up_save_ensemble_sub_json_dump(self, selected_ensemble_model, ensemble_save_name: str):
        return pop_up_save_ensemble_sub_json_dump(self, selected_ensemble_model, ensemble_save_name)

    def open_ensemble_model_settings(self, event=None):
        return open_ensemble_model_settings(self, event)

    def pop_up_ensemble_model_settings(self, models_info):
        return pop_up_ensemble_model_settings(self, models_info)

    # --Download & Model Management Delegates--

    def deletion_list_fill(self, option_menu: ComboBoxMenu, selection_var: tk.StringVar, selection_dir, var_set, menu_name=None):
        return self.download_manager.deletion_list_fill(option_menu, selection_var, selection_dir, var_set, menu_name)

    def deletion_entry(self, selection: str, path, callback):
        return self.download_manager.deletion_entry(selection, path, callback)

    def update_delete_model_list(self, remove=None):
        return self.download_manager.update_delete_model_list(remove)

    def delete_model_command(self, selection):
        return self.download_manager.delete_model_command(selection)

    def _inject_community_name_mappings(self):
        return self.download_manager._inject_community_name_mappings()

    def offline_state_set(self, is_start_up=False):
        return self.download_manager.offline_state_set(is_start_up)

    def online_data_refresh(self, user_refresh=True, confirmation_box=False, refresh_list_Button=False, is_start_up=False, is_download_complete=False):
        return self.download_manager.online_data_refresh(user_refresh, confirmation_box, refresh_list_Button, is_start_up, is_download_complete)

    def download_validate_code(self, confirm=False, code_message=None):
        return self.download_manager.download_validate_code(confirm, code_message)

    def download_list_fill(self, model_type=ALL_TYPES):
        return self.download_manager.download_list_fill(model_type)

    def download_model_settings(self):
        return self.download_manager.download_model_settings()

    def download_list_state(self, reset=True, disable_only=False):
        return self.download_manager.download_list_state(reset, disable_only)

    def download_model_select(self, selection, type, var: tk.StringVar):
        return self.download_manager.download_model_select(selection, type, var)

    def download_item(self, is_update_app=False):
        return self.download_manager.download_item(is_update_app)

    def download_post_action(self, action):
        return self.download_manager.download_post_action(action)

    #--Refresh/Loop Methods--    

    def update_loop(self):
        """Update the model dropdown menus"""

        if self.clear_cache_torch:
            clear_gpu_cache()
            self.clear_cache_torch = False

        if self.is_process_stopped:
            if self.thread_check(self.active_processing_thread):
                self.conversion_Button_Text_var.set(STOP_PROCESSING)
                self.conversion_Button.configure(state=tk.DISABLED)
                self.stop_Button.configure(state=tk.DISABLED)
            else:
                self.stop_Button.configure(state=tk.NORMAL)
                self.conversion_Button_Text_var.set(START_PROCESSING)
                self.conversion_Button.configure(state=tk.NORMAL)
                self.progress_bar_main_var.set(0)
                clear_gpu_cache()
                self.is_process_stopped = False
            
        if self.is_confirm_error_var.get():
            self.check_is_menu_open(ERROR_OPTION)
            self.is_confirm_error_var.set(False)

        if self.is_check_splash and is_windows:
            
            while not self.msg_queue.empty():
                message = self.msg_queue.get_nowait()
                print(message)
            
            close_process(self.msg_queue)
            self.is_check_splash = False

        #self.auto_save()

        self.update_available_models()
        self.after(600, self.update_loop)
          
    def update_menus(self, option_widget:ComboBoxMenu, style_name, command, new_items, last_items=None, base_options=None):
                
        if new_items != last_items:
            formatted_items = [item.replace("_", " ") for item in new_items]
            if not formatted_items and base_options:
                base_options = [option for option in base_options if option != OPT_SEPARATOR_SAVE]
            
            final_options = formatted_items + base_options if base_options else formatted_items
            option_widget['values'] = final_options
            option_widget.update_dropdown_size(formatted_items, style_name, command=command)
            return new_items
        return last_items
          
    def update_available_models(self):
        """
        Loops through all models in each model directory and adds them to the appropriate model menu.
        Also updates ensemble listbox and user saved settings list.
        """
        
        def fix_name(name, mapper:dict): return next((new_name for old_name, new_name in mapper.items() if name == old_name), name)
        
        new_vr_models = self.get_files_from_dir(VR_MODELS_DIR, PTH)
        new_mdx_models = self.get_files_from_dir(MDX_MODELS_DIR, (ONNX, CKPT, '.safetensors', '.pth'), is_mdxnet=True)
        
        # Collect and filter Deverb models
        self.vocal_deverb_models_list = [NO_MODEL]
        if 'UVR-DeEcho-DeReverb' in new_vr_models:
            self.vocal_deverb_models_list.append('UVR-DeEcho-DeReverb')
            
        mdx_deverb_models = []
        for m in new_mdx_models:
            fixed = fix_name(m, self.mdx_name_select_MAPPER)
            if 'deverb' in fixed.lower() or 'dereverb' in fixed.lower():
                mdx_deverb_models.append(m)
                self.vocal_deverb_models_list.append(fixed)
                

        new_demucs_models = self.get_files_from_dir(DEMUCS_MODELS_DIR, (CKPT, '.gz', '.th')) + self.get_files_from_dir(DEMUCS_NEWER_REPO_DIR, YAML)
        new_ensembles_found = self.get_files_from_dir(ENSEMBLE_CACHE_DIR, JSON)
        new_settings_found = self.get_files_from_dir(SETTINGS_CACHE_DIR, JSON)
        new_models_found = new_vr_models + new_mdx_models + new_demucs_models
        is_online = self.is_online_model_menu
        
        def loop_directories(option_menu:ComboBoxMenu, option_var, model_list, model_type, name_mapper=None):
            current_selection = option_menu.get()
            option_list = [fix_name(file_name, name_mapper) for file_name in model_list] if name_mapper else model_list
            sorted_options = natsort.natsorted(option_list)
            option_list_option_menu = sorted_options + [OPT_SEPARATOR, DOWNLOAD_MORE] if self.is_online else sorted_options
            
            if not option_list and self.is_online:
                option_list_option_menu = [option for option in option_list_option_menu if option != OPT_SEPARATOR]
            
            option_menu['values'] = option_list_option_menu
            option_menu.set(current_selection)
            option_menu.update_dropdown_size(option_list, model_type)
            
            if self.is_root_defined_var.get() and model_type == MDX_ARCH_TYPE and self.chosen_process_method_var.get() == MDX_ARCH_TYPE:
                self.selection_action_models_sub(current_selection, model_type, option_var)
                
            return tuple(f"{model_type}{ENSEMBLE_PARTITION}{model_name}" for model_name in sorted_options)

        if new_models_found != self.last_found_models or is_online != self.is_online:
            self.model_data_table = []
            
            vr_model_list = loop_directories(self.vr_model_Option, self.vr_model_var, new_vr_models, VR_ARCH_TYPE, name_mapper=None)
            mdx_model_list = loop_directories(self.mdx_net_model_Option, self.mdx_net_model_var, new_mdx_models, MDX_ARCH_TYPE, name_mapper=self.mdx_name_select_MAPPER)
            demucs_model_list = loop_directories(self.demucs_model_Option, self.demucs_model_var, new_demucs_models, DEMUCS_ARCH_TYPE, name_mapper=self.demucs_name_select_MAPPER)
            
            self.ensemble_model_list = vr_model_list + mdx_model_list + demucs_model_list
            self.default_change_model_list = vr_model_list + mdx_model_list
            self.last_found_models = new_models_found
            self.is_online_model_menu = self.is_online
            
            if not self.chosen_ensemble_var.get() == CHOOSE_ENSEMBLE_OPTION:
                self.selection_action_chosen_ensemble(self.chosen_ensemble_var.get())
            else:
                if not self.ensemble_main_stem_var.get() == CHOOSE_STEM_PAIR:
                    self.selection_action_ensemble_stems(self.ensemble_main_stem_var.get(), auto_update=self.ensemble_listbox_get_all_selected_models())
                else:
                    self.ensemble_listbox_clear_and_insert_new(self.ensemble_model_list)

        self.last_found_ensembles = self.update_menus(option_widget=self.chosen_ensemble_Option, 
                                                      style_name='savedensembles',
                                                      command=None, 
                                                      new_items=new_ensembles_found, 
                                                      last_items=self.last_found_ensembles, 
                                                      base_options=ENSEMBLE_OPTIONS
        )

        self.last_found_settings = self.update_menus(option_widget=self.save_current_settings_Option, 
                                                      style_name='savedsettings',
                                                      command=None, 
                                                      new_items=new_settings_found, 
                                                      last_items=self.last_found_settings, 
                                                      base_options=SAVE_SET_OPTIONS
        )

    def update_main_widget_states_mdx(self):
        return self.mdx_panel.update_main_widget_states_mdx()

    def move_widget_offscreen(self, widget, step=10):
        current_x = widget.winfo_x()
        current_y = widget.winfo_y()
        if current_x > -1000:
            widget.place(x=current_x - step, y=current_y)
            widget.after(10, lambda: self.move_widget_offscreen(widget, step))

    def update_main_widget_states(self):
        return self.options_coordinator.update_main_widget_states()

    def update_button_states(self):
        return self.demucs_panel.update_button_states()

    def update_button_states_mdx(self, model_stems):
        return self.mdx_panel.update_button_states_mdx(model_stems)

    def update_stem_checkbox_labels(self, selection, demucs=False, disable_boxes=False, is_disable_demucs_boxes=True):
        return self.options_coordinator.update_stem_checkbox_labels(
            selection, demucs=demucs, disable_boxes=disable_boxes, is_disable_demucs_boxes=is_disable_demucs_boxes
        )
     
    def update_ensemble_algorithm_menu(self, is_4_stem=False):
        options = ENSEMBLE_TYPE_4_STEM if is_4_stem else ENSEMBLE_TYPE

        if "/" not in self.ensemble_type_var.get() or is_4_stem: 
            self.ensemble_type_var.set(options[0])

        self.ensemble_type_Option["values"] = options

    def selection_action(self, event, option_var, is_mdx_net=False):
        selected_value = event.widget.get()
        selected_value = CHOOSE_MODEL if selected_value == OPT_SEPARATOR else selected_value
        option_var.set(selected_value)
        if is_mdx_net:
            self.update_main_widget_states_mdx()
        self.selection_action_models(selected_value)

    def selection_action_models(self, selection):
        """Accepts model names and verifies their state."""

        # Handle different selections.
        if selection in CHOOSE_MODEL:
            self.update_stem_checkbox_labels(PRIMARY_STEM, disable_boxes=True)
        else:
            self.is_stem_only_Options_Enable()

        # Process method matching current selection.
        self._handle_model_by_chosen_method(selection)

        # Handle Ensemble mode case.
        if self.chosen_process_method_var.get() == ENSEMBLE_MODE:
            return self._handle_ensemble_mode_selection(selection)

        if not self.is_menu_settings_open and selection == DOWNLOAD_MORE:
            self.update_checkbox_text()
            self.menu_settings(select_tab_3=True)

    def _handle_model_by_chosen_method(self, selection):
        """Handles model selection based on the currently chosen method."""
        current_method = self.chosen_process_method_var.get()
        model_var = self.method_mapper.get(current_method)
        if model_var:
            self.selection_action_models_sub(selection, current_method, model_var)

    def _handle_ensemble_mode_selection(self, selection):
        """Handles the case where the current method is 'ENSEMBLE_MODE'."""
        model_data = self.assemble_model_data(selection, ENSEMBLE_CHECK)[0]
        if not model_data.model_status:
            return self.model_stems_list.index(selection)
        return False

    def selection_action_models_sub(self, selection, ai_type, var: tk.StringVar):
        """Takes input directly from the selection_action_models parent function"""

        if ai_type == MDX_ARCH_TYPE:
            self.overlap_mdx_Option.place(x=-1000, y=-1000)
            self.overlap_mdx23_Option.place(x=-1000, y=-1000)
            self.mdxnet_stems_Option.place(x=-1000, y=-1000)
            self.mdxnet_stems_Label.place(x=-1000, y=-1000)
            self.mdx_segment_size_Option.place(x=-1000, y=-1000)
            self.mdx_segment_size_Label.place(x=-1000, y=-1000)

        if selection == DOWNLOAD_MORE:
            is_model_status = False
        else:
            model_data = self.assemble_model_data(selection, ai_type)[0]
            is_model_status = model_data.model_status

        if not is_model_status:
            var.set(CHOOSE_MODEL)
            if ai_type == MDX_ARCH_TYPE:
                self.mdx_segment_size_Label_place()
                self.mdx_segment_size_Option_place()
                self.overlap_mdx_Label_place()
                self.overlap_mdx_Option_place()
                self.update_stem_checkbox_labels(PRIMARY_STEM, disable_boxes=True)
        else:
            if ai_type == DEMUCS_ARCH_TYPE:
                if self.demucs_stems_var.get().lower() not in model_data.demucs_source_list:
                    self.demucs_stems_var.set(ALL_STEMS if model_data.demucs_stem_count == 4 else VOCAL_STEM)
                    
                self.update_button_states()
            else:
                if model_data.is_mdx_c and len(model_data.mdx_model_stems) >= 1:
                    if len(model_data.mdx_model_stems) >= 3:
                        self.mdxnet_stems_Label_place()
                        self.mdxnet_stems_Option_place()
                    else:
                        self.mdx_segment_size_Label_place()
                        self.mdx_segment_size_Option_place()
                    self.overlap_mdx_Label_place()
                    self.overlap_mdx23_Option_place()
                    self.update_button_states_mdx(model_data.mdx_model_stems)
                else:
                    if ai_type == MDX_ARCH_TYPE:
                        self.mdx_segment_size_Label_place()
                        self.mdx_segment_size_Option_place()
                        self.overlap_mdx_Label_place()
                        self.overlap_mdx_Option_place()

                    stem = model_data.primary_stem
                    self.update_stem_checkbox_labels(stem)

    def selection_action_process_method(self, selection, from_widget=False, is_from_conv_menu=False):
        return self.options_coordinator.selection_action_process_method(
            selection, from_widget=from_widget, is_from_conv_menu=is_from_conv_menu
        )

    def selection_action_chosen_ensemble(self, selection):
        return self.ensemble_panel.selection_action_chosen_ensemble(selection)

    def selection_action_chosen_ensemble_load_saved(self, saved_ensemble):
        return self.ensemble_panel.selection_action_chosen_ensemble_load_saved(saved_ensemble)

    def selection_action_ensemble_stems(self, selection: str, from_menu=True, auto_update=None):
        return self.ensemble_panel.selection_action_ensemble_stems(
            selection, from_menu=from_menu, auto_update=auto_update
        )

    def selection_action_saved_settings(self, selection, process_method=None):
        return self.settings_manager.selection_action_saved_settings(selection, process_method)

    def handle_special_options(self, selection, process_method):
        return self.settings_manager.handle_special_options(selection, process_method)

    def handle_saved_settings(self, selection, process_method):
        return self.settings_manager.handle_saved_settings(selection, process_method)

    #--Processing Methods-- 

    def process_input_selections(self):
        return self.process_controller.process_input_selections()

    def process_check_wav_type(self):
        return self.process_controller.process_check_wav_type()

    def process_preliminary_checks(self):
        return self.process_controller.process_preliminary_checks()

    def process_storage_check(self):
        return self.process_controller.process_storage_check()

    def process_initialize(self):
        return self.process_controller.process_initialize()


    def queue_worker_loop(self):
        return self.queue_ui.queue_worker_loop()

    def remove_selected_task(self):
        return self.queue_ui.remove_selected_task()

    def clear_task_queue(self):
        return self.queue_ui.clear_task_queue()

    def update_queue_ui_display(self):
        return self.queue_ui.update_queue_ui_display()

    def pause_resume_selected_task(self):
        return self.queue_ui.pause_resume_selected_task()

    def move_task_up(self):
        return self.queue_ui.move_task_up()

    def move_task_down(self):
        return self.queue_ui.move_task_down()

    def move_task_direction(self, direction):
        return self.queue_ui.move_task_direction(direction)

    def queue_selection_changed(self, event=None):
        return self.queue_ui.queue_selection_changed(event)

    def toggle_chime(self):
        return self.queue_ui.toggle_chime()

    def update_chime_button_text(self, *args):
        return self.queue_ui.update_chime_button_text(*args)

    def process_button_init(self):
        return self.process_controller.process_button_init()

    def process_button_queue_mode(self):
        return self.process_controller.process_button_queue_mode()

    def process_get_baseText(self, total_files, file_num, is_dual=False):
        return self.process_controller.process_get_baseText(total_files, file_num, is_dual)

    def process_update_progress(self, total_files, step: float = 1):
        return self.process_controller.process_update_progress(total_files, step)

    def show_stop_menu(self):
        return self.process_controller.show_stop_menu()

    def confirm_stop_process(self, stop_all=False):
        return self.process_controller.confirm_stop_process(stop_all)

    def process_end(self, error=None):
        return self.process_controller.process_end(error)

    def process_tool_start(self, task=None):
        return self.process_controller.process_tool_start(task)

    def process_determine_secondary_model(self, process_method, main_model_primary_stem, is_primary_stem_only=False, is_secondary_stem_only=False):
        return self.process_controller.process_determine_secondary_model(process_method, main_model_primary_stem, is_primary_stem_only, is_secondary_stem_only)

    def process_determine_demucs_pre_proc_model(self, primary_stem=None):
        return self.process_controller.process_determine_demucs_pre_proc_model(primary_stem)

    def process_determine_vocal_split_model(self):
        return self.process_controller.process_determine_vocal_split_model()

    def check_only_selection_stem(self, checktype):
        return self.process_controller.check_only_selection_stem(checktype)

    def determine_voc_split(self, models):
        return self.process_controller.determine_voc_split(models)

    def process_start(self, task=None):
        return self.process_controller.process_start(task)


    #--Varible Methods--

    # --Settings & Variables Delegates--

    def load_to_default_confirm(self):
        return self.settings_manager.load_to_default_confirm()

    def load_saved_vars(self, data):
        return self.settings_manager.load_saved_vars(data)

    def load_saved_settings(self, loaded_setting: dict, process_method=None, is_default_reset=False):
        return self.settings_manager.load_saved_settings(loaded_setting, process_method, is_default_reset)

    def save_values(self, app_close=True, is_restart=False, is_auto_save=False):
        return self.settings_manager.save_values(app_close, is_restart, is_auto_save)

    def get_settings_list(self):
        return self.settings_manager.get_settings_list()


def open_link(event, link=None):
    webbrowser.open(link)

def auto_hyperlink(text_widget:tk.Text):
    content = text_widget.get('1.0', tk.END)
    
    # Regular expression to identify URLs
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)

    for url in urls:
        start_idx = content.find(url)
        end_idx = start_idx + len(url)
        
        # Convert indices to tk.Text widget format
        start_line = content.count('\n', 0, start_idx) + 1
        start_char = start_idx - content.rfind('\n', 0, start_idx) - 1
        end_line = content.count('\n', 0, end_idx) + 1
        end_char = end_idx - content.rfind('\n', 0, end_idx) - 1

        start_tag = f"{start_line}.{start_char}"
        end_tag = f"{end_line}.{end_char}"

        # Tag the hyperlink text and configure it
        text_widget.tag_add(url, start_tag, end_tag)
        text_widget.tag_configure(url, foreground=FG_COLOR, underline=True)
        text_widget.tag_bind(url, "<Button-1>", lambda e, link=url: open_link(e, link))
        text_widget.tag_bind(url, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
        text_widget.tag_bind(url, "<Leave>", lambda e: text_widget.config(cursor="arrow"))

def extract_stems(audio_file_base, export_path):
    
    filenames = [file for file in os.listdir(export_path) if file.startswith(audio_file_base)]

    pattern = r'\(([^()]+)\)(?=[^()]*\.wav)'
    stem_list = []

    for filename in filenames:
        re_match = re.search(pattern, filename)
        if re_match:
            stem_list.append(re_match.group(1))
            
    counter = Counter(stem_list)
    filtered_lst = [item for item in stem_list if counter[item] > 1]

    return list(set(filtered_lst))

if __name__ == "__main__":
    from uvr.app import main
    main()
