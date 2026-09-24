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
    import shutil
    import subprocess
    import sys
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
    open_ensemble_model_settings,
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
from uvr.ui.dnd_bridge import CTkDnD
from uvr.ui.managers import DownloadManager, QueueUI, SettingsManager
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
        saved_settings_sub_menu = tk.Menu(parent_menu, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=False)
        settings_options = self.last_found_settings + tuple(SAVE_SET_OPTIONS)
        
        for opt in settings_options:
            opt_label = opt.replace("_", " ")
            saved_settings_sub_menu.add_command(label=opt_label, command=lambda o=opt_label:self.selection_action_saved_settings(o, process_method=process_method))

        saved_settings_sub_menu.insert_separator(len(self.last_found_settings))
        
        return saved_settings_sub_menu

    def right_click_menu_popup(self, event, text_box=False, main_menu=False):
        
        def add_text_edit_options(menu):
            """Add options related to text editing."""
            menu.add_command(label='Copy', command=self.right_click_menu_copy)
            menu.add_command(label='Paste', command=lambda: self.right_click_menu_paste(text_box=text_box))
            menu.add_command(label='Delete', command=lambda: self.right_click_menu_delete(text_box=text_box))
        
        def add_advanced_settings_options(menu, settings_mapper, var_mapper):
            """Add advanced settings options to the menu."""
            current_method = self.chosen_process_method_var.get()
            
            if current_method in settings_mapper and (var_mapper[current_method] or (current_method == DEMUCS_ARCH_TYPE and self.is_demucs_pre_proc_model_activate_var.get())):
                menu.add_cascade(label='Select Saved Settings', menu=saved_settings_sub_load_for_menu)
                menu.add_separator()
                for method, option in settings_mapper.items():
                    if method != ENSEMBLE_MODE or current_method == ENSEMBLE_MODE:
                        menu.add_command(label=f'Advanced {method} Settings', command=option)
            elif current_method in settings_mapper:
                menu.add_command(label=f'Advanced {current_method} Settings', command=settings_mapper[current_method])

        # Create the right-click menu
        right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)

        # Mappings
        settings_mapper = {
            ENSEMBLE_MODE: lambda: self.check_is_menu_open(ENSEMBLE_OPTION),
            VR_ARCH_PM: lambda: self.check_is_menu_open(VR_OPTION),
            MDX_ARCH_TYPE: lambda: self.check_is_menu_open(MDX_OPTION),
            DEMUCS_ARCH_TYPE: lambda: self.check_is_menu_open(DEMUCS_OPTION)
        }
        
        var_mapper = {
            ENSEMBLE_MODE: True,
            VR_ARCH_PM: self.vr_is_secondary_model_activate_var.get(),
            MDX_ARCH_TYPE: self.mdx_is_secondary_model_activate_var.get(),
            DEMUCS_ARCH_TYPE: self.demucs_is_secondary_model_activate_var.get()
        }

        # Submenu for saved settings
        saved_settings_sub_load_for_menu = tk.Menu(right_click_menu, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=False)
        for label, arch_type in [(VR_ARCH_SETTING_LOAD, VR_ARCH_PM), (MDX_SETTING_LOAD, MDX_ARCH_TYPE), (DEMUCS_SETTING_LOAD, DEMUCS_ARCH_TYPE), (ALL_ARCH_SETTING_LOAD, None)]:
            submenu = self.right_click_select_settings_sub(saved_settings_sub_load_for_menu, arch_type)
            saved_settings_sub_load_for_menu.add_cascade(label=label, menu=submenu)

        if not main_menu:
            add_text_edit_options(right_click_menu)
        else:
            if self.chosen_process_method_var.get() == AUDIO_TOOLS and self.chosen_audio_tool_var.get() == ALIGN_INPUTS:
                right_click_menu.add_command(label='Advanced Align Tool Settings', command=lambda: self.check_is_menu_open(ALIGNMENT_TOOL))
            else:
                add_advanced_settings_options(right_click_menu, settings_mapper, var_mapper)

            # Additional Settings and Help Hints
            if not self.is_menu_settings_open:
                right_click_menu.add_command(label='Additional Settings', command=lambda: self.menu_settings(select_tab_2=True))
                
            help_hints_label = 'Enable' if not self.help_hints_var.get() else 'Disable'
            right_click_menu.add_command(label=f'{help_hints_label} Help Hints', command=lambda: self.help_hints_var.set(not self.help_hints_var.get()))
                
            if self.error_log_var.get():
                right_click_menu.add_command(label='Error Log', command=lambda: self.check_is_menu_open(ERROR_OPTION))

        try:
            right_click_menu.tk_popup(event.x_root, event.y_root)
            right_click_release_linux(right_click_menu)
        finally:
            right_click_menu.grab_release()

    def right_click_menu_copy(self):
        hightlighted_text = self.current_text_box.selection_get()
        self.clipboard_clear()
        self.clipboard_append(hightlighted_text)

    def right_click_menu_paste(self, text_box=False):
        clipboard = self.clipboard_get()
        self.right_click_menu_delete(text_box=True) if text_box else self.right_click_menu_delete()
        self.current_text_box.insert(self.current_text_box.index(tk.INSERT), clipboard)

    def right_click_menu_delete(self, text_box=False):
        if text_box:
            try:
                s0 = self.current_text_box.index("sel.first")
                s1 = self.current_text_box.index("sel.last")
                self.current_text_box.tag_configure('highlight')
                self.current_text_box.tag_add("highlight", s0, s1)
                start_indexes = self.current_text_box.tag_ranges("highlight")[0::2]
                end_indexes = self.current_text_box.tag_ranges("highlight")[1::2]

                for start, end in zip(start_indexes, end_indexes):
                    self.current_text_box.tag_remove("highlight", start, end)

                for start, end in zip(start_indexes, end_indexes):
                    self.current_text_box.delete(start, end)
            except Exception as e:
                print('RIGHT-CLICK-DELETE ERROR: \n', e)
        else:
            self.current_text_box.delete(0, tk.END)
    
    def right_click_console(self, event):
        right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
        right_click_menu.add_command(label='Copy', command=self.command_Text.copy_text)
        right_click_menu.add_command(label='Select All', command=self.command_Text.select_all_text)
        
        try:
            right_click_menu.tk_popup(event.x_root,event.y_root)
            right_click_release_linux(right_click_menu)
        finally:
            right_click_menu.grab_release()

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
                     
        menu_view_inputs_top = tk.Toplevel(root)
    
        self.is_open_menu_view_inputs.set(True)
        self.menu_view_inputs_close_window = lambda:close_window()
        menu_view_inputs_top.protocol("WM_DELETE_WINDOW", self.menu_view_inputs_close_window)
    
        input_length_var = tk.StringVar(value='')   
        input_info_text_var = tk.StringVar(value='')  
        is_widen_box_var = tk.BooleanVar(value=False) 
        is_play_file_var = tk.BooleanVar(value=False) 
        varification_text_var = tk.StringVar(value=VERIFY_INPUTS_TEXT)

        reset_list = lambda:(input_files_listbox_Option.delete(0, 'end'), [input_files_listbox_Option.insert(tk.END, inputs) for inputs in self.inputPaths])
        audio_input_total = lambda:input_length_var.set(f'{AUDIO_INPUT_TOTAL_TEXT}: {len(self.inputPaths)}')
        audio_input_total()

        def list_diff(list1, list2): return list(set(list1).symmetric_difference(set(list2)))

        def list_to_string(list1): return '\n'.join(''.join(sub) for sub in list1)

        def close_window():
            self.verification_thread.kill() if self.thread_check(self.verification_thread) else None
            self.is_open_menu_view_inputs.set(False)
            menu_view_inputs_top.destroy()

        def drag_n_drop(e):
            input_info_text_var.set('')
            drop(e, accept_mode='files')
            reset_list()
            audio_input_total()
            
        def selected_files(is_remove=False):
            items_list = [input_files_listbox_Option.get(i) for i in input_files_listbox_Option.curselection()]
            inputPaths = list(self.inputPaths)# if is_remove else items_list
            if is_remove:
                [inputPaths.remove(i) for i in items_list if items_list]
            else:
                [inputPaths.remove(i) for i in self.inputPaths if i not in items_list]
            removed_files = list_diff(self.inputPaths, inputPaths)
            [input_files_listbox_Option.delete(input_files_listbox_Option.get(0, tk.END).index(i)) for i in removed_files]
            starting_len = len(self.inputPaths)
            self.inputPaths = tuple(inputPaths)
            self.update_inputPaths()
            audio_input_total()
            input_info_text_var.set(f'{starting_len - len(self.inputPaths)} input(s) removed.')
            
        def box_size():
            input_info_text_var.set('')
            input_files_listbox_Option.config(width=230, height=25) if is_widen_box_var.get() else input_files_listbox_Option.config(width=110, height=17)
            self.menu_placement(menu_view_inputs_top, 'Selected Inputs', pop_up=True)

        def input_options(is_select_inputs=True):
            input_info_text_var.set('')
            if is_select_inputs:
                menu_view_inputs_top.withdraw()
                self.input_select_filedialog(parent_win=menu_view_inputs_top, is_append=True)
                menu_view_inputs_top.deiconify()
            else:
                self.inputPaths = ()
            reset_list()
            self.update_inputPaths()
            audio_input_total()

        def pop_open_file_path(is_play_file=False):
            if self.inputPaths:
                track_selected = self.inputPaths[input_files_listbox_Option.index(tk.ACTIVE)]
                if os.path.isfile(track_selected):
                    OPEN_FILE_func(track_selected if is_play_file else os.path.dirname(track_selected))
        
        def get_export_dir():
            if os.path.isdir(self.export_path_var.get()):
                export_dir = self.export_path_var.get()
            else:
                export_dir = self.export_select_filedialog()

            return export_dir
        
        def verify_audio(is_create_samples=False):
            inputPaths = list(self.inputPaths)
            iterated_list = self.inputPaths if not is_create_samples else [input_files_listbox_Option.get(i) for i in input_files_listbox_Option.curselection()]
            removed_files = []
            export_dir = None
            total_audio_count, current_file = len(iterated_list), 0
            if iterated_list:
                for i in iterated_list:
                    current_file += 1
                    input_info_text_var.set(f'{SAMPLE_BEGIN if is_create_samples else VERIFY_BEGIN}{current_file}/{total_audio_count}')
                    if is_create_samples:
                        export_dir = get_export_dir()
                        if not export_dir:
                            input_info_text_var.set('No export directory selected.')
                            return
                    is_good, error_data = self.verify_audio(i, is_process=False, sample_path=export_dir)
                    if not is_good:
                        inputPaths.remove(i)
                        removed_files.append(error_data)#sample = self.create_sample(i)
                        
                varification_text_var.set(VERIFY_INPUTS_TEXT)
                input_files_listbox_Option.configure(state=tk.NORMAL)
                
                if removed_files:
                    input_info_text_var.set(f'{len(removed_files)} {BROKEN_OR_INCOM_TEXT}')
                    error_text = ''
                    for i in removed_files:
                        error_text += i
                    removed_files = list_diff(self.inputPaths, inputPaths)
                    [input_files_listbox_Option.delete(input_files_listbox_Option.get(0, tk.END).index(i)) for i in removed_files]
                    self.error_log_var.set(REMOVED_FILES(list_to_string(removed_files), error_text))
                    self.inputPaths = tuple(inputPaths)
                    self.update_inputPaths()
                else:
                    input_info_text_var.set('No errors found!')
                    
                audio_input_total()
            else:
                input_info_text_var.set(f'{NO_FILES_TEXT} {SELECTED_VER if is_create_samples else DETECTED_VER}')
                varification_text_var.set(VERIFY_INPUTS_TEXT)
                input_files_listbox_Option.configure(state=tk.NORMAL)
                return
            
            audio_input_total()
            
        def verify_audio_start_thread(is_create_samples=False):
            
            if not self.thread_check(self.active_processing_thread):
                if not self.thread_check(self.verification_thread):
                    varification_text_var.set('Stop Progress')
                    input_files_listbox_Option.configure(state=tk.DISABLED)
                    self.verification_thread = KThread(target=lambda:verify_audio(is_create_samples=is_create_samples))
                    self.verification_thread.start()
                else:
                    input_files_listbox_Option.configure(state=tk.NORMAL)
                    varification_text_var.set(VERIFY_INPUTS_TEXT)
                    input_info_text_var.set('Process Stopped')
                    self.verification_thread.kill()
            else:
                input_info_text_var.set('You cannot verify inputs during an active process.')

        def right_click_menu(event):
                right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
                right_click_menu.add_command(label='Remove Selected Items Only', command=lambda:selected_files(is_remove=True))
                right_click_menu.add_command(label='Keep Selected Items Only', command=lambda:selected_files(is_remove=False))
                right_click_menu.add_command(label='Clear All Input(s)', command=lambda:input_options(is_select_inputs=False))
                right_click_menu.add_separator()
                right_click_menu_sub = tk.Menu(right_click_menu, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=False)
                right_click_menu.add_command(label='Verify and Create Samples of Selected Inputs', command=lambda:verify_audio_start_thread(is_create_samples=True))
                right_click_menu.add_cascade(label='Preferred Double Click Action', menu=right_click_menu_sub)
                if is_play_file_var.get():
                    right_click_menu_sub.add_command(label='Enable: Open Audio File Directory', command=lambda:(input_files_listbox_Option.bind('<Double-Button>', lambda e:pop_open_file_path()), is_play_file_var.set(False)))
                else:
                    right_click_menu_sub.add_command(label='Enable: Open Audio File', command=lambda:(input_files_listbox_Option.bind('<Double-Button>', lambda e:pop_open_file_path(is_play_file=True)), is_play_file_var.set(True)))

                try:
                    right_click_menu.tk_popup(event.x_root,event.y_root)
                    right_click_release_linux(right_click_menu, menu_view_inputs_top)
                finally:
                    right_click_menu.grab_release()

        def move_selected_input(direction):
            selected = input_files_listbox_Option.curselection()
            if not selected:
                return
            idx = selected[0]
            new_idx = idx + direction
            if new_idx < 0 or new_idx >= len(self.inputPaths):
                return
            
            paths_list = list(self.inputPaths)
            paths_list[idx], paths_list[new_idx] = paths_list[new_idx], paths_list[idx]
            self.inputPaths = tuple(paths_list)
            
            reset_list()
            input_files_listbox_Option.selection_set(new_idx)
            input_files_listbox_Option.activate(new_idx)
            input_files_listbox_Option.see(new_idx)
            self.update_inputPaths()

        menu_view_inputs_Frame = self.menu_FRAME_SET(menu_view_inputs_top)
        menu_view_inputs_Frame.grid(row=0)  

        self.main_window_LABEL_SET(menu_view_inputs_Frame, SELECTED_INPUTS).grid(row=0,column=0,padx=0,pady=MENU_PADDING_1)
        tk.Label(menu_view_inputs_Frame, textvariable=input_length_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR).grid(row=1, column=0, padx=0, pady=MENU_PADDING_1)
        if not OPERATING_SYSTEM == "Linux":
            ttk.Button(menu_view_inputs_Frame, text=SELECT_INPUTS, command=lambda:input_options()).grid(row=2,column=0,padx=0,pady=MENU_PADDING_2)
        input_files_listbox_Option = tk.Listbox(menu_view_inputs_Frame, selectmode=tk.EXTENDED, activestyle='dotbox', font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), background='#101414', exportselection=0, width=150, height=20, relief=tk.SOLID, borderwidth=0)
        input_files_listbox_vertical_scroll = ttk.Scrollbar(menu_view_inputs_Frame, orient=tk.VERTICAL)
        input_files_listbox_Option.config(yscrollcommand=input_files_listbox_vertical_scroll.set)
        input_files_listbox_vertical_scroll.configure(command=input_files_listbox_Option.yview)
        input_files_listbox_Option.grid(row=4, sticky=tk.W)
        input_files_listbox_vertical_scroll.grid(row=4, column=1, sticky=tk.NS)

        tk.Label(menu_view_inputs_Frame, textvariable=input_info_text_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR).grid(row=5, column=0, padx=0, pady=0)
        inputs_buttons_frame = tk.Frame(menu_view_inputs_Frame, bg='#101414')
        inputs_buttons_frame.grid(row=6, column=0, pady=MENU_PADDING_1)
        
        ttk.Button(inputs_buttons_frame, text="Add New Files", command=lambda:input_options(is_select_inputs=True), width=15).pack(side="left", padx=5)
        ttk.Button(inputs_buttons_frame, text="Remove Selected", command=lambda:selected_files(is_remove=True), width=15).pack(side="left", padx=5)
        ttk.Button(inputs_buttons_frame, image=self.up_img, command=lambda: move_selected_input(-1)).pack(side="left", padx=5)
        ttk.Button(inputs_buttons_frame, image=self.down_img, command=lambda: move_selected_input(1)).pack(side="left", padx=5)

        if is_dnd_compatible:
            menu_view_inputs_top.drop_target_register(DND_FILES)
            menu_view_inputs_top.dnd_bind('<<Drop>>', lambda e: drag_n_drop(e))
        input_files_listbox_Option.bind(right_click_button, lambda e:right_click_menu(e))
        input_files_listbox_Option.bind('<Double-Button>', lambda e:pop_open_file_path())
        input_files_listbox_Option.bind('<Delete>', lambda e:selected_files(is_remove=True))
        input_files_listbox_Option.bind('<BackSpace>', lambda e:selected_files(is_remove=False))

        reset_list()

        self.menu_placement(menu_view_inputs_top, 'Selected Inputs', pop_up=True)

    def menu_batch_dual(self):
        menu_batch_dual_top = tk.Toplevel(root)
        
        def drag_n_drop(event, accept_mode):
            listbox = left_frame if accept_mode == FILE_1_LB else right_frame
            paths = drop(event, accept_mode)
            for item in paths:
                if item not in listbox.path_list:  # only add file if it's not already in the list
                    basename = os.path.basename(item)
                    listbox.listbox.insert(tk.END, basename)  # insert basename to the listbox
                    listbox.path_list.append(item)  # append the file path to the list
            listbox.update_displayed_index()
        
        def move_entry(is_primary=True):
            if is_primary:
                selected_frame, other_frame = left_frame, right_frame
            else:
                selected_frame, other_frame = right_frame, left_frame

            selected = selected_frame.listbox.curselection()

            if selected:
                basename = selected_frame.listbox.get(selected[0]).split(': ', 1)[1]  # remove displayed index

                if basename in other_frame.basename_to_path:
                    return

                path = selected_frame.basename_to_path[basename]  # Get the actual path

                selected_frame.listbox.delete(selected)
                other_frame.listbox.insert(tk.END, basename)

                selected_frame.path_list.remove(path)
                del selected_frame.basename_to_path[basename]

                other_frame.path_list.append(path)
                other_frame.basename_to_path[basename] = path

                selected_frame.update_displayed_index()
                other_frame.update_displayed_index()
        
        def open_selected_path(lb, is_play_file=False):
            selected_frame = left_frame if lb == FILE_1_LB else right_frame
            selected_path = selected_frame.get_selected_path()
            
            if selected_path:
                if os.path.isfile(selected_path):
                    OPEN_FILE_func(selected_path if is_play_file else os.path.dirname(selected_path))

        def clear_all_data(lb):
            selected_frame = left_frame if lb == FILE_1_LB else right_frame
            selected_frame.listbox.delete(0, "end")
            selected_frame.path_list.clear()
            selected_frame.basename_to_path.clear()
        
        def clear_all(event, lb):
            selected_frame = left_frame if lb == FILE_1_LB else right_frame
            selected = selected_frame.listbox.curselection()
            
            right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
            if selected:
                right_click_menu.add_command(label='Open Location', command=lambda:open_selected_path(lb))
                right_click_menu.add_command(label='Open File', command=lambda:open_selected_path(lb, is_play_file=True))
            right_click_menu.add_command(label='Clear All', command=lambda:clear_all_data(lb))

            try:
                right_click_menu.tk_popup(event.x_root,event.y_root)
                right_click_release_linux(right_click_menu, menu_batch_dual_top)
            finally:
                right_click_menu.grab_release()
       
        def gather_input_list():
            left_paths = list(left_frame.basename_to_path.values())
            right_paths = list(right_frame.basename_to_path.values())
            
            clear_all_data(FILE_1_LB)
            clear_all_data(FILE_2_LB)
            
            if left_paths and right_paths:
                left_frame.select_input(left_paths)
                right_frame.select_input(right_paths)

            self.DualBatch_inputPaths = list(zip(left_paths, right_paths))
            self.check_dual_paths()
            menu_batch_dual_top.destroy()

        menu_view_inputs_Frame = self.menu_FRAME_SET(menu_batch_dual_top)
        menu_view_inputs_Frame.grid(row=0)
        
        left_frame = ListboxBatchFrame(menu_view_inputs_Frame, self.file_one_sub_var.get().title(), move_entry, self.right_img, self.img_mapper)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        right_frame = ListboxBatchFrame(menu_view_inputs_Frame, self.file_two_sub_var.get().title(), lambda:move_entry(False), self.left_img, self.img_mapper)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        left_frame.listbox.drop_target_register(DND_FILES)
        right_frame.listbox.drop_target_register(DND_FILES)
        left_frame.listbox.dnd_bind('<<Drop>>', lambda e: drag_n_drop(e, FILE_1_LB))
        right_frame.listbox.dnd_bind('<<Drop>>', lambda e: drag_n_drop(e, FILE_2_LB))
        left_frame.listbox.dnd_bind(right_click_button, lambda e: clear_all(e, FILE_1_LB))
        right_frame.listbox.dnd_bind(right_click_button, lambda e: clear_all(e, FILE_2_LB))

        menu_view_inputs_bottom_Frame = self.menu_FRAME_SET(menu_batch_dual_top)
        menu_view_inputs_bottom_Frame.grid(row=1)
        
        confirm_btn = ttk.Button(menu_view_inputs_bottom_Frame, text=CONFIRM_ENTRIES, command=gather_input_list)
        confirm_btn.grid(pady=MENU_PADDING_1)
        
        close_btn = ttk.Button(menu_view_inputs_bottom_Frame, text=CLOSE_WINDOW, command=lambda:menu_batch_dual_top.destroy())
        close_btn.grid(pady=MENU_PADDING_1)

        if self.check_dual_paths():
            left_frame_pane = [i[0] for i in self.DualBatch_inputPaths]
            right_frame_pane = [i[1] for i in self.DualBatch_inputPaths]
            left_frame.update_displayed_index(left_frame_pane)
            right_frame.update_displayed_index(right_frame_pane)
            self.check_dual_paths()

        self.menu_placement(menu_batch_dual_top, DUAL_AUDIO_PROCESSING, pop_up=True)

    def check_dual_paths(self, is_fill_menu=False):
        
        if self.DualBatch_inputPaths:
            first_paths = tuple(self.DualBatch_inputPaths)
            first_paths_len = len(first_paths)
            first_paths = first_paths[0]
            
            if first_paths_len == 1:
                file1_base_text = os.path.basename(first_paths[0])
                file2_base_text = os.path.basename(first_paths[1])
            else:
                first_paths_len = first_paths_len - 1
                file1_base_text = f"{os.path.basename(first_paths[0])}, +{first_paths_len} file(s){BATCH_MODE_DUAL}"
                file2_base_text = f"{os.path.basename(first_paths[1])}, +{first_paths_len} file(s){BATCH_MODE_DUAL}"
            
            self.fileOneEntry_var.set(file1_base_text)
            self.fileOneEntry_Full_var.set(f"{first_paths[0]}")
            self.fileTwoEntry_var.set(file2_base_text)
            self.fileTwoEntry_Full_var.set(f"{first_paths[1]}")
        else:
            if is_fill_menu:
                file_one = self.fileOneEntry_Full_var.get()
                file_two = self.fileTwoEntry_Full_var.get()

                if file_one and file_two and BATCH_MODE_DUAL not in file_one and BATCH_MODE_DUAL not in file_two:
                    self.DualBatch_inputPaths = [(file_one, file_two)]
            else:
                if BATCH_MODE_DUAL in self.fileOneEntry_var.get():
                    self.fileOneEntry_var.set("")
                    self.fileOneEntry_Full_var.set("")
                if BATCH_MODE_DUAL in self.fileTwoEntry_var.get():
                    self.fileTwoEntry_var.set("")
                    self.fileTwoEntry_Full_var.set("")
            
        return self.DualBatch_inputPaths

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

    def menu_settings(self, select_tab_2=False, select_tab_3=False):#**
        """Open Settings and Download Center"""

        settings_menu = tk.Toplevel()
        
        option_var = tk.StringVar(value=SELECT_SAVED_SETTING)
        self.is_menu_settings_open = True
        
        tabControl = ttk.Notebook(settings_menu)
  
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)

        tabControl.add(tab1, text = SETTINGS_GUIDE_TEXT)
        tabControl.add(tab2, text = ADDITIONAL_SETTINGS_TEXT)
        tabControl.add(tab3, text = DOWNLOAD_CENTER_TEXT)

        tabControl.pack(expand = 1, fill ="both")
        
        tab1.grid_rowconfigure(0, weight=1)
        tab1.grid_columnconfigure(0, weight=1)
        
        tab2.grid_rowconfigure(0, weight=1)
        tab2.grid_columnconfigure(0, weight=1)
        
        tab3.grid_rowconfigure(0, weight=1)
        tab3.grid_columnconfigure(0, weight=1)

        self.disable_tabs = lambda:(tabControl.tab(0, state="disabled"), tabControl.tab(1, state="disabled"))
        self.enable_tabs = lambda:(tabControl.tab(0, state="normal"), tabControl.tab(1, state="normal"))        
        self.main_menu_var = tk.StringVar(value=CHOOSE_ADVANCED_MENU_TEXT) 

        self.download_progress_bar_var.set(0)
        self.download_progress_info_var.set('')
        self.download_progress_percent_var.set('')
                
        def set_vars_for_sample_mode(event):
            value = int(float(event))
            value = round(value / 5) * 5
            self.model_sample_mode_duration_var.set(value)
            self.model_sample_mode_duration_checkbox_var.set(SAMPLE_MODE_CHECKBOX(value))
            self.model_sample_mode_duration_label_var.set(f'{value} {SECONDS_TEXT}')
            
        #Settings Tab 1
        settings_menu_main_Frame = self.menu_FRAME_SET(tab1)
        settings_menu_main_Frame.grid(row=0)  
        settings_title_Label = self.menu_title_LABEL_SET(settings_menu_main_Frame, GENERAL_MENU_TEXT)
        settings_title_Label.grid(pady=MENU_PADDING_2)
        
        select_Label = self.menu_sub_LABEL_SET(settings_menu_main_Frame, ADDITIONAL_MENUS_INFORMATION_TEXT)
        select_Label.grid(pady=MENU_PADDING_1)
        
        select_Option = ComboBoxMenu(settings_menu_main_Frame, textvariable=self.main_menu_var, values=OPTION_LIST, width=GEN_SETTINGS_WIDTH+3)
        select_Option.update_dropdown_size(OPTION_LIST, 'menuchoose', command=lambda e:(self.check_is_menu_open(self.main_menu_var.get()), close_window()))
        select_Option.grid(pady=MENU_PADDING_1)
        
        help_hints_Option = ttk.Checkbutton(settings_menu_main_Frame, text=ENABLE_HELP_HINTS_TEXT, variable=self.help_hints_var, width=HELP_HINT_CHECKBOX_WIDTH) 
        help_hints_Option.grid(pady=MENU_PADDING_1)
        
        open_app_dir_Button = ttk.Button(settings_menu_main_Frame, text=OPEN_APPLICATION_DIRECTORY_TEXT, command=lambda:OPEN_FILE_func(BASE_PATH), width=SETTINGS_BUT_WIDTH)
        open_app_dir_Button.grid(pady=MENU_PADDING_1)
        
        reset_all_app_settings_Button = ttk.Button(settings_menu_main_Frame, text=RESET_ALL_SETTINGS_TO_DEFAULT_TEXT, command=lambda:self.load_to_default_confirm(), width=SETTINGS_BUT_WIDTH)#pop_up_change_model_defaults
        reset_all_app_settings_Button.grid(pady=MENU_PADDING_1)
        
        if is_windows:
            restart_app_Button = ttk.Button(settings_menu_main_Frame, text=RESTART_APPLICATION_TEXT, command=lambda:self.restart())
            restart_app_Button.grid(pady=MENU_PADDING_1)

        delete_your_settings_Label = self.menu_title_LABEL_SET(settings_menu_main_Frame, DELETE_USER_SAVED_SETTING_TEXT)
        delete_your_settings_Label.grid(pady=MENU_PADDING_2)
        self.help_hints(delete_your_settings_Label, text=DELETE_YOUR_SETTINGS_HELP)
        
        delete_your_settings_Option = ComboBoxMenu(settings_menu_main_Frame, textvariable=option_var, width=GEN_SETTINGS_WIDTH+3)
        delete_your_settings_Option.grid(padx=20,pady=MENU_PADDING_1)
        self.deletion_list_fill(delete_your_settings_Option, option_var, SETTINGS_CACHE_DIR, SELECT_SAVED_SETTING, menu_name='deletesetting')

        delete_model_Label = self.menu_title_LABEL_SET(settings_menu_main_Frame, DELETE_MODEL_TEXT)
        delete_model_Label.grid(pady=MENU_PADDING_2)
        self.help_hints(delete_model_Label, text=DELETE_MODEL_HELP)
        
        self.delete_model_var = tk.StringVar(value="Select Model to Delete")
        self.delete_model_Option = ComboBoxMenu(settings_menu_main_Frame, textvariable=self.delete_model_var, width=GEN_SETTINGS_WIDTH+3)
        self.delete_model_Option.grid(padx=20,pady=MENU_PADDING_1)
        self.update_delete_model_list()

        app_update_Label = self.menu_title_LABEL_SET(settings_menu_main_Frame, APPLICATION_UPDATES_TEXT)
        app_update_Label.grid(pady=MENU_PADDING_2)
        
        self.app_update_button = ttk.Button(settings_menu_main_Frame, textvariable=self.app_update_button_Text_var, width=SETTINGS_BUT_WIDTH-2, command=lambda:self.pop_up_update_confirmation())
        self.app_update_button.grid(pady=MENU_PADDING_1)
        
        self.app_update_status_Label = tk.Label(settings_menu_main_Frame, textvariable=self.app_update_status_Text_var, padx=3, pady=3, font=(MAIN_FONT_NAME,  f"{FONT_SIZE_4}"), width=UPDATE_LABEL_WIDTH, justify="center", relief="ridge", fg="#13849f")
        self.app_update_status_Label.grid(pady=20)
        
        donate_Button = ttk.Button(settings_menu_main_Frame, image=self.donate_img, command=lambda:webbrowser.open_new_tab(DONATE_LINK_BMAC))
        donate_Button.grid(pady=MENU_PADDING_2)
        self.help_hints(donate_Button, text=DONATE_HELP)
        
        close_settings_win_Button = ttk.Button(settings_menu_main_Frame, text=CLOSE_WINDOW, command=lambda:close_window())
        close_settings_win_Button.grid(pady=MENU_PADDING_1)      
          
        #Settings Tab 2
        settings_menu_format_Frame = self.menu_FRAME_SET(tab2)
        settings_menu_format_Frame.grid(row=0)  
        
        audio_format_title_Label = self.menu_title_LABEL_SET(settings_menu_format_Frame, AUDIO_FORMAT_SETTINGS_TEXT, width=20)
        audio_format_title_Label.grid(pady=MENU_PADDING_2)
        
        wav_type_set_Label = self.menu_sub_LABEL_SET(settings_menu_format_Frame, WAV_TYPE_TEXT)
        wav_type_set_Label.grid(pady=MENU_PADDING_1)
        
        wav_type_set_Option = ComboBoxMenu(settings_menu_format_Frame, textvariable=self.wav_type_set_var, values=WAV_TYPE, width=HELP_HINT_CHECKBOX_WIDTH)
        wav_type_set_Option.grid(padx=20,pady=MENU_PADDING_1)
        
        mp3_bit_set_Label = self.menu_sub_LABEL_SET(settings_menu_format_Frame, MP3_BITRATE_TEXT)
        mp3_bit_set_Label.grid(pady=MENU_PADDING_1)
        
        mp3_bit_set_Option = ComboBoxMenu(settings_menu_format_Frame, textvariable=self.mp3_bit_set_var, values=MP3_BIT_RATES, width=HELP_HINT_CHECKBOX_WIDTH)
        mp3_bit_set_Option.grid(padx=20,pady=MENU_PADDING_1)

        audio_format_title_Label = self.menu_title_LABEL_SET(settings_menu_format_Frame, GENERAL_PROCESS_SETTINGS_TEXT)
        audio_format_title_Label.grid(pady=MENU_PADDING_2)
        
        is_testing_audio_Option = ttk.Checkbutton(settings_menu_format_Frame, text=SETTINGS_TEST_MODE_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_testing_audio_var) 
        is_testing_audio_Option.grid()
        self.help_hints(is_testing_audio_Option, text=IS_TESTING_AUDIO_HELP)
        
        is_add_model_name_Option = ttk.Checkbutton(settings_menu_format_Frame, text=MODEL_TEST_MODE_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_add_model_name_var) 
        is_add_model_name_Option.grid()
        self.help_hints(is_add_model_name_Option, text=IS_MODEL_TESTING_AUDIO_HELP)
        
        is_create_model_folder_Option = ttk.Checkbutton(settings_menu_format_Frame, text=GENERATE_MODEL_FOLDER_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_create_model_folder_var) 
        is_create_model_folder_Option.grid()
        self.help_hints(is_create_model_folder_Option, text=IS_CREATE_MODEL_FOLDER_HELP)
        
        is_accept_any_input_Option = ttk.Checkbutton(settings_menu_format_Frame, text=ACCEPT_ANY_INPUT_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_accept_any_input_var) 
        is_accept_any_input_Option.grid()
        self.help_hints(is_accept_any_input_Option, text=IS_ACCEPT_ANY_INPUT_HELP)
        
        is_task_complete_Option = ttk.Checkbutton(settings_menu_format_Frame, text=NOTIFICATION_CHIMES_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_task_complete_var) 
        is_task_complete_Option.grid()
        self.help_hints(is_task_complete_Option, text=IS_TASK_COMPLETE_HELP)
        
        is_normalization_Option = ttk.Checkbutton(settings_menu_format_Frame, text=NORMALIZE_OUTPUT_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_normalization_var) 
        is_normalization_Option.grid()
        self.help_hints(is_normalization_Option, text=IS_NORMALIZATION_HELP)
        
        is_replaygain_Option = ttk.Checkbutton(settings_menu_format_Frame, text=REPLAYGAIN_TEXT, width=GEN_SETTINGS_WIDTH, variable=self.is_replaygain_var) 
        is_replaygain_Option.grid()
        self.help_hints(is_replaygain_Option, text=IS_REPLAYGAIN_HELP)
        
        change_model_default_Button = ttk.Button(settings_menu_format_Frame, text=CHANGE_MODEL_DEFAULTS_TEXT, command=lambda:self.pop_up_change_model_defaults(settings_menu), width=SETTINGS_BUT_WIDTH-2)#
        change_model_default_Button.grid(pady=MENU_PADDING_4)

        #if not is_choose_arch:
        self.vocal_splitter_Button_opt(settings_menu, settings_menu_format_Frame, width=SETTINGS_BUT_WIDTH-2, pady=MENU_PADDING_4)

        if not is_macos and self.is_gpu_available:
            gpu_list_options = lambda:self.loop_gpu_list(device_set_Option, 'gpudevice', self.cuda_device_list)
            device_set_Label = self.menu_title_LABEL_SET(settings_menu_format_Frame, CUDA_NUM_TEXT)
            device_set_Label.grid(pady=MENU_PADDING_2)
            
            device_set_Option = ComboBoxMenu(settings_menu_format_Frame, textvariable=self.device_set_var, values=GPU_DEVICE_NUM_OPTS, width=GEN_SETTINGS_WIDTH+1)
            device_set_Option.grid(padx=20,pady=MENU_PADDING_1)
            gpu_list_options()
            self.help_hints(device_set_Label, text=IS_CUDA_SELECT_HELP)

        model_sample_mode_Label = self.menu_title_LABEL_SET(settings_menu_format_Frame, MODEL_SAMPLE_MODE_SETTINGS_TEXT)
        model_sample_mode_Label.grid(pady=MENU_PADDING_2)
        
        model_sample_mode_duration_Label = self.menu_sub_LABEL_SET(settings_menu_format_Frame, SAMPLE_CLIP_DURATION_TEXT)
        model_sample_mode_duration_Label.grid(pady=MENU_PADDING_1)
        
        tk.Label(settings_menu_format_Frame, textvariable=self.model_sample_mode_duration_label_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR).grid(pady=2)
        model_sample_mode_duration_Option = ttk.Scale(settings_menu_format_Frame, variable=self.model_sample_mode_duration_var, from_=5, to=120, command=set_vars_for_sample_mode, orient='horizontal')
        model_sample_mode_duration_Option.grid(pady=2)
        
        #Settings Tab 3
        settings_menu_download_center_Frame = self.menu_FRAME_SET(tab3)
        settings_menu_download_center_Frame.grid(row=0)  
        
        download_center_title_Label = self.menu_title_LABEL_SET(settings_menu_download_center_Frame, APPLICATION_DOWNLOAD_CENTER_TEXT)
        download_center_title_Label.grid(padx=20,pady=MENU_PADDING_2)

        select_download_Label = self.menu_sub_LABEL_SET(settings_menu_download_center_Frame, SELECT_DOWNLOAD_TEXT)
        select_download_Label.grid(pady=MENU_PADDING_2)
        
        self.model_download_vr_Button = ttk.Radiobutton(settings_menu_download_center_Frame, text='VR Arch', width=8, variable=self.select_download_var, value='VR Arc', command=lambda:self.download_list_state())
        self.model_download_vr_Button.grid(pady=MENU_PADDING_1)
        self.model_download_vr_Option = ComboBoxMenu(settings_menu_download_center_Frame, textvariable=self.model_download_vr_var, width=READ_ONLY_COMBO_WIDTH)
        self.model_download_vr_Option.grid(pady=MENU_PADDING_1)
        
        self.model_download_mdx_Button = ttk.Radiobutton(settings_menu_download_center_Frame, text='MDX-Net', width=8, variable=self.select_download_var, value='MDX-Net', command=lambda:self.download_list_state())
        self.model_download_mdx_Button.grid(pady=MENU_PADDING_1)
        self.model_download_mdx_Option = ComboBoxMenu(settings_menu_download_center_Frame, textvariable=self.model_download_mdx_var, width=READ_ONLY_COMBO_WIDTH)
        self.model_download_mdx_Option.grid(pady=MENU_PADDING_1)

        self.model_download_demucs_Button = ttk.Radiobutton(settings_menu_download_center_Frame, text='Demucs', width=8, variable=self.select_download_var, value='Demucs', command=lambda:self.download_list_state())
        self.model_download_demucs_Button.grid(pady=MENU_PADDING_1)
        self.model_download_demucs_Option = ComboBoxMenu(settings_menu_download_center_Frame, textvariable=self.model_download_demucs_var, width=READ_ONLY_COMBO_WIDTH)
        self.model_download_demucs_Option.grid(pady=MENU_PADDING_1)
        
        self.download_Button = ttk.Button(settings_menu_download_center_Frame, image=self.download_img, command=lambda:self.download_item())#, command=download_model)
        self.download_Button.grid(pady=MENU_PADDING_1)
        
        self.download_progress_info_Label = tk.Label(settings_menu_download_center_Frame, textvariable=self.download_progress_info_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_2}"), foreground=FG_COLOR, borderwidth=0)
        self.download_progress_info_Label.grid(pady=MENU_PADDING_1)
        
        self.download_progress_percent_Label = tk.Label(settings_menu_download_center_Frame, textvariable=self.download_progress_percent_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_2}"), wraplength=350, foreground=FG_COLOR)
        self.download_progress_percent_Label.grid(pady=MENU_PADDING_1)
        
        self.download_progress_bar_Progressbar = ttk.Progressbar(settings_menu_download_center_Frame, variable=self.download_progress_bar_var)
        self.download_progress_bar_Progressbar.grid(pady=MENU_PADDING_1)
        
        self.stop_download_Button = ttk.Button(settings_menu_download_center_Frame, textvariable=self.download_stop_var, width=15, command=lambda:self.download_post_action(DOWNLOAD_STOPPED))
        self.stop_download_Button.grid(pady=MENU_PADDING_1)
        self.stop_download_Button_DISABLE = lambda:(self.download_stop_var.set(""), self.stop_download_Button.configure(state=tk.DISABLED))
        self.stop_download_Button_ENABLE = lambda:(self.download_stop_var.set(STOP_DOWNLOAD_TEXT), self.stop_download_Button.configure(state=tk.NORMAL))

        self.refresh_list_Button = ttk.Button(settings_menu_download_center_Frame, text=REFRESH_LIST_TEXT, command=lambda:self.online_data_refresh(refresh_list_Button=True))#, command=refresh_list)
        self.refresh_list_Button.grid(pady=MENU_PADDING_1)
        
        self.download_key_Button = ttk.Button(settings_menu_download_center_Frame, image=self.key_img, command=lambda:self.pop_up_user_code_input())
        self.download_key_Button.grid(pady=MENU_PADDING_1)
                            
        self.manual_download_Button = ttk.Button(settings_menu_download_center_Frame, text=TRY_MANUAL_DOWNLOAD_TEXT, command=self.menu_manual_downloads)
        self.manual_download_Button.grid(pady=MENU_PADDING_1)

        self.download_center_Buttons = (self.model_download_vr_Button,
                                        self.model_download_mdx_Button,
                                        self.model_download_demucs_Button,
                                        self.download_Button,
                                        self.download_key_Button)
        
        self.download_lists = (self.model_download_vr_Option,
                               self.model_download_mdx_Option,
                               self.model_download_demucs_Option)
        
        self.download_list_vars = (self.model_download_vr_var,
                                   self.model_download_mdx_var,
                                   self.model_download_demucs_var)
        
        # Queue moved to main UI

        self.online_data_refresh()

        self.menu_placement(settings_menu, SETTINGS_GUIDE_TEXT, is_help_hints=True, close_function=lambda:close_window())

        if select_tab_2:
            tabControl.select(tab2)
            settings_menu.update_idletasks()
            
        if select_tab_3:
            tabControl.select(tab3)
            settings_menu.update_idletasks()

        def close_window():
            self.active_download_thread.terminate() if self.thread_check(self.active_download_thread) else None
            self.is_menu_settings_open = False
            self.select_download_var.set('')
            settings_menu.destroy()

        #self.update_checkbox_text()
        settings_menu.protocol("WM_DELETE_WINDOW", close_window)

    def menu_advanced_vr_options(self):#**
        """Open Advanced VR Options"""     

        vr_opt = tk.Toplevel()
        
        tab1 = self.menu_tab_control(vr_opt, self.vr_secondary_model_vars)

        self.is_open_menu_advanced_vr_options.set(True)
        self.menu_advanced_vr_options_close_window = lambda:(self.is_open_menu_advanced_vr_options.set(False), vr_opt.destroy())
        vr_opt.protocol("WM_DELETE_WINDOW", self.menu_advanced_vr_options_close_window)
        
        toggle_post_process = lambda:self.post_process_threshold_Option.configure(state=READ_ONLY) if self.is_post_process_var.get() else self.post_process_threshold_Option.configure(state=tk.DISABLED)
        
        vr_opt_frame = self.menu_FRAME_SET(tab1)
        vr_opt_frame.grid(pady=0 if not self.chosen_process_method_var.get() == VR_ARCH_PM else 70)  
        
        vr_title = self.menu_title_LABEL_SET(vr_opt_frame, ADVANCED_VR_OPTIONS_TEXT)
        vr_title.grid(padx=25, pady=MENU_PADDING_2)
  
        if not self.chosen_process_method_var.get() == VR_ARCH_PM:
            window_size_Label = self.menu_sub_LABEL_SET(vr_opt_frame, WINDOW_SIZE_TEXT)
            window_size_Label.grid(pady=MENU_PADDING_1)
            window_size_Option = ComboBoxEditableMenu(vr_opt_frame, values=VR_WINDOW, width=MENU_COMBOBOX_WIDTH, textvariable=self.window_size_var, pattern=REG_WINDOW, default=VR_WINDOW[1])#
            window_size_Option.grid(pady=MENU_PADDING_1)
            self.help_hints(window_size_Label, text=WINDOW_SIZE_HELP)
            
            aggression_setting_Label = self.menu_sub_LABEL_SET(vr_opt_frame, AGGRESSION_SETTING_TEXT)
            aggression_setting_Label.grid(pady=MENU_PADDING_1)
            aggression_setting_Option = ComboBoxEditableMenu(vr_opt_frame, values=VR_AGGRESSION, width=MENU_COMBOBOX_WIDTH, textvariable=self.aggression_setting_var, pattern=REG_AGGRESSION, default=VR_AGGRESSION[5])#
            aggression_setting_Option.grid(pady=MENU_PADDING_1)
            self.help_hints(aggression_setting_Label, text=AGGRESSION_SETTING_HELP)
        
        self.batch_size_Label = self.menu_sub_LABEL_SET(vr_opt_frame, BATCH_SIZE_TEXT)
        self.batch_size_Label.grid(pady=MENU_PADDING_1)
        self.batch_size_Option = ComboBoxEditableMenu(vr_opt_frame, values=BATCH_SIZE, width=MENU_COMBOBOX_WIDTH, textvariable=self.batch_size_var, pattern=REG_BATCHES, default=BATCH_SIZE)#
        self.batch_size_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(self.batch_size_Label, text=BATCH_SIZE_HELP)
        
        self.post_process_threshold_Label = self.menu_sub_LABEL_SET(vr_opt_frame, POST_PROCESS_THRESHOLD_TEXT)
        self.post_process_threshold_Label.grid(pady=MENU_PADDING_1)
        self.post_process_threshold_Option = ComboBoxEditableMenu(vr_opt_frame, values=POST_PROCESSES_THREASHOLD_VALUES, width=MENU_COMBOBOX_WIDTH, textvariable=self.post_process_threshold_var, pattern=REG_THES_POSTPORCESS, default=POST_PROCESSES_THREASHOLD_VALUES[1])#
        self.post_process_threshold_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(self.post_process_threshold_Label, text=POST_PROCESS_THREASHOLD_HELP)
        
        self.is_tta_Option = ttk.Checkbutton(vr_opt_frame, text=ENABLE_TTA_TEXT, width=VR_CHECKBOXS_WIDTH, variable=self.is_tta_var) 
        self.is_tta_Option.grid(pady=0)
        self.help_hints(self.is_tta_Option, text=IS_TTA_HELP)
        
        self.is_post_process_Option = ttk.Checkbutton(vr_opt_frame, text=POST_PROCESS_TEXT, width=VR_CHECKBOXS_WIDTH, variable=self.is_post_process_var, command=toggle_post_process) 
        self.is_post_process_Option.grid(pady=0)
        self.help_hints(self.is_post_process_Option, text=IS_POST_PROCESS_HELP)
        
        self.is_high_end_process_Option = ttk.Checkbutton(vr_opt_frame, text=HIGHEND_PROCESS_TEXT, width=VR_CHECKBOXS_WIDTH, variable=self.is_high_end_process_var) 
        self.is_high_end_process_Option.grid(pady=0)
        self.help_hints(self.is_high_end_process_Option, text=IS_HIGH_END_PROCESS_HELP)
        
        self.vocal_splitter_Button_opt(vr_opt, vr_opt_frame, pady=MENU_PADDING_1, width=VR_BUT_WIDTH)
        
        self.vr_clear_cache_Button = ttk.Button(vr_opt_frame, text=CLEAR_AUTOSET_CACHE_TEXT, command=lambda:self.clear_cache(VR_ARCH_TYPE), width=VR_BUT_WIDTH)
        self.vr_clear_cache_Button.grid(pady=MENU_PADDING_1)
        self.help_hints(self.vr_clear_cache_Button, text=CLEAR_CACHE_HELP)
        
        self.open_vr_model_dir_Button = ttk.Button(vr_opt_frame, text=OPEN_MODELS_FOLDER_TEXT, command=lambda:OPEN_FILE_func(VR_MODELS_DIR), width=VR_BUT_WIDTH)
        self.open_vr_model_dir_Button.grid(pady=MENU_PADDING_1)
        
        self.vr_return_Button=ttk.Button(vr_opt_frame, text=BACK_TO_MAIN_MENU, command=lambda:(self.menu_advanced_vr_options_close_window(), self.check_is_menu_settings_open()))
        self.vr_return_Button.grid(pady=MENU_PADDING_1)

        self.vr_close_Button = ttk.Button(vr_opt_frame, text=CLOSE_WINDOW, command=lambda:self.menu_advanced_vr_options_close_window())
        self.vr_close_Button.grid(pady=MENU_PADDING_1)
        
        toggle_post_process()
        
        frame_list = [vr_opt_frame]
        self.menu_placement(vr_opt, ADVANCED_VR_OPTIONS_TEXT, is_help_hints=True, close_function=self.menu_advanced_vr_options_close_window, frame_list=frame_list)

    def menu_advanced_demucs_options(self):#**
        """Open Advanced Demucs Options"""
        
        demuc_opt = tk.Toplevel()

        self.is_open_menu_advanced_demucs_options.set(True)
        self.menu_advanced_demucs_options_close_window = lambda:(self.is_open_menu_advanced_demucs_options.set(False), demuc_opt.destroy())
        demuc_opt.protocol("WM_DELETE_WINDOW", self.menu_advanced_demucs_options_close_window)

        tab1, tab3 = self.menu_tab_control(demuc_opt, self.demucs_secondary_model_vars, is_demucs=True)
        
        demucs_frame = self.menu_FRAME_SET(tab1)
        demucs_frame.grid(pady=0 if not self.chosen_process_method_var.get() == DEMUCS_ARCH_TYPE else 55)  
        
        demucs_pre_model_frame = self.menu_FRAME_SET(tab3)
        demucs_pre_model_frame.grid(row=0)  
        
        demucs_title_Label = self.menu_title_LABEL_SET(demucs_frame, ADVANCED_DEMUCS_OPTIONS_TEXT)
        demucs_title_Label.grid(pady=MENU_PADDING_2)
        
        if not self.chosen_process_method_var.get() == DEMUCS_ARCH_TYPE:
            segment_Label = self.menu_sub_LABEL_SET(demucs_frame, SEGMENTS_TEXT)
            segment_Label.grid(pady=MENU_PADDING_2)
            segment_Option = ComboBoxEditableMenu(demucs_frame, values=DEMUCS_SEGMENTS, width=MENU_COMBOBOX_WIDTH, textvariable=self.segment_var, pattern=REG_SEGMENTS, default=DEMUCS_SEGMENTS)#
            segment_Option.grid()
            self.help_hints(segment_Label, text=SEGMENT_HELP)
        
        self.shifts_Label = self.menu_sub_LABEL_SET(demucs_frame, SHIFTS_TEXT)
        self.shifts_Label.grid(pady=MENU_PADDING_1)
        self.shifts_Option = ComboBoxEditableMenu(demucs_frame, values=DEMUCS_SHIFTS, width=MENU_COMBOBOX_WIDTH, textvariable=self.shifts_var, pattern=REG_SHIFTS, default=DEMUCS_SHIFTS[2])#
        self.shifts_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(self.shifts_Label, text=SHIFTS_HELP)

        self.overlap_Label = self.menu_sub_LABEL_SET(demucs_frame, OVERLAP_TEXT)
        self.overlap_Label.grid(pady=MENU_PADDING_1)
        self.overlap_Option = ComboBoxEditableMenu(demucs_frame, values=DEMUCS_OVERLAP, width=MENU_COMBOBOX_WIDTH, textvariable=self.overlap_var, pattern=REG_OVERLAP, default=DEMUCS_OVERLAP)#
        self.overlap_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(self.overlap_Label, text=OVERLAP_HELP)

        pitch_shift_Label = self.menu_sub_LABEL_SET(demucs_frame, SHIFT_CONVERSION_PITCH_TEXT)
        pitch_shift_Label.grid(pady=MENU_PADDING_1)
        pitch_shift_Option = ComboBoxEditableMenu(demucs_frame, values=SEMITONE_SEL, width=MENU_COMBOBOX_WIDTH, textvariable=self.semitone_shift_var, pattern=REG_SEMITONES, default=SEMI_DEF)#
        pitch_shift_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(pitch_shift_Label, text=PITCH_SHIFT_HELP)

        self.is_split_mode_Option = ttk.Checkbutton(demucs_frame, text=SPLIT_MODE_TEXT, width=DEMUCS_CHECKBOXS_WIDTH, variable=self.is_split_mode_var) 
        self.is_split_mode_Option.grid()
        self.help_hints(self.is_split_mode_Option, text=IS_SPLIT_MODE_HELP)
        
        self.is_demucs_combine_stems_Option = ttk.Checkbutton(demucs_frame, text=COMBINE_STEMS_TEXT, width=DEMUCS_CHECKBOXS_WIDTH, variable=self.is_demucs_combine_stems_var) 
        self.is_demucs_combine_stems_Option.grid()
        self.help_hints(self.is_demucs_combine_stems_Option, text=IS_DEMUCS_COMBINE_STEMS_HELP)
        
        is_invert_spec_Option = ttk.Checkbutton(demucs_frame, text=SPECTRAL_INVERSION_TEXT, width=DEMUCS_CHECKBOXS_WIDTH, variable=self.is_invert_spec_var) 
        is_invert_spec_Option.grid()
        self.help_hints(is_invert_spec_Option, text=IS_INVERT_SPEC_HELP)
        
        is_demucs_tta_Option = ttk.Checkbutton(demucs_frame, text=ENABLE_TTA_TEXT, width=DEMUCS_CHECKBOXS_WIDTH, variable=self.is_demucs_tta_var) 
        is_demucs_tta_Option.grid()
        self.help_hints(is_demucs_tta_Option, text=IS_TTA_HELP)
        
        self.vocal_splitter_Button_opt(demuc_opt, demucs_frame, width=VR_BUT_WIDTH, pady=MENU_PADDING_1)
        
        self.open_demucs_model_dir_Button = ttk.Button(demucs_frame, text=OPEN_MODELS_FOLDER_TEXT, command=lambda:OPEN_FILE_func(DEMUCS_MODELS_DIR), width=VR_BUT_WIDTH)
        self.open_demucs_model_dir_Button.grid(pady=MENU_PADDING_1)
        
        self.demucs_return_Button = ttk.Button(demucs_frame, text=BACK_TO_MAIN_MENU, command=lambda:(self.menu_advanced_demucs_options_close_window(), self.check_is_menu_settings_open()))
        self.demucs_return_Button.grid(pady=MENU_PADDING_1)
        
        self.demucs_close_Button = ttk.Button(demucs_frame, text=CLOSE_WINDOW, command=lambda:self.menu_advanced_demucs_options_close_window())
        self.demucs_close_Button.grid(pady=MENU_PADDING_1)
        
        frame_list = [demucs_pre_model_frame, demucs_frame]
        self.menu_placement(demuc_opt, ADVANCED_DEMUCS_OPTIONS_TEXT, is_help_hints=True, close_function=self.menu_advanced_demucs_options_close_window, frame_list=frame_list)
        
    def menu_advanced_mdx_options(self):#**
        """Open Advanced MDX Options"""

        mdx_net_opt = tk.Toplevel()

        self.is_open_menu_advanced_mdx_options.set(True)
        self.menu_advanced_mdx_options_close_window = lambda:(self.is_open_menu_advanced_mdx_options.set(False), mdx_net_opt.destroy())
        mdx_net_opt.protocol("WM_DELETE_WINDOW", self.menu_advanced_mdx_options_close_window)

        tab1, tab3 = self.menu_tab_control(mdx_net_opt, self.mdx_secondary_model_vars, is_mdxnet=True)
        
        mdx_net_frame = self.menu_FRAME_SET(tab1)
        mdx_net_frame.grid(pady=0)  

        mdx_net23_frame = self.menu_FRAME_SET(tab3)
        mdx_net23_frame.grid(pady=0)

        mdx_opt_title = self.menu_title_LABEL_SET(mdx_net_frame, ADVANCED_MDXNET_OPTIONS_TEXT)
        mdx_opt_title.grid(pady=MENU_PADDING_1)
        
        compensate_Label = self.menu_sub_LABEL_SET(mdx_net_frame, VOLUME_COMPENSATION_TEXT)
        compensate_Label.grid(pady=MENU_PADDING_4)
        compensate_Option = ComboBoxEditableMenu(mdx_net_frame, values=VOL_COMPENSATION, width=MENU_COMBOBOX_WIDTH, textvariable=self.compensate_var, pattern=REG_COMPENSATION, default=VOL_COMPENSATION)#
        compensate_Option.grid(pady=MENU_PADDING_4)
        self.help_hints(compensate_Label, text=COMPENSATE_HELP)

        mdx_segment_size_Label = self.menu_sub_LABEL_SET(mdx_net_frame, SEGMENT_SIZE_TEXT)
        mdx_segment_size_Label.grid(pady=MENU_PADDING_4)
        mdx_segment_size_Option = ComboBoxEditableMenu(mdx_net_frame, values=MDX_SEGMENTS, width=MENU_COMBOBOX_WIDTH, textvariable=self.mdx_segment_size_var, pattern=REG_MDX_SEG, default="Default")#
        mdx_segment_size_Option.grid(pady=MENU_PADDING_4)
        self.help_hints(mdx_segment_size_Label, text=MDX_SEGMENT_SIZE_HELP)

        overlap_mdx_Label = self.menu_sub_LABEL_SET(mdx_net_frame, OVERLAP_TEXT)
        overlap_mdx_Label.grid(pady=MENU_PADDING_4)
        overlap_mdx_Option = ComboBoxEditableMenu(mdx_net_frame, values=MDX_OVERLAP, width=MENU_COMBOBOX_WIDTH, textvariable=self.overlap_mdx_var, pattern=REG_OVERLAP, default=MDX_OVERLAP)#
        overlap_mdx_Option.grid(pady=MENU_PADDING_4)
        self.help_hints(overlap_mdx_Label, text=OVERLAP_HELP)

        pitch_shift_Label = self.menu_sub_LABEL_SET(mdx_net_frame, SHIFT_CONVERSION_PITCH_TEXT)
        pitch_shift_Label.grid(pady=MENU_PADDING_4)
        pitch_shift_Option = ComboBoxEditableMenu(mdx_net_frame, values=SEMITONE_SEL, width=MENU_COMBOBOX_WIDTH, textvariable=self.semitone_shift_var, pattern=REG_SEMITONES, default=SEMI_DEF)#
        pitch_shift_Option.grid(pady=MENU_PADDING_4)
        self.help_hints(pitch_shift_Label, text=PITCH_SHIFT_HELP)
        
        if not os.path.isfile(DENOISER_MODEL_PATH):
            denoise_options_var_text = self.denoise_option_var.get()
            denoise_options = [option for option in MDX_DENOISE_OPTION if option != DENOISE_M]
            self.denoise_option_var.set(DENOISE_S if denoise_options_var_text == DENOISE_M else denoise_options_var_text)
        else:
            denoise_options = MDX_DENOISE_OPTION
            
        denoise_option_Label = self.menu_sub_LABEL_SET(mdx_net_frame, DENOISE_OUTPUT_TEXT)
        denoise_option_Label.grid(pady=MENU_PADDING_4)
        denoise_option_Option = ComboBoxMenu(mdx_net_frame, textvariable=self.denoise_option_var, values=denoise_options, width=MENU_COMBOBOX_WIDTH)
        denoise_option_Option.grid(pady=MENU_PADDING_4)
        self.help_hints(denoise_option_Label, text=IS_DENOISE_HELP)

        is_match_frequency_pitch_Option = ttk.Checkbutton(mdx_net_frame, text=MATCH_FREQ_CUTOFF_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_match_frequency_pitch_var) 
        is_match_frequency_pitch_Option.grid(pady=0)
        self.help_hints(is_match_frequency_pitch_Option, text=IS_FREQUENCY_MATCH_HELP)

        is_invert_spec_Option = ttk.Checkbutton(mdx_net_frame, text=SPECTRAL_INVERSION_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_invert_spec_var) 
        is_invert_spec_Option.grid(pady=0)
        self.help_hints(is_invert_spec_Option, text=IS_INVERT_SPEC_HELP)
        
        is_mdx_tta_Option = ttk.Checkbutton(mdx_net_frame, text=ENABLE_TTA_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_mdx_tta_var) 
        is_mdx_tta_Option.grid(pady=0)
        self.help_hints(is_mdx_tta_Option, text=IS_TTA_HELP)
        
        self.vocal_splitter_Button_opt(mdx_net_opt, mdx_net_frame, pady=MENU_PADDING_1, width=VR_BUT_WIDTH)

        clear_mdx_cache_Button = ttk.Button(mdx_net_frame, text=CLEAR_AUTOSET_CACHE_TEXT, command=lambda:self.clear_cache(MDX_ARCH_TYPE), width=VR_BUT_WIDTH)
        clear_mdx_cache_Button.grid(pady=MENU_PADDING_1)
        self.help_hints(clear_mdx_cache_Button, text=CLEAR_CACHE_HELP)
        
        open_mdx_model_dir_Button = ttk.Button(mdx_net_frame, text=OPEN_MODELS_FOLDER_TEXT, command=lambda:OPEN_FILE_func(MDX_MODELS_DIR), width=VR_BUT_WIDTH)
        open_mdx_model_dir_Button.grid(pady=MENU_PADDING_1)
        
        mdx_return_Button = ttk.Button(mdx_net_frame, text=BACK_TO_MAIN_MENU, command=lambda:(self.menu_advanced_mdx_options_close_window(), self.check_is_menu_settings_open()))
        mdx_return_Button.grid(pady=MENU_PADDING_1)

        mdx_close_Button = ttk.Button(mdx_net_frame, text=CLOSE_WINDOW, command=lambda:self.menu_advanced_mdx_options_close_window())
        mdx_close_Button.grid(pady=MENU_PADDING_1)
        
        mdx23_opt_title = self.menu_title_LABEL_SET(mdx_net23_frame, ADVANCED_MDXNET23_OPTIONS_TEXT)
        mdx23_opt_title.grid(pady=MENU_PADDING_2)
        
        mdx_batch_size_Label = self.menu_sub_LABEL_SET(mdx_net23_frame, BATCH_SIZE_TEXT)
        mdx_batch_size_Label.grid(pady=MENU_PADDING_1)
        mdx_batch_size_Option = ComboBoxEditableMenu(mdx_net23_frame, values=BATCH_SIZE, width=MENU_COMBOBOX_WIDTH, textvariable=self.mdx_batch_size_var, pattern=REG_BATCHES, default=BATCH_SIZE)#
        mdx_batch_size_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(mdx_batch_size_Label, text=BATCH_SIZE_HELP)
        
        overlap_mdx23_Label = self.menu_sub_LABEL_SET(mdx_net23_frame, OVERLAP_TEXT)
        overlap_mdx23_Label.grid(pady=MENU_PADDING_1)
        overlap_mdx23_Option = ComboBoxEditableMenu(mdx_net23_frame, values=MDX23_OVERLAP, width=MENU_COMBOBOX_WIDTH, textvariable=self.overlap_mdx23_var, pattern=REG_OVERLAP23, default="8")#
        overlap_mdx23_Option.grid(pady=MENU_PADDING_1)
        self.help_hints(overlap_mdx23_Label, text=OVERLAP_23_HELP)
        
        # Segment Default Checkbox has been removed and integrated into MDX_SEGMENTS ComboBox
        
        is_mdx_combine_stems_Option = ttk.Checkbutton(mdx_net23_frame, text=COMBINE_STEMS_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_mdx23_combine_stems_var)
        is_mdx_combine_stems_Option.grid()
        self.help_hints(is_mdx_combine_stems_Option, text=IS_DEMUCS_COMBINE_STEMS_HELP)
        
        mdx23_close_Button = ttk.Button(mdx_net23_frame, text=CLOSE_WINDOW, command=lambda:self.menu_advanced_mdx_options_close_window())
        mdx23_close_Button.grid(pady=MENU_PADDING_2)
        
        frame_list = [mdx_net_frame, mdx_net23_frame]
        self.menu_placement(mdx_net_opt, ADVANCED_MDXNET_OPTIONS_TEXT, is_help_hints=True, close_function=self.menu_advanced_mdx_options_close_window, frame_list=frame_list)

    def menu_advanced_ensemble_options(self):#**
        """Open Ensemble Custom"""
        
        custom_ens_opt = tk.Toplevel()
        
        self.is_open_menu_advanced_ensemble_options.set(True)
        self.menu_advanced_ensemble_options_close_window = lambda:(self.is_open_menu_advanced_ensemble_options.set(False), custom_ens_opt.destroy())
        custom_ens_opt.protocol("WM_DELETE_WINDOW", self.menu_advanced_ensemble_options_close_window)

        option_var = tk.StringVar(value=SELECT_SAVED_ENSEMBLE)

        custom_ens_opt_frame = self.menu_FRAME_SET(custom_ens_opt)
        custom_ens_opt_frame.grid(row=0)  
        
        settings_title_Label = self.menu_title_LABEL_SET(custom_ens_opt_frame, ADVANCED_OPTION_MENU_TEXT)
        settings_title_Label.grid(pady=MENU_PADDING_2)
        
        delete_entry_Label = self.menu_sub_LABEL_SET(custom_ens_opt_frame, REMOVE_SAVED_ENSEMBLE_TEXT)
        delete_entry_Label.grid(pady=MENU_PADDING_1)
        delete_entry_Option = ComboBoxMenu(custom_ens_opt_frame, textvariable=option_var, width=ENSEMBLE_CHECKBOXS_WIDTH+2)
        delete_entry_Option.grid(padx=20,pady=MENU_PADDING_1)
        
        is_save_all_outputs_ensemble_Option = ttk.Checkbutton(custom_ens_opt_frame, text=SAVE_ALL_OUTPUTS_TEXT, width=ENSEMBLE_CHECKBOXS_WIDTH, variable=self.is_save_all_outputs_ensemble_var)
        is_save_all_outputs_ensemble_Option.grid(pady=0)
        self.help_hints(is_save_all_outputs_ensemble_Option, text=IS_SAVE_ALL_OUTPUTS_ENSEMBLE_HELP)

        is_append_ensemble_name_Option = ttk.Checkbutton(custom_ens_opt_frame, text=APPEND_ENSEMBLE_NAME_TEXT, width=ENSEMBLE_CHECKBOXS_WIDTH, variable=self.is_append_ensemble_name_var) 
        is_append_ensemble_name_Option.grid(pady=0)
        self.help_hints(is_append_ensemble_name_Option, text=IS_APPEND_ENSEMBLE_NAME_HELP)

        is_wav_ensemble_Option = ttk.Checkbutton(custom_ens_opt_frame, text=ENSEMBLE_WAVFORMS_TEXT, width=ENSEMBLE_CHECKBOXS_WIDTH, variable=self.is_wav_ensemble_var) 
        is_wav_ensemble_Option.grid(pady=0)
        self.help_hints(is_wav_ensemble_Option, text=IS_WAV_ENSEMBLE_HELP)

        ensemble_return_Button = ttk.Button(custom_ens_opt_frame, text=BACK_TO_MAIN_MENU, command=lambda:(self.menu_advanced_ensemble_options_close_window(), self.check_is_menu_settings_open()))
        ensemble_return_Button.grid(pady=MENU_PADDING_1)
        
        ensemble_close_Button = ttk.Button(custom_ens_opt_frame, text=CLOSE_WINDOW, command=lambda:self.menu_advanced_ensemble_options_close_window())
        ensemble_close_Button.grid(pady=MENU_PADDING_1)
        
        self.deletion_list_fill(delete_entry_Option, option_var, ENSEMBLE_CACHE_DIR, SELECT_SAVED_ENSEMBLE, menu_name='deleteensemble')
        
        self.menu_placement(custom_ens_opt, ADVANCED_ENSEMBLE_OPTIONS_TEXT, is_help_hints=True, close_function=self.menu_advanced_ensemble_options_close_window)

    def menu_advanced_align_options(self):#**
        """Open Ensemble Custom"""
        
        advanced_align_opt = tk.Toplevel()
        
        self.is_open_menu_advanced_align_options.set(True)
        self.menu_advanced_align_options_close_window = lambda:(self.is_open_menu_advanced_align_options.set(False), advanced_align_opt.destroy())
        advanced_align_opt.protocol("WM_DELETE_WINDOW", self.menu_advanced_align_options_close_window)

        advanced_align_opt_frame = self.menu_FRAME_SET(advanced_align_opt)
        advanced_align_opt_frame.grid(row=0)  
        
        settings_title_Label = self.menu_title_LABEL_SET(advanced_align_opt_frame, ADVANCED_ALIGN_TOOL_OPTIONS_TEXT)
        settings_title_Label.grid(pady=MENU_PADDING_2)
        
        phase_option_Label = self.menu_sub_LABEL_SET(advanced_align_opt_frame, SECONDARY_PHASE_TEXT)
        phase_option_Label.grid(pady=4)
        phase_option_Option = ComboBoxMenu(advanced_align_opt_frame, textvariable=self.phase_option_var, values=ALIGN_PHASE_OPTIONS, width=MENU_COMBOBOX_WIDTH)
        phase_option_Option.grid(pady=4)
        self.help_hints(phase_option_Label, text=IS_PHASE_HELP)
        
        phase_shifts_Label = self.menu_sub_LABEL_SET(advanced_align_opt_frame, PHASE_SHIFTS_TEXT)
        phase_shifts_Label.grid(pady=4)#
        phase_shifts_Option = ComboBoxMenu(advanced_align_opt_frame, textvariable=self.phase_shifts_var, values=list(PHASE_SHIFTS_OPT.keys()), width=MENU_COMBOBOX_WIDTH)
        phase_shifts_Option.grid(pady=4)
        self.help_hints(phase_shifts_Label, text=PHASE_SHIFTS_ALIGN_HELP)
        
        is_save_align_Option = ttk.Checkbutton(advanced_align_opt_frame, text=SAVE_ALIGNED_TRACK_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_save_align_var)
        is_save_align_Option.grid(pady=0)
        self.help_hints(is_save_align_Option, text=IS_ALIGN_TRACK_HELP)
        
        is_match_silence_Option = ttk.Checkbutton(advanced_align_opt_frame, text=SILENCE_MATCHING_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_match_silence_var)
        is_match_silence_Option.grid(pady=0)
        self.help_hints(is_match_silence_Option, text=IS_MATCH_SILENCE_HELP)

        is_spec_match_Option = ttk.Checkbutton(advanced_align_opt_frame, text=SPECTRAL_MATCHING_TEXT, width=MDX_CHECKBOXS_WIDTH, variable=self.is_spec_match_var)
        is_spec_match_Option.grid(pady=0)
        self.help_hints(is_spec_match_Option, text=IS_MATCH_SPEC_HELP)

        ensemble_return_Button = ttk.Button(advanced_align_opt_frame, text=BACK_TO_MAIN_MENU, command=lambda:(self.menu_advanced_align_options_close_window(), self.check_is_menu_settings_open()))
        ensemble_return_Button.grid(pady=MENU_PADDING_1)
        
        ensemble_close_Button = ttk.Button(advanced_align_opt_frame, text=CLOSE_WINDOW, command=lambda:self.menu_advanced_align_options_close_window())
        ensemble_close_Button.grid(pady=MENU_PADDING_1)
        
        self.menu_placement(advanced_align_opt, ADVANCED_ALIGN_TOOL_OPTIONS_TEXT, is_help_hints=True, close_function=self.menu_advanced_align_options_close_window)
 
    def menu_help(self):#**
        """Open Help Guide"""
        
        help_guide_opt = tk.Toplevel()

        self.is_open_menu_help.set(True)
        self.menu_help_close_window = lambda:(self.is_open_menu_help.set(False), help_guide_opt.destroy())
        help_guide_opt.protocol("WM_DELETE_WINDOW", self.menu_help_close_window)
        
        tabControl = ttk.Notebook(help_guide_opt)

        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        tab4 = ttk.Frame(tabControl)

        tabControl.add(tab1, text ='Credits')
        tabControl.add(tab2, text ='Resources')
        tabControl.add(tab3, text ='Application License & Version Information')
        tabControl.add(tab4, text ='Additional Information')

        tabControl.pack(expand = 1, fill ="both")
        
        tab1.grid_rowconfigure(0, weight=1)
        tab1.grid_columnconfigure(0, weight=1)
        
        tab2.grid_rowconfigure(0, weight=1)
        tab2.grid_columnconfigure(0, weight=1)
        
        tab3.grid_rowconfigure(0, weight=1)
        tab3.grid_columnconfigure(0, weight=1)
        
        tab4.grid_rowconfigure(0, weight=1)
        tab4.grid_columnconfigure(0, weight=1)
        
        section_title_Label = lambda place, frame, text, font_size=FONT_SIZE_4: tk.Label(master=frame, text=text,font=(MAIN_FONT_NAME, f"{font_size}", "bold"), justify="center", fg="#F4F4F4").grid(row=place,column=0,padx=0,pady=MENU_PADDING_4)
        description_Label = lambda place, frame, text, font=FONT_SIZE_2: tk.Label(master=frame, text=text, font=(MAIN_FONT_NAME, f"{font}"), justify="center", fg="#F6F6F7").grid(row=place,column=0,padx=0,pady=MENU_PADDING_4)

        def credit_label(place, frame, text, link=None, message=None, is_link=False, is_top=False):
            if is_top:
                thank = tk.Label(master=frame, text=text, font=(MAIN_FONT_NAME, f"{FONT_SIZE_3}", "bold"), justify="center", fg="#13849f")
            else:
                thank = tk.Label(master=frame, text=text, font=(MAIN_FONT_NAME, f"{FONT_SIZE_3}", "underline" if is_link else "normal"), justify="center", fg="#13849f")
            thank.configure(cursor="hand2") if is_link else None
            thank.grid(row=place,column=0,padx=0,pady=1)
            if link:
                thank.bind("<Button-1>", lambda e:webbrowser.open_new_tab(link))
            if message:
                description_Label(place+1, frame, message)
        
        def Link(place, frame, text, link, description, font=FONT_SIZE_2): 
            link_label = tk.Label(master=frame, text=text, font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}", "underline"), foreground=FG_COLOR, justify="center", cursor="hand2")
            link_label.grid(row=place,column=0,padx=0,pady=MENU_PADDING_1)
            link_label.bind("<Button-1>", lambda e:webbrowser.open_new_tab(link))
            description_Label(place+1, frame, description, font=font)

        def right_click_menu(event):
                right_click_menu = tk.Menu(self, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
                right_click_menu.add_command(label='Return to Settings Menu', command=lambda:(self.menu_help_close_window(), self.check_is_menu_settings_open()))
                right_click_menu.add_command(label='Exit Window', command=lambda:self.menu_help_close_window())
                
                try:
                    right_click_menu.tk_popup(event.x_root,event.y_root)
                    right_click_release_linux(right_click_menu, help_guide_opt)
                finally:
                    right_click_menu.grab_release()

        help_guide_opt.bind(right_click_button, lambda e:right_click_menu(e))
        credits_Frame = tk.Frame(tab1, highlightthicknes=50)
        credits_Frame.grid(row=0, column=0, padx=0, pady=0)
        tk.Label(credits_Frame, image=self.credits_img).grid(row=1,column=0,padx=0,pady=MENU_PADDING_1)

        section_title_Label(place=0,
                            frame=credits_Frame,
                            text="Core UVR Developers")
        
        credit_label(place=2,
                     frame=credits_Frame,
                     text="Anjok07\nAufr33",
                     is_top=True)
        
        section_title_Label(place=3,
                            frame=credits_Frame,
                            text="Special Thanks")
        
        credit_label(place=6,
                     frame=credits_Frame,
                     text="Tsurumeso",
                     message="Developed the original VR Architecture AI code.",
                     link="https://github.com/tsurumeso/vocal-remover",
                     is_link=True)
        
        credit_label(place=8,
                     frame=credits_Frame,
                     text="Kuielab & Woosung Choi",
                     message="Developed the original MDX-Net AI code.",
                     link="https://github.com/kuielab",
                     is_link=True)
        
        credit_label(place=10,
                     frame=credits_Frame,
                     text="Adefossez & Demucs",
                     message="Core developer of Facebook's Demucs Music Source Separation.",
                     link="https://github.com/facebookresearch/demucs",
                     is_link=True)
        
        credit_label(place=12,
                     frame=credits_Frame,
                     text="Bas Curtiz",
                     message="Designed the official UVR logo, icon, banner, splash screen.")
        
        credit_label(place=14,
                     frame=credits_Frame,
                     text="DilanBoskan",
                     message="Your contributions at the start of this project were essential to the success of UVR. Thank you!")
        
        credit_label(place=16,
                     frame=credits_Frame,
                     text="Audio Separation and CC Karaoke & Friends Discord Communities",
                     message="Thank you for the support!")

        more_info_tab_Frame = tk.Frame(tab2, highlightthicknes=30)
        more_info_tab_Frame.grid(row=0,column=0,padx=0,pady=0)

        section_title_Label(place=3, 
                            frame=more_info_tab_Frame, 
                            text="Resources")

        Link(place=4, 
             frame=more_info_tab_Frame, 
             text="Ultimate Vocal Remover (Official GitHub)", 
             link="https://github.com/Anjok07/ultimatevocalremovergui", 
             description="You can find updates, report issues, and give us a shout via our official GitHub.",
             font=FONT_SIZE_1)
        
        Link(place=8, 
             frame=more_info_tab_Frame, 
             text="X-Minus AI", 
             link="https://x-minus.pro/ai", 
             description="Many of the models provided are also on X-Minus.\n" + \
                         "X-Minus benefits users without the computing resources to run the GUI or models locally.",
             font=FONT_SIZE_1)
        
        Link(place=12, 
             frame=more_info_tab_Frame, 
             text="MVSep", 
             link="https://mvsep.com/quality_checker/leaderboard.php", 
             description="Some of our models are also on MVSep.\n" + \
                         "Click the link above for a list of some of the best settings \nand model combinations recorded by fellow UVR users.\nSpecial thanks to ZFTurbo for all his work on MVSep!",
             font=FONT_SIZE_1)
        
        Link(place=18, 
             frame=more_info_tab_Frame, 
             text="FFmpeg", 
             link="https://www.wikihow.com/Install-FFmpeg-on-Windows", 
             description="UVR relies on FFmpeg for processing non-wav audio files.\n" + \
                         "If you are missing FFmpeg, please see the installation guide via the link provided.",
             font=FONT_SIZE_1)
        
        Link(place=22, 
             frame=more_info_tab_Frame, 
             text="Rubber Band Library", 
             link="https://breakfastquay.com/rubberband/",
             description="UVR uses the Rubber Band library for the sound stretch and pitch shift tool.\n" + \
                         "You can get more information on it via the link provided.",
             font=FONT_SIZE_1)
        
        Link(place=26, 
             frame=more_info_tab_Frame, 
             text="Matchering", 
             link="https://github.com/sergree/matchering",
             description="UVR uses the Matchering library for the \"Matchering\" Audio Tool.\n" + \
                         "You can get more information on it via the link provided.",
             font=FONT_SIZE_1)
        
        Link(place=30, 
             frame=more_info_tab_Frame, 
             text="Official UVR BMAC", 
             link=DONATE_LINK_BMAC, 
             description="If you wish to support and donate to this project, click the link above!",
             font=FONT_SIZE_1)
        
        appplication_license_tab_Frame = tk.Frame(tab3)
        appplication_license_tab_Frame.grid(row=0,column=0,padx=0,pady=0)
        
        appplication_license_Label = tk.Label(appplication_license_tab_Frame, text='UVR License Information', font=(MAIN_FONT_NAME, f"{FONT_SIZE_6}", "bold"), justify="center", fg="#f4f4f4")
        appplication_license_Label.grid(row=0,column=0,padx=0,pady=25)
        
        appplication_license_Text = tk.Text(appplication_license_tab_Frame, font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}"), fg="white", bg="black", width=72, wrap=tk.WORD, borderwidth=0)
        appplication_license_Text.grid(row=1,column=0,padx=0,pady=0)
        appplication_license_Text_scroll = ttk.Scrollbar(appplication_license_tab_Frame, orient=tk.VERTICAL)
        appplication_license_Text.config(yscrollcommand=appplication_license_Text_scroll.set)
        appplication_license_Text_scroll.configure(command=appplication_license_Text.yview)
        appplication_license_Text.grid(row=4,sticky=tk.W)
        appplication_license_Text_scroll.grid(row=4, column=1, sticky=tk.NS)
        appplication_license_Text.insert("insert", LICENSE_TEXT(VERSION, current_patch))
        appplication_license_Text.configure(state=tk.DISABLED)
        
        application_change_log_tab_Frame = tk.Frame(tab4)
        application_change_log_tab_Frame.grid(row=0,column=0,padx=0,pady=0)

        application_change_log_Label = tk.Label(application_change_log_tab_Frame, text='Additional Information', font=(MAIN_FONT_NAME, f"{FONT_SIZE_6}", "bold"), justify="center", fg="#f4f4f4")
        application_change_log_Label.grid(row=0,column=0,padx=0,pady=25)
        
        application_change_log_Text = tk.Text(application_change_log_tab_Frame, font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}"), fg="white", bg="black", width=72, wrap=tk.WORD, borderwidth=0)
        application_change_log_Text.grid(row=1,column=0,padx=40 if is_macos else 30,pady=0)
        application_change_log_Text_scroll = ttk.Scrollbar(application_change_log_tab_Frame, orient=tk.VERTICAL)
        application_change_log_Text.config(yscrollcommand=application_change_log_Text_scroll.set)
        application_change_log_Text_scroll.configure(command=application_change_log_Text.yview)
        application_change_log_Text.grid(row=4,sticky=tk.W)
        application_change_log_Text_scroll.grid(row=4, column=1, sticky=tk.NS)
        application_change_log_Text.insert("insert", self.bulletin_data)
        auto_hyperlink(application_change_log_Text)
        application_change_log_Text.configure(state=tk.DISABLED)

        self.menu_placement(help_guide_opt, "Information Guide")

    def menu_error_log(self):#
        """Open Error Log"""

        self.is_confirm_error_var.set(False)
        
        copied_var = tk.StringVar(value='')
        error_log_screen = tk.Toplevel()
        
        self.is_open_menu_error_log.set(True)
        self.menu_error_log_close_window = lambda:(self.is_open_menu_error_log.set(False), error_log_screen.destroy())
        error_log_screen.protocol("WM_DELETE_WINDOW", self.menu_error_log_close_window)
        
        error_log_frame = self.menu_FRAME_SET(error_log_screen)
        error_log_frame.grid(row=0)  
        
        error_consol_title_Label = self.menu_title_LABEL_SET(error_log_frame, ERROR_CONSOLE_TEXT)
        error_consol_title_Label.grid(row=1,column=0,padx=20,pady=MENU_PADDING_2)
        
        error_details_Text = tk.Text(error_log_frame, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), fg="#D37B7B", bg="black", width=110, wrap=tk.WORD, borderwidth=0)
        error_details_Text.grid(row=2,column=0,padx=0,pady=0)
        error_details_Text.insert("insert", self.error_log_var.get())
        error_details_Text.bind(right_click_button, lambda e:self.right_click_menu_popup(e, text_box=True))
        self.current_text_box = error_details_Text
        error_details_Text_scroll = ttk.Scrollbar(error_log_frame, orient=tk.VERTICAL)
        error_details_Text.config(yscrollcommand=error_details_Text_scroll.set)
        error_details_Text_scroll.configure(command=error_details_Text.yview)
        error_details_Text.grid(row=2,sticky=tk.W)
        error_details_Text_scroll.grid(row=2, column=1, sticky=tk.NS)

        copy_text_Label = tk.Label(error_log_frame, textvariable=copied_var, font=(MAIN_FONT_NAME,  f"{FONT_SIZE_0}"), justify="center", fg="#f4f4f4")
        copy_text_Label.grid(padx=20,pady=0)
        
        copy_text_Button = ttk.Button(error_log_frame, text=COPY_ALL_TEXT_TEXT, width=14, command=lambda:(pyperclip.copy(error_details_Text.get(1.0, tk.END+"-1c")), copied_var.set('Copied!')))
        copy_text_Button.grid(padx=20,pady=MENU_PADDING_1)
        
        report_issue_Button = ttk.Button(error_log_frame, text=REPORT_ISSUE_TEXT, width=14, command=lambda:webbrowser.open_new_tab(ISSUE_LINK))
        report_issue_Button.grid(padx=20,pady=MENU_PADDING_1)

        error_log_return_Button = ttk.Button(error_log_frame, text=BACK_TO_MAIN_MENU, command=lambda:(self.menu_error_log_close_window(), self.menu_settings()))
        error_log_return_Button.grid(padx=20,pady=MENU_PADDING_1)
        
        error_log_close_Button = ttk.Button(error_log_frame, text=CLOSE_WINDOW, command=lambda:self.menu_error_log_close_window())
        error_log_close_Button.grid(padx=20,pady=MENU_PADDING_1)
        
        self.menu_placement(error_log_screen, UVR_ERROR_LOG_TEXT)

    def menu_secondary_model(self, tab, ai_network_vars: dict):
        
        #Settings Tab 1
        secondary_model_Frame = self.menu_FRAME_SET(tab)
        secondary_model_Frame.grid(row=0)  
        
        settings_title_Label = self.menu_title_LABEL_SET(secondary_model_Frame, SECONDARY_MODEL_TEXT)
        settings_title_Label.grid(row=0,column=0,padx=0,pady=MENU_PADDING_3)
        
        voc_inst_list = self.model_list(VOCAL_STEM, INST_STEM, is_dry_check=True)
        other_list = self.model_list(OTHER_STEM, NO_OTHER_STEM, is_dry_check=True)
        bass_list = self.model_list(BASS_STEM, NO_BASS_STEM, is_dry_check=True)
        drum_list = self.model_list(DRUM_STEM, NO_DRUM_STEM, is_dry_check=True)
        
        voc_inst_secondary_model_var = ai_network_vars["voc_inst_secondary_model"]
        other_secondary_model_var = ai_network_vars["other_secondary_model"]
        bass_secondary_model_var = ai_network_vars["bass_secondary_model"]
        drums_secondary_model_var = ai_network_vars["drums_secondary_model"]
        voc_inst_secondary_model_scale_var = ai_network_vars['voc_inst_secondary_model_scale']
        other_secondary_model_scale_var = ai_network_vars['other_secondary_model_scale']
        bass_secondary_model_scale_var = ai_network_vars['bass_secondary_model_scale']
        drums_secondary_model_scale_var = ai_network_vars['drums_secondary_model_scale']
        is_secondary_model_activate_var = ai_network_vars["is_secondary_model_activate"]
        
        change_state_lambda = lambda:change_state(tk.NORMAL if is_secondary_model_activate_var.get() else tk.DISABLED)
        init_convert_to_percentage = lambda raw_value:f"{int(float(raw_value)*100)}%"
        
        voc_inst_secondary_model_scale_LABEL_var = tk.StringVar(value=init_convert_to_percentage(voc_inst_secondary_model_scale_var.get()))
        other_secondary_model_scale_LABEL_var = tk.StringVar(value=init_convert_to_percentage(other_secondary_model_scale_var.get()))
        bass_secondary_model_scale_LABEL_var = tk.StringVar(value=init_convert_to_percentage(bass_secondary_model_scale_var.get()))
        drums_secondary_model_scale_LABEL_var = tk.StringVar(value=init_convert_to_percentage(drums_secondary_model_scale_var.get()))

        def change_state(change_state):
            for child_widget in secondary_model_Frame.winfo_children():
                if type(child_widget) is ComboBoxMenu:
                    change_state = READ_ONLY if change_state == tk.NORMAL else change_state
                    child_widget.configure(state=change_state)
                elif type(child_widget) is ttk.Scale:
                    child_widget.configure(state=change_state)
        
        def convert_to_percentage(raw_value, scale_var: tk.StringVar, label_var: tk.StringVar):
            raw_value = f"{float(raw_value):0.2f}"
            scale_var.set(raw_value)
            label_var.set(f"{int(float(raw_value)*100)}%")

        def build_widgets(stem_pair: str, model_list: list, option_var: tk.StringVar, label_var: tk.StringVar, scale_var: tk.DoubleVar):
            model_list.insert(0, NO_MODEL)
            secondary_model_Label = self.menu_sub_LABEL_SET(secondary_model_Frame, f'{stem_pair}', font_size=FONT_SIZE_3)
            secondary_model_Label.grid(pady=MENU_PADDING_1)
            secondary_model_Option = ComboBoxMenu(secondary_model_Frame, textvariable=option_var, values=model_list, dropdown_name=stem_pair, offset=310, width=READ_ONLY_COMBO_WIDTH)
            secondary_model_Option.grid(pady=MENU_PADDING_1)
            secondary_scale_info_Label = tk.Label(secondary_model_Frame, textvariable=label_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR)
            secondary_scale_info_Label.grid(pady=0)   
            secondary_model_scale_Option = ttk.Scale(secondary_model_Frame, variable=scale_var, from_=0.01, to=0.99, command=lambda s:convert_to_percentage(s, scale_var, label_var), orient='horizontal')
            secondary_model_scale_Option.grid(pady=2)
            self.help_hints(secondary_model_Label, text=SECONDARY_MODEL_HELP)
            self.help_hints(secondary_scale_info_Label, text=SECONDARY_MODEL_SCALE_HELP)

        build_widgets(stem_pair=VOCAL_PAIR,
                      model_list=voc_inst_list,
                      option_var=voc_inst_secondary_model_var,
                      label_var=voc_inst_secondary_model_scale_LABEL_var,
                      scale_var=voc_inst_secondary_model_scale_var)
        
        build_widgets(stem_pair=OTHER_PAIR,
                      model_list=other_list,
                      option_var=other_secondary_model_var,
                      label_var=other_secondary_model_scale_LABEL_var,
                      scale_var=other_secondary_model_scale_var)
        
        build_widgets(stem_pair=BASS_PAIR,
                      model_list=bass_list,
                      option_var=bass_secondary_model_var,
                      label_var=bass_secondary_model_scale_LABEL_var,
                      scale_var=bass_secondary_model_scale_var)
        
        build_widgets(stem_pair=DRUM_PAIR,
                      model_list=drum_list,
                      option_var=drums_secondary_model_var,
                      label_var=drums_secondary_model_scale_LABEL_var,
                      scale_var=drums_secondary_model_scale_var)
     
        is_secondary_model_activate_Option = ttk.Checkbutton(secondary_model_Frame, text=ACTIVATE_SECONDARY_MODEL_TEXT, variable=is_secondary_model_activate_var, command=change_state_lambda) 
        is_secondary_model_activate_Option.grid(row=21,pady=MENU_PADDING_1)
        self.help_hints(is_secondary_model_activate_Option, text=SECONDARY_MODEL_ACTIVATE_HELP)
        
        change_state_lambda()
        
        self.change_state_lambda = change_state_lambda
        
    def menu_preproc_model(self, tab):
        
        preproc_model_Frame = self.menu_FRAME_SET(tab)
        preproc_model_Frame.grid(row=0)  

        demucs_pre_proc_model_title_Label = self.menu_title_LABEL_SET(preproc_model_Frame, PREPROCESS_MODEL_CHOOSE_TEXT)
        demucs_pre_proc_model_title_Label.grid(pady=MENU_PADDING_3)
        
        pre_proc_list = self.model_list(VOCAL_STEM, INST_STEM, is_dry_check=True, is_no_demucs=True)
        pre_proc_list.insert(0, NO_MODEL)
        
        enable_pre_proc_model = lambda:(is_demucs_pre_proc_model_inst_mix_Option.configure(state=tk.NORMAL), demucs_pre_proc_model_Option.configure(state=READ_ONLY))
        disable_pre_proc_model = lambda:(is_demucs_pre_proc_model_inst_mix_Option.configure(state=tk.DISABLED), demucs_pre_proc_model_Option.configure(state=tk.DISABLED), self.is_demucs_pre_proc_model_inst_mix_var.set(False))
        pre_proc_model_toggle = lambda:enable_pre_proc_model() if self.is_demucs_pre_proc_model_activate_var.get() else disable_pre_proc_model()
        
        demucs_pre_proc_model_Label = self.menu_sub_LABEL_SET(preproc_model_Frame, SELECT_MODEL_TEXT, font_size=FONT_SIZE_3)
        demucs_pre_proc_model_Label.grid()
        demucs_pre_proc_model_Option = ComboBoxMenu(preproc_model_Frame, textvariable=self.demucs_pre_proc_model_var, values=pre_proc_list, dropdown_name='demucspre', offset=310, width=READ_ONLY_COMBO_WIDTH)
        demucs_pre_proc_model_Option.grid(pady=MENU_PADDING_2)

        is_demucs_pre_proc_model_inst_mix_Option = ttk.Checkbutton(preproc_model_Frame, text='Save Instrumental Mixture', width=DEMUCS_PRE_CHECKBOXS_WIDTH, variable=self.is_demucs_pre_proc_model_inst_mix_var) 
        is_demucs_pre_proc_model_inst_mix_Option.grid()
        self.help_hints(is_demucs_pre_proc_model_inst_mix_Option, text=PRE_PROC_MODEL_INST_MIX_HELP)
        
        is_demucs_pre_proc_model_activate_Option = ttk.Checkbutton(preproc_model_Frame, text=ACTIVATE_PRE_PROCESS_MODEL_TEXT, width=DEMUCS_PRE_CHECKBOXS_WIDTH, variable=self.is_demucs_pre_proc_model_activate_var, command=pre_proc_model_toggle) 
        is_demucs_pre_proc_model_activate_Option.grid()
        self.help_hints(is_demucs_pre_proc_model_activate_Option, text=PRE_PROC_MODEL_ACTIVATE_HELP)
        
        pre_proc_model_toggle()
        
    def menu_manual_downloads(self):
        
        manual_downloads_menu = tk.Toplevel()
        model_selection_var = tk.StringVar(value=SELECT_MODEL_TEXT)
        #info_text_var = tk.StringVar(value='')

        if self.is_online:
            model_data = self.online_data
            
            # Save the data as a JSON file
            with open(DOWNLOAD_MODEL_CACHE, 'w') as json_file:
                json.dump(model_data, json_file)
                
        else:
            if os.path.isfile(DOWNLOAD_MODEL_CACHE):
                with open(DOWNLOAD_MODEL_CACHE) as json_file:
                    model_data = json.load(json_file)
                    
        vr_download_list = model_data["vr_download_list"]
        mdx_download_list = model_data["mdx_download_list"]
        demucs_download_list = model_data["demucs_download_list"]
        mdx_download_list.update(model_data.get("mdx23c_download_list", {}))
        mdx_download_list.update(model_data.get("roformer_download_list", {}))
        mdx_download_list.update(model_data.get("other_network_list", {}))
        mdx_download_list.update(model_data.get("other_network_list_new", {}))

        def create_link(link):
            final_link = lambda:webbrowser.open_new_tab(link)
            return final_link
            
        def get_links():
            for widgets in manual_downloads_link_Frame.winfo_children():
                widgets.destroy()
                
            main_selection = model_selection_var.get()
            
            MAIN_ROW = 0
            
            self.menu_sub_LABEL_SET(manual_downloads_link_Frame, 'Download Link(s)').grid(row=0,column=0,padx=0,pady=MENU_PADDING_4)
            
            if VR_ARCH_TYPE in main_selection:
                main_selection = vr_download_list[main_selection]
                model_dir = VR_MODELS_DIR
            elif MDX_ARCH_TYPE in main_selection or MDX_23_NAME in main_selection:
                model_data = mdx_download_list[main_selection]
                if isinstance(model_data, dict):
                    has_custom_urls = any(val.startswith('http') for val in model_data.values())
                    if has_custom_urls:
                        main_selection = model_data
                    else:
                        main_selection = list(model_data.keys())[0]
                else:
                    main_selection = model_data
                    
                model_dir = MDX_MODELS_DIR

            elif DEMUCS_ARCH_TYPE in main_selection:
                model_dir = DEMUCS_NEWER_REPO_DIR if 'v3' in main_selection or 'v4' in main_selection else DEMUCS_MODELS_DIR
                main_selection = demucs_download_list[main_selection]

            if type(main_selection) is dict:
                for links in main_selection.values():
                    MAIN_ROW += 1
                    button_text = f" - Item {MAIN_ROW}" if len(main_selection.keys()) >= 2 else ''
                    link = create_link(links)
                    link_button = ttk.Button(manual_downloads_link_Frame, text=f"Open Link to Model{button_text}", command=link).grid(row=MAIN_ROW,column=0,padx=0,pady=MENU_PADDING_1)
            else:
                link = f"{NORMAL_REPO}{main_selection}"
                link_button = ttk.Button(manual_downloads_link_Frame, text=OPEN_LINK_TO_MODEL_TEXT, command=lambda:webbrowser.open_new_tab(link))
                link_button.grid(row=1,column=0,padx=0,pady=MENU_PADDING_2)
        
            self.menu_sub_LABEL_SET(manual_downloads_link_Frame, SELECTED_MODEL_PLACE_PATH_TEXT).grid(row=MAIN_ROW+2,column=0,padx=0,pady=MENU_PADDING_4)
            ttk.Button(manual_downloads_link_Frame, text=OPEN_MODEL_DIRECTORY_TEXT, command=lambda:OPEN_FILE_func(model_dir)).grid(row=MAIN_ROW+3,column=0,padx=0,pady=MENU_PADDING_1)
        
        manual_downloads_menu_Frame = self.menu_FRAME_SET(manual_downloads_menu)
        manual_downloads_menu_Frame.grid(row=0)  

        manual_downloads_link_Frame = self.menu_FRAME_SET(manual_downloads_menu, thickness=5)
        manual_downloads_link_Frame.grid(row=1)  

        manual_downloads_menu_title_Label = self.menu_title_LABEL_SET(manual_downloads_menu_Frame, MANUAL_DOWNLOADS_TEXT, width=45)
        manual_downloads_menu_title_Label.grid(row=0,column=0,padx=0,pady=MENU_PADDING_3)
        
        manual_downloads_menu_select_Label = self.menu_sub_LABEL_SET(manual_downloads_menu_Frame, SELECT_MODEL_TEXT)
        manual_downloads_menu_select_Label.grid(row=1,column=0,padx=0,pady=MENU_PADDING_1)
        
        manual_downloads_menu_select_Option = ttk.OptionMenu(manual_downloads_menu_Frame, model_selection_var)
        manual_downloads_menu_select_VR_Option = tk.Menu(manual_downloads_menu_select_Option['menu'])
        manual_downloads_menu_select_MDX_Option = tk.Menu(manual_downloads_menu_select_Option['menu'])
        manual_downloads_menu_select_DEMUCS_Option = tk.Menu(manual_downloads_menu_select_Option['menu'])
        manual_downloads_menu_select_Option['menu'].add_cascade(label='VR Models', menu= manual_downloads_menu_select_VR_Option)
        manual_downloads_menu_select_Option['menu'].add_cascade(label='MDX-Net Models', menu= manual_downloads_menu_select_MDX_Option)
        manual_downloads_menu_select_Option['menu'].add_cascade(label='Demucs Models', menu= manual_downloads_menu_select_DEMUCS_Option)

        for model_selection_vr in vr_download_list.keys():
            if not os.path.isfile(os.path.join(VR_MODELS_DIR, vr_download_list[model_selection_vr])):
                manual_downloads_menu_select_VR_Option.add_radiobutton(label=model_selection_vr, variable=model_selection_var, command=get_links)
            
        for model_selection_mdx in mdx_download_list.keys():
            
            model_name = mdx_download_list[model_selection_mdx]
            
            if isinstance(model_name, dict):
                model_filename = list(model_name.keys())[0]
                config_filename = None
                config_link = None
                for key, val in model_name.items():
                    if key.endswith('.yaml') or key.endswith('.json'):
                        config_filename = key
                        if val.startswith('http'):
                            config_link = val
                        else:
                            config_link = f"{MDX23_CONFIG_CHECKS}{val}"
                    elif key.endswith(CKPT) or key.endswith('.safetensors') or key.endswith(ONNX):
                        model_filename = key
                        if val.endswith('.yaml') or val.endswith('.json'):
                            config_filename = val
                            config_link = f"{MDX23_CONFIG_CHECKS}{val}"
                model_name = model_filename
                if config_filename and config_link:
                    config_local = os.path.join(MDX_C_CONFIG_PATH, config_filename)
                    if not os.path.isfile(config_local):
                        try:
                            with urllib.request.urlopen(config_link) as response:
                                with open(config_local, 'wb') as out_file:
                                    out_file.write(response.read())
                        except Exception as e:
                            print(f"Error downloading config in manual downloads: {e}")
                            model_name = None

            if model_name: 
                if not os.path.isfile(os.path.join(MDX_MODELS_DIR, model_name)):
                    manual_downloads_menu_select_MDX_Option.add_radiobutton(label=model_selection_mdx, variable=model_selection_var, command=get_links)
            
        for model_selection_demucs in demucs_download_list.keys():
            manual_downloads_menu_select_DEMUCS_Option.add_radiobutton(label=model_selection_demucs, variable=model_selection_var, command=get_links)
            
        manual_downloads_menu_select_Option.grid(row=2,column=0,padx=0,pady=MENU_PADDING_1)
    
        self.menu_placement(manual_downloads_menu, MANUAL_DOWNLOADS_TEXT, pop_up=True, close_function=lambda:manual_downloads_menu.destroy())
        
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
        """Ask user is they want to update"""
        
        is_new_update = self.online_data_refresh(confirmation_box=True)
        is_download_in_app_var = tk.BooleanVar(value=False)
        
        def update_type():
            if is_download_in_app_var.get():
                self.download_item(is_update_app=True)
            else:
                webbrowser.open_new_tab(self.download_update_link_var.get())

            update_confirmation_win.destroy()
            
        if is_new_update:
            
            update_confirmation_win = tk.Toplevel()

            update_confirmation_Frame = self.menu_FRAME_SET(update_confirmation_win)
            update_confirmation_Frame.grid(row=0)  
            
            update_found_label = self.menu_title_LABEL_SET(update_confirmation_Frame, UPDATE_FOUND_TEXT, width=15)
            update_found_label.grid(row=0,column=0,padx=0,pady=MENU_PADDING_2)
            
            confirm_update_label = self.menu_sub_LABEL_SET(update_confirmation_Frame, UPDATE_CONFIRMATION_TEXT, font_size=FONT_SIZE_3)
            confirm_update_label.grid(row=1,column=0,padx=0,pady=MENU_PADDING_1)
                    
            yes_button = ttk.Button(update_confirmation_Frame, text=YES_TEXT, command=update_type)
            yes_button.grid(row=2,column=0,padx=0,pady=MENU_PADDING_1)
            
            no_button = ttk.Button(update_confirmation_Frame, text=NO_TEXT, command=lambda:(update_confirmation_win.destroy()))
            no_button.grid(row=3,column=0,padx=0,pady=MENU_PADDING_1)
            
            if is_windows:
                download_outside_application_button = ttk.Checkbutton(update_confirmation_Frame, variable=is_download_in_app_var, text='Download Update in Application')
                download_outside_application_button.grid(row=4,column=0,padx=0,pady=MENU_PADDING_1)

            self.menu_placement(update_confirmation_win, CONFIRM_UPDATE_TEXT, pop_up=True)

    def pop_up_user_code_input(self):
        """Input VIP Code"""

        self.user_code_validation_var.set('')
        
        self.user_code = tk.Toplevel()
        
        user_code_Frame = self.menu_FRAME_SET(self.user_code)
        user_code_Frame.grid(row=0)  
                
        user_code_title_Label = self.menu_title_LABEL_SET(user_code_Frame, USER_DOWNLOAD_CODES_TEXT, width=20)
        user_code_title_Label.grid(row=0,column=0,padx=0,pady=MENU_PADDING_1)    
        
        user_code_Label = self.menu_sub_LABEL_SET(user_code_Frame, DOWNLOAD_CODE_TEXT)
        user_code_Label.grid(pady=MENU_PADDING_1)       
                
        self.user_code_Entry = ttk.Entry(user_code_Frame, textvariable=self.user_code_var, justify='center')
        self.user_code_Entry.grid(pady=MENU_PADDING_1)
        self.user_code_Entry.bind(right_click_button, self.right_click_menu_popup)
        self.current_text_box = self.user_code_Entry
        
        tooltip = ToolTip(self.user_code_Entry)
        def invalid_message_(text, is_success_message):
            tooltip.hidetip()
            tooltip.showtip(text, True, is_success_message)
        
        self.spacer_label(user_code_Frame)

        user_code_confrim_Button = ttk.Button(user_code_Frame, text=CONFIRM_TEXT, command=lambda:self.download_validate_code(confirm=True, code_message=invalid_message_))
        user_code_confrim_Button.grid(pady=MENU_PADDING_1)
        
        user_code_cancel_Button = ttk.Button(user_code_Frame, text=CANCEL_TEXT, command=lambda:self.user_code.destroy())
        user_code_cancel_Button.grid(pady=MENU_PADDING_1)
        
        support_title_Label = self.menu_title_LABEL_SET(user_code_Frame, text=SUPPORT_UVR_TEXT, width=20)
        support_title_Label.grid(pady=MENU_PADDING_1)    
        
        support_sub_Label = tk.Label(user_code_Frame, text=GET_DL_VIP_CODE_TEXT, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR)
        support_sub_Label.grid(pady=MENU_PADDING_1)
        
        uvr_patreon_Button = ttk.Button(user_code_Frame, text=UVR_PATREON_LINK_TEXT, command=lambda:webbrowser.open_new_tab(DONATE_LINK_PATREON))
        uvr_patreon_Button.grid(pady=MENU_PADDING_1)
        
        bmac_patreon_Button=ttk.Button(user_code_Frame, text=BMAC_UVR_TEXT, command=lambda:webbrowser.open_new_tab(DONATE_LINK_BMAC))
        bmac_patreon_Button.grid(pady=MENU_PADDING_1)
        
        self.menu_placement(self.user_code, INPUT_CODE_TEXT, pop_up=True)

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
        """Grabbing all audio files from selected directories."""
        
        input_list = []

        ext = FFMPEG_EXT if not self.is_accept_any_input_var.get() else ANY_EXT

        for i in self.inputPaths:
            if os.path.isfile(i):
                if i.endswith(ext):
                    input_list.append(i)
            for root, _dirs, files in os.walk(i):
                for file in files:
                    if file.endswith(ext):
                        file = os.path.join(root, file)
                        if os.path.isfile(file):
                            input_list.append(file)
                                         
        self.inputPaths = tuple(input_list)

    def process_check_wav_type(self):
        if self.wav_type_set_var.get() == '32-bit Float':
            self.wav_type_set = 'FLOAT'
        elif self.wav_type_set_var.get() == '64-bit Float':#
            self.wav_type_set = 'FLOAT' if not self.save_format_var.get() == WAV else 'DOUBLE'
        else:
            self.wav_type_set = self.wav_type_set_var.get()
            
    def process_preliminary_checks(self):
        """Verifies a valid model is chosen"""
        
        self.process_check_wav_type()
        
        if self.chosen_process_method_var.get() == ENSEMBLE_MODE:
            continue_process = lambda:False if len(self.ensemble_listbox_get_all_selected_models()) <= 1 else True
        if self.chosen_process_method_var.get() == VR_ARCH_PM:
            continue_process = lambda:False if self.vr_model_var.get() == CHOOSE_MODEL else True
        if self.chosen_process_method_var.get() == MDX_ARCH_TYPE:
            continue_process = lambda:False if self.mdx_net_model_var.get() == CHOOSE_MODEL else True
        if self.chosen_process_method_var.get() == DEMUCS_ARCH_TYPE:
            continue_process = lambda:False if self.demucs_model_var.get() == CHOOSE_MODEL else True

        return continue_process()

    def process_storage_check(self):
        """Verifies storage requirments"""
        
        total, used, free = shutil.disk_usage("/") 
        
        space_details = f'Detected Total Space: {int(total/1.074e+9)} GB\'s\n' +\
                        f'Detected Used Space: {int(used/1.074e+9)} GB\'s\n' +\
                        f'Detected Free Space: {int(free/1.074e+9)} GB\'s\n'
            
        appropriate_storage = True
            
        if int(free/1.074e+9) <= 2:
            self.error_dialoge([STORAGE_ERROR[0], f'{STORAGE_ERROR[1]}{space_details}'])
            appropriate_storage = False
        
        if int(free/1.074e+9) in [3, 4, 5, 6, 7, 8]:
            appropriate_storage = self.message_box([STORAGE_WARNING[0], f'{STORAGE_WARNING[1]}{space_details}{CONFIRM_WARNING}'])
                        
        return appropriate_storage

    def process_initialize(self):
        """Verifies the input/output directories are valid and prepares to thread the main process."""
        
        if not (
            self.chosen_process_method_var.get() == AUDIO_TOOLS 
            and self.chosen_audio_tool_var.get() in [ALIGN_INPUTS, MATCH_INPUTS] 
            and self.fileOneEntry_var.get() 
            and self.fileTwoEntry_var.get()
        ) and not (
            self.inputPaths and os.path.isfile(self.inputPaths[0])
        ):
            self.error_dialoge(INVALID_INPUT)
            return

            
        if not os.path.isdir(self.export_path_var.get()):
            self.error_dialoge(INVALID_EXPORT)
            return

        if not self.process_storage_check():
            return

        if self.chosen_process_method_var.get() != AUDIO_TOOLS:
            if not self.process_preliminary_checks():
                error_msg = INVALID_ENSEMBLE if self.chosen_process_method_var.get() == ENSEMBLE_MODE else INVALID_MODEL
                self.error_dialoge(error_msg)
                return

        with self.queue_lock:
            if self.chosen_process_method_var.get() == AUDIO_TOOLS and self.chosen_audio_tool_var.get() in [ALIGN_INPUTS, MATCH_INPUTS]:
                self.queue_task_counter += 1
                task = QueueTask(self.queue_task_counter, self)
                self.processing_queue.append(task)
                self.command_Text.write(f"Task #{task.id} added to the processing queue.\n")
            else:
                for input_path in self.inputPaths:
                    self.queue_task_counter += 1
                    task = QueueTask(self.queue_task_counter, self)
                    task.input_paths = (input_path,)
                    self.processing_queue.append(task)
                    self.command_Text.write(f"Task #{task.id} added to the processing queue.\n")
        
        # Update Treeview if settings window is open
        self.update_queue_ui_display()
        
        # Start queue worker if not running
        if not self.is_queue_worker_running:
            self.queue_worker_thread = KThread(target=self.queue_worker_loop)
            self.queue_worker_thread.start()

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
        self.auto_save()
        self.conversion_Button_Text_var.set(WAIT_PROCESSING)
        self.conversion_Button.configure(state=tk.DISABLED)
        self.progress_text_var.set("No Active Processing")
        self.command_Text.clear()

    def process_button_queue_mode(self):
        """Keep button enabled so user can keep adding tasks to the queue."""
        self.auto_save()
        self.command_Text.clear()
        # Button stays NORMAL — user can click it again to enqueue more tasks
        self.conversion_Button_Text_var.set(START_PROCESSING)
        self.progress_text_var.set("No Active Processing")
        self.conversion_Button.configure(state=tk.NORMAL)

    def process_get_baseText(self, total_files, file_num, is_dual=False):
        """Create the base text for the command widget"""
        
        init_text = 'Files' if is_dual else 'File'
        
        text = f'{init_text} {file_num}/{total_files} '
        
        return text

    def process_update_progress(self, total_files, step: float = 1):
        """Calculate the progress for the progress widget in the GUI"""
        while getattr(self, 'is_process_paused', False):
            import time
            time.sleep(0.1)
            
        total_count = self.true_model_count * total_files
        base = (100 / total_count)
        progress = base * self.iteration - base
        progress += base * step

        def _update():
            self.progress_bar_main_var.set(progress)
            self.progress_text_var.set(f'Process Progress: {int(progress)}%')

        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.after(0, _update)

    def show_stop_menu(self):
        x = self.stop_expand_Button.winfo_rootx()
        y = self.stop_expand_Button.winfo_rooty() + self.stop_expand_Button.winfo_height()
        try:
            self.stop_menu.tk_popup(x, y)
        finally:
            self.stop_menu.grab_release()

    def confirm_stop_process(self, stop_all=False):
        """Asks for confirmation before halting active process"""
        
        self.auto_save()

        if self.active_processing_thread and self.active_processing_thread.is_alive():
            confirm = messagebox.askyesno(parent=root, title=STOP_PROCESS_CONFIRM[0], message=STOP_PROCESS_CONFIRM[1])

            if confirm:
                if stop_all:
                    for task in self.processing_queue:
                        if task.status == TASK_STATUS_PENDING:
                            task.status = TASK_STATUS_FAILED
                    self.update_queue_ui_display()
                try:
                    self.active_processing_thread.terminate()
                finally:
                    self.is_process_stopped = True
                    self.command_Text.write(PROCESS_STOPPED_BY_USER)
        else:
            if stop_all:
                for task in self.processing_queue:
                    if task.status == TASK_STATUS_PENDING:
                        task.status = TASK_STATUS_FAILED
                self.update_queue_ui_display()
            self.clear_cache_torch = True

    def process_end(self, error=None):
        """End of process actions"""
        
        self.auto_save()
        self.cached_sources_clear()
        self.clear_cache_torch = True
        self.conversion_Button_Text_var.set(START_PROCESSING)
        self.conversion_Button.configure(state=tk.NORMAL)
        self.progress_bar_main_var.set(0)

        if not error and not getattr(self, 'is_process_stopped', False):
            try:
                send_notification("Ultimate Vocal Remover", "Audio processing completed successfully!")
            except Exception:
                pass

        if error:
            error_message_box_text = f'{error_dialouge(error)}{ERROR_OCCURED[1]}'
            
            def show_error():
                confirm = messagebox.askyesno(parent=root,
                                                 title=ERROR_OCCURED[0],
                                                 message=error_message_box_text)
                
                if confirm:
                    self.is_confirm_error_var.set(True)
                    self.clear_cache_torch = True
                    
            root.after(0, show_error)

            self.clear_cache_torch = True
            
            if MODEL_MISSING_CHECK in error_message_box_text: 
                self.update_checkbox_text()
 
    def process_tool_start(self, task=None):
        """Start the conversion for all the given mp3 and wav files"""

        def time_elapsed():
            return f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}'

        def get_audio_file_base(audio_file):
            if audio_tool.audio_tool == MANUAL_ENSEMBLE:
                return f'{os.path.splitext(os.path.basename(inputPaths[0]))[0]}'
            elif audio_tool.audio_tool in [ALIGN_INPUTS, MATCH_INPUTS]:
                return f'{os.path.splitext(os.path.basename(audio_file[0]))[0]}'
            else:
                return f'{os.path.splitext(os.path.basename(audio_file))[0]}'

        def handle_ensemble(inputPaths, audio_file_base):
            self.progress_bar_main_var.set(50)
            choose_algorithm = task.choose_algorithm if task else self.choose_algorithm_var.get()
            if choose_algorithm == COMBINE_INPUTS:
                audio_tool.combine_audio(inputPaths, audio_file_base)
            else:
                audio_tool.ensemble_manual(inputPaths, audio_file_base)
            self.progress_bar_main_var.set(100)
            self.command_Text.write(DONE)

        def handle_alignment_match(audio_file, audio_file_base, command_Text, set_progress_bar):
            audio_file_2_base = f'{os.path.splitext(os.path.basename(audio_file[1]))[0]}'
            if audio_tool.audio_tool == MATCH_INPUTS:
                audio_tool.match_inputs(audio_file, audio_file_base, command_Text)
            else:
                command_Text(f"{PROCESS_STARTING_TEXT}\n")
                audio_tool.align_inputs(audio_file, audio_file_base, audio_file_2_base, command_Text, set_progress_bar)
            self.progress_bar_main_var.set(base * file_num)
            self.command_Text.write(f"{DONE}\n")

        def handle_pitch_time_shift(audio_file, audio_file_base):
            audio_tool.pitch_or_time_shift(audio_file, audio_file_base)
            self.progress_bar_main_var.set(base * file_num)
            self.command_Text.write(DONE)

        multiple_files = False
        stime = time.perf_counter()
        if not task:
            self.process_button_init()
        inputPaths = task.input_paths if task else self.inputPaths
        is_verified_audio = True
        is_dual = False
        is_model_sample_mode = task.model_sample_mode if task else self.model_sample_mode_var.get()
        is_task_complete = task.is_task_complete if task else self.is_task_complete_var.get()
        self.iteration = 0
        self.true_model_count = 1
        self.process_check_wav_type()
        process_complete_text = PROCESS_COMPLETE

        chosen_audio_tool = task.chosen_audio_tool if task else self.chosen_audio_tool_var.get()
        if chosen_audio_tool in [ALIGN_INPUTS, MATCH_INPUTS]:
            DualBatch_inputPaths = task.DualBatch_inputPaths if task else self.DualBatch_inputPaths
            fileOneEntry_Full = task.fileOneEntry_Full if task else self.fileOneEntry_Full_var.get()
            fileTwoEntry_Full = task.fileTwoEntry_Full if task else self.fileTwoEntry_Full_var.get()
            if DualBatch_inputPaths:
                inputPaths = tuple(DualBatch_inputPaths)
            else:
                if not fileOneEntry_Full or not fileTwoEntry_Full:
                    self.command_Text.write(NOT_ENOUGH_ERROR_TEXT)
                    if not task:
                        self.process_end()
                    else:
                        raise RuntimeError("Not enough files selected.")
                    return
                else:
                    inputPaths = [(fileOneEntry_Full, fileTwoEntry_Full)]

        try:
            total_files = len(inputPaths)
            if task:
                audio_tool = task.audio_tool
                if chosen_audio_tool in [TIME_STRETCH, CHANGE_PITCH, ALIGN_INPUTS, MATCH_INPUTS]:
                    self.progress_bar_main_var.set(2)
                    if chosen_audio_tool in [ALIGN_INPUTS, MATCH_INPUTS]:
                        is_dual = True
                elif chosen_audio_tool == MANUAL_ENSEMBLE:
                    multiple_files = True
                    if total_files <= 1:
                        self.command_Text.write(NOT_ENOUGH_ERROR_TEXT)
                        raise RuntimeError("Not enough files selected.")
            else:
                if self.chosen_audio_tool_var.get() == TIME_STRETCH:
                    audio_tool = AudioTools(TIME_STRETCH, root=self)
                    self.progress_bar_main_var.set(2)
                elif self.chosen_audio_tool_var.get() == CHANGE_PITCH:
                    audio_tool = AudioTools(CHANGE_PITCH, root=self)
                    self.progress_bar_main_var.set(2)
                elif self.chosen_audio_tool_var.get() == MANUAL_ENSEMBLE:
                    if self.chosen_audio_tool_var.get() == MANUAL_ENSEMBLE:
                        audio_tool = Ensembler(is_manual_ensemble=True, root=self)
                    multiple_files = True
                    if total_files <= 1:
                        self.command_Text.write(NOT_ENOUGH_ERROR_TEXT)
                        self.process_end()
                        return
                elif self.chosen_audio_tool_var.get() in [ALIGN_INPUTS, MATCH_INPUTS]:
                    audio_tool = AudioTools(self.chosen_audio_tool_var.get(), root=self)
                    self.progress_bar_main_var.set(2)
                    is_dual = True

            for file_num, audio_file in enumerate(inputPaths, start=1):
                self.iteration += 1
                base = (100 / total_files)
                audio_file_base = get_audio_file_base(audio_file)
                self.base_text = self.process_get_baseText(total_files=total_files, file_num=total_files if multiple_files else file_num, is_dual=is_dual)
                command_Text = lambda text: self.command_Text.write(self.base_text + text)

                set_progress_bar = lambda step, inference_iterations=0:self.process_update_progress(total_files=total_files, step=(step + (inference_iterations)))

                if not self.verify_audio(audio_file):
                    error_text_console = f'{self.base_text}"{os.path.basename(audio_file)}\" {MISSING_MESS_TEXT}\n'
                    if total_files >= 2:
                        self.command_Text.write(f'\n{error_text_console}')
                    is_verified_audio = False
                    continue

                audio_tool_action = audio_tool.audio_tool
                if audio_tool_action not in [MANUAL_ENSEMBLE, ALIGN_INPUTS, MATCH_INPUTS]:
                    audio_file = self.create_sample(audio_file) if is_model_sample_mode else audio_file
                    self.command_Text.write(f'{NEW_LINE if file_num != 1 else NO_LINE}{self.base_text}"{os.path.basename(audio_file)}\".{NEW_LINES}')
                elif audio_tool_action in [ALIGN_INPUTS, MATCH_INPUTS]:
                    text_write = ("File 1", "File 2") if audio_tool_action == ALIGN_INPUTS else ("Target", "Reference")
                    if audio_file[0] != audio_file[1]:
                        self.command_Text.write(f'{self.base_text}{text_write[0]}:  "{os.path.basename(audio_file[0])}"{NEW_LINE}')
                        self.command_Text.write(f'{self.base_text}{text_write[1]}:  "{os.path.basename(audio_file[1])}"{NEW_LINES}')
                    else:
                        self.command_Text.write(f'{self.base_text}{text_write[0]} & {text_write[1]} {SIMILAR_TEXT}{NEW_LINES}')
                        continue
                elif audio_tool_action == MANUAL_ENSEMBLE:
                    for n, i in enumerate(inputPaths):
                        self.command_Text.write(f'File {n+1} "{os.path.basename(i)}"{NEW_LINE}')
                    self.command_Text.write(NEW_LINE)
                    
                is_verified_audio = True

                if audio_tool_action not in [ALIGN_INPUTS, MATCH_INPUTS]:
                    command_Text(PROCESS_STARTING_TEXT)

                if audio_tool_action == MANUAL_ENSEMBLE:
                    handle_ensemble(inputPaths, audio_file_base)
                    break
                if audio_tool_action in [ALIGN_INPUTS, MATCH_INPUTS]:
                    process_complete_text = PROCESS_COMPLETE_2
                    handle_alignment_match(audio_file, audio_file_base, command_Text, set_progress_bar)
                if audio_tool_action in [TIME_STRETCH, CHANGE_PITCH]:
                    handle_pitch_time_shift(audio_file, audio_file_base)

            if total_files == 1 and not is_verified_audio:
                self.command_Text.write(f'{error_text_console}\n{PROCESS_FAILED}')
                self.command_Text.write(time_elapsed())
                playsound(FAIL_CHIME) if is_task_complete else None
                if task:
                    raise RuntimeError("Verification failed.")
            else:
                self.command_Text.write(f'{process_complete_text}{time_elapsed()}')
                playsound(COMPLETE_CHIME) if is_task_complete else None

            if not task:
                self.process_end()

        except Exception as e:
            self.error_log_var.set(error_text(chosen_audio_tool, e))
            self.command_Text.write(f'\n\n{PROCESS_FAILED}')
            self.command_Text.write(time_elapsed())
            playsound(FAIL_CHIME) if is_task_complete else None
            if not task:
                self.process_end(error=e)
            else:
                task.status = TASK_STATUS_FAILED
                raise e

    def process_determine_secondary_model(self, process_method, main_model_primary_stem, is_primary_stem_only=False, is_secondary_stem_only=False):
        """Obtains the correct secondary model data for conversion."""
        
        secondary_model_scale = None
        secondary_model = tk.StringVar(value=NO_MODEL)
        
        if process_method == VR_ARCH_TYPE:
            secondary_model_vars = self.vr_secondary_model_vars
        if process_method == MDX_ARCH_TYPE:
            secondary_model_vars = self.mdx_secondary_model_vars
        if process_method == DEMUCS_ARCH_TYPE:
            secondary_model_vars = self.demucs_secondary_model_vars

        if main_model_primary_stem in [VOCAL_STEM, INST_STEM]:
            secondary_model = secondary_model_vars["voc_inst_secondary_model"]
            secondary_model_scale = secondary_model_vars["voc_inst_secondary_model_scale"].get()
        if main_model_primary_stem in [OTHER_STEM, NO_OTHER_STEM]:
            secondary_model = secondary_model_vars["other_secondary_model"]
            secondary_model_scale = secondary_model_vars["other_secondary_model_scale"].get()
        if main_model_primary_stem in [DRUM_STEM, NO_DRUM_STEM]:
            secondary_model = secondary_model_vars["drums_secondary_model"]
            secondary_model_scale = secondary_model_vars["drums_secondary_model_scale"].get()
        if main_model_primary_stem in [BASS_STEM, NO_BASS_STEM]:
            secondary_model = secondary_model_vars["bass_secondary_model"]
            secondary_model_scale = secondary_model_vars["bass_secondary_model_scale"].get()

        if secondary_model_scale:
           secondary_model_scale = float(secondary_model_scale)

        if not secondary_model.get() == NO_MODEL:
            secondary_model = ModelData(secondary_model.get(), 
                                        is_secondary_model=True, 
                                        primary_model_primary_stem=main_model_primary_stem, 
                                        is_primary_model_primary_stem_only=is_primary_stem_only, 
                                        is_primary_model_secondary_stem_only=is_secondary_stem_only, root=self)
            if not secondary_model.model_status:
                secondary_model = None
        else:
            secondary_model = None
            
        return secondary_model, secondary_model_scale
        
    def process_determine_demucs_pre_proc_model(self, primary_stem=None):
        """Obtains the correct pre-process secondary model data for conversion."""
        
        # Check if a pre-process model is set and it's not the 'NO_MODEL' value
        if self.demucs_pre_proc_model_var.get() != NO_MODEL and self.is_demucs_pre_proc_model_activate_var.get():
            pre_proc_model = ModelData(self.demucs_pre_proc_model_var.get(), 
                                        primary_model_primary_stem=primary_stem, 
                                        is_pre_proc_model=True, root=self)
            
            # Return the model if it's valid
            if pre_proc_model.model_status:
                return pre_proc_model
                
        return None

    def process_determine_vocal_split_model(self):
        """Obtains the correct vocal splitter secondary model data for conversion."""
        
        # Check if a vocal splitter model is set and if it's not the 'NO_MODEL' value
        if self.set_vocal_splitter_var.get() != NO_MODEL and self.is_set_vocal_splitter_var.get():
            vocal_splitter_model = ModelData(self.set_vocal_splitter_var.get(), is_vocal_split_model=True, root=self)
            
            # Return the model if it's valid
            if vocal_splitter_model.model_status:
                return vocal_splitter_model
                
        return None

    def check_only_selection_stem(self, checktype):
        
        chosen_method = self.chosen_process_method_var.get()
        is_demucs = chosen_method == DEMUCS_ARCH_TYPE#

        stem_primary_label = self.is_primary_stem_only_Demucs_Text_var.get() if is_demucs else self.is_primary_stem_only_Text_var.get()
        stem_primary_bool = self.is_primary_stem_only_Demucs_var.get() if is_demucs else self.is_primary_stem_only_var.get()
        stem_secondary_label = self.is_secondary_stem_only_Demucs_Text_var.get() if is_demucs else self.is_secondary_stem_only_Text_var.get()
        stem_secondary_bool = self.is_secondary_stem_only_Demucs_var.get() if is_demucs else self.is_secondary_stem_only_var.get()

        if checktype == VOCAL_STEM_ONLY:
            return not (
                (not VOCAL_STEM_ONLY == stem_primary_label and stem_primary_bool) or 
                (VOCAL_STEM_ONLY not in stem_secondary_label and stem_secondary_bool)
            )
        elif checktype == INST_STEM_ONLY:
            return (
                (INST_STEM_ONLY == stem_primary_label and stem_primary_bool and self.is_save_inst_set_vocal_splitter_var.get() and self.set_vocal_splitter_var.get() != NO_MODEL) or 
                (INST_STEM_ONLY == stem_secondary_label and stem_secondary_bool and self.is_save_inst_set_vocal_splitter_var.get() and self.set_vocal_splitter_var.get() != NO_MODEL)
            )
        elif checktype == IS_SAVE_VOC_ONLY:
            return (
                (VOCAL_STEM_ONLY == stem_primary_label and stem_primary_bool) or 
                (VOCAL_STEM_ONLY == stem_secondary_label and stem_secondary_bool)
            )
        elif checktype == IS_SAVE_INST_ONLY:
            return (
                (INST_STEM_ONLY == stem_primary_label and stem_primary_bool) or 
                (INST_STEM_ONLY == stem_secondary_label and stem_secondary_bool)
            )

    def determine_voc_split(self, models):
        is_vocal_active = self.check_only_selection_stem(VOCAL_STEM_ONLY) or self.check_only_selection_stem(INST_STEM_ONLY)

        if self.set_vocal_splitter_var.get() != NO_MODEL and self.is_set_vocal_splitter_var.get() and is_vocal_active:
            model_stems_list = self.model_list(VOCAL_STEM, INST_STEM, is_dry_check=True, is_check_vocal_split=True)
            if any(model.model_basename in model_stems_list for model in models):
                return 1
        
        return 0
        
    def process_start(self, task=None):
        """Start the conversion for all the given mp3 and wav files"""
        
        stime = time.perf_counter()
        time_elapsed = lambda:f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}'
        export_path = task.export_path if task else self.export_path_var.get()
        is_ensemble = task.is_ensemble if task else False
        self.true_model_count = 0
        self.iteration = 0
        is_verified_audio = True
        if not task:
            self.process_button_init()
        inputPaths = task.input_paths if task else self.inputPaths
        inputPath_total_len = len(inputPaths)
        is_model_sample_mode = task.is_model_sample_mode if task else self.model_sample_mode_var.get()
        
        try:
            if task:
                model = task.model_data
                ensemble = task.ensemble
            else:
                if self.chosen_process_method_var.get() == ENSEMBLE_MODE:
                    model, ensemble = self.assemble_model_data(), Ensembler(root=self)
                    export_path, is_ensemble = ensemble.ensemble_folder_name, True
                if self.chosen_process_method_var.get() == VR_ARCH_PM:
                    model = self.assemble_model_data(self.vr_model_var.get(), VR_ARCH_TYPE)
                if self.chosen_process_method_var.get() == MDX_ARCH_TYPE:
                    model = self.assemble_model_data(self.mdx_net_model_var.get(), MDX_ARCH_TYPE)
                if self.chosen_process_method_var.get() == DEMUCS_ARCH_TYPE:
                    model = self.assemble_model_data(self.demucs_model_var.get(), DEMUCS_ARCH_TYPE)

            self.cached_source_model_list_check(model)
            
            true_model_4_stem_count = sum(m.demucs_4_stem_added_count if m.process_method == DEMUCS_ARCH_TYPE else 0 for m in model)
            true_model_pre_proc_model_count = sum(2 if m.pre_proc_model_activated else 0 for m in model)
            self.true_model_count = sum(2 if m.is_secondary_model_activated else 1 for m in model) + true_model_4_stem_count + true_model_pre_proc_model_count + self.determine_voc_split(model)

            #print("self.true_model_count", self.true_model_count)

            for file_num, audio_file in enumerate(inputPaths, start=1):
                self.cached_sources_clear()
                base_text = self.process_get_baseText(total_files=inputPath_total_len, file_num=file_num)
                self.file_progress_var.set(f"File {file_num}/{inputPath_total_len}: {os.path.basename(audio_file)}")

                if self.verify_audio(audio_file):
                    original_audio_file = audio_file
                    audio_file = self.create_sample(audio_file) if is_model_sample_mode else audio_file
                    self.command_Text.write(f'{NEW_LINE if not file_num ==1 else NO_LINE}{base_text}"{os.path.basename(audio_file)}\".{NEW_LINES}')
                    is_verified_audio = True
                else:
                    error_text_console = f'{base_text}"{os.path.basename(audio_file)}\" {MISSING_MESS_TEXT}\n'
                    self.command_Text.write(f'\n{error_text_console}') if inputPath_total_len >= 2 else None
                    self.iteration += self.true_model_count
                    is_verified_audio = False
                    continue

                for current_model_num, current_model in enumerate(model, start=1):
                    self.iteration += 1

                    if is_ensemble:
                        self.command_Text.write(f'Ensemble Mode - {current_model.model_basename} - Model {current_model_num}/{len(model)}{NEW_LINES}')

                    model_name_text = f'({current_model.model_basename})' if not is_ensemble else ''
                    config_details = ""
                    if current_model.process_method == MDX_ARCH_TYPE:
                        overlap_val = current_model.overlap_mdx if not current_model.is_mdx_c else current_model.overlap_mdx23
                        config_details = f" [Seg: {current_model.mdx_segment_size} | Over: {overlap_val} | TTA: {'Y' if current_model.is_tta else 'N'}]"
                    elif current_model.process_method == VR_ARCH_TYPE:
                        config_details = f" [Win: {current_model.window_size} | Agg: {current_model.aggression_setting} | TTA: {'Y' if current_model.is_tta else 'N'}]"
                    elif current_model.process_method == DEMUCS_ARCH_TYPE:
                        config_details = f" [Seg: {current_model.segment} | Shift: {current_model.shifts}]"

                    self.command_Text.write(base_text + f'{LOADING_MODEL_TEXT} {model_name_text}{config_details}...')

                    set_progress_bar = lambda step, inference_iterations=0:self.process_update_progress(total_files=inputPath_total_len, step=(step + (inference_iterations)))
                    write_to_console = lambda progress_text, base_text=base_text:self.command_Text.write(base_text + progress_text)

                    current_export_path = export_path
                    if (task.is_create_model_folder if task else self.is_create_model_folder_var.get()) and not is_ensemble:
                        current_export_path = os.path.join(Path(task.export_path if task else self.export_path_var.get()), current_model.model_basename, os.path.splitext(os.path.basename(audio_file))[0])
                        if not os.path.isdir(current_export_path):
                            os.makedirs(current_export_path)

                    import glob
                    base_name_original = os.path.splitext(os.path.basename(audio_file))[0]
                    audio_file_base = base_name_original
                    counter = 1
                    
                    while True:
                        temp_base = audio_file_base
                        if (task.is_testing_audio if task else self.is_testing_audio_var.get()) and not is_ensemble:
                            temp_base = f"{round(time.time())}_{temp_base}"
                        if is_ensemble:
                            temp_base = f"{temp_base}_{current_model.model_basename}"
                        elif (task.is_add_model_name if task else self.is_add_model_name_var.get()):
                            temp_base = f"{temp_base}_{current_model.model_basename}"
                            
                        existing = glob.glob(os.path.join(current_export_path, f"{temp_base}*"))
                        if not existing:
                            audio_file_base = temp_base
                            break
                            
                        audio_file_base = f"{base_name_original}_{counter}"
                        counter += 1

                    process_data = {
                                    'model_data': current_model, 
                                    'export_path': current_export_path,
                                    'audio_file_base': audio_file_base,
                                    'audio_file': audio_file,
                                    'set_progress_bar': set_progress_bar,
                                    'write_to_console': write_to_console,
                                    'process_iteration': self.process_iteration,
                                    'cached_source_callback': self.cached_source_callback,
                                    'cached_model_source_holder': self.cached_model_source_holder,
                                    'list_all_models': self.all_models,
                                    'is_ensemble_master': is_ensemble,
                                    'is_half_precision': getattr(task, 'is_half_precision', self.is_half_precision_var.get()) if task else self.is_half_precision_var.get(),
                                    'is_4_stem_ensemble': True if (task.ensemble_main_stem if task else self.ensemble_main_stem_var.get()) in [FOUR_STEM_ENSEMBLE, MULTI_STEM_ENSEMBLE] and is_ensemble else False,
                                    'original_audio_file': original_audio_file}
                    
                    if current_model.process_method == VR_ARCH_TYPE:
                        seperator = SeperateVR(current_model, process_data)
                    if current_model.process_method == MDX_ARCH_TYPE:
                        seperator = SeperateMDXC(current_model, process_data) if current_model.is_mdx_c else SeperateMDX(current_model, process_data)
                    if current_model.process_method == DEMUCS_ARCH_TYPE:
                        seperator = SeperateDemucs(current_model, process_data)
                        
                    seperator.seperate()
                    
                    if is_ensemble:
                        self.command_Text.write('\n')

                if is_ensemble:
                    
                    audio_file_base = audio_file_base.replace(f"_{current_model.model_basename}","")
                    self.command_Text.write(base_text + ENSEMBLING_OUTPUTS)
                    
                    if (task.ensemble_main_stem if task else self.ensemble_main_stem_var.get()) in [FOUR_STEM_ENSEMBLE, MULTI_STEM_ENSEMBLE]:
                        stem_list = extract_stems(audio_file_base, export_path)
                        for output_stem in stem_list:
                            ensemble.ensemble_outputs(audio_file_base, export_path, output_stem, is_4_stem=True)
                    else:
                        if not (task.is_secondary_stem_only if task else self.is_secondary_stem_only_var.get()):
                            ensemble.ensemble_outputs(audio_file_base, export_path, PRIMARY_STEM)
                        if not (task.is_primary_stem_only if task else self.is_primary_stem_only_var.get()):
                            ensemble.ensemble_outputs(audio_file_base, export_path, SECONDARY_STEM)
                            ensemble.ensemble_outputs(audio_file_base, export_path, SECONDARY_STEM, is_inst_mix=True)

                    self.command_Text.write(DONE)
                    
                if is_model_sample_mode:
                    if os.path.isfile(audio_file):
                        os.remove(audio_file)
                    
                clear_gpu_cache()
                
            shutil.rmtree(export_path) if is_ensemble and len(os.listdir(export_path)) == 0 else None

            if inputPath_total_len == 1 and not is_verified_audio:
                self.command_Text.write(f'{error_text_console}\n{PROCESS_FAILED}')
                self.command_Text.write(time_elapsed())
                playsound(FAIL_CHIME) if (task.is_task_complete if task else self.is_task_complete_var.get()) else None
            else:
                set_progress_bar(1.0)
                self.command_Text.write(PROCESS_COMPLETE)
                self.command_Text.write(time_elapsed())
                playsound(COMPLETE_CHIME) if (task.is_task_complete if task else self.is_task_complete_var.get()) else None
                
            if not task:
                self.process_end()
                        
        except Exception as e:
            self.error_log_var.set(f"{error_text(task.process_method if task else self.chosen_process_method_var.get(), e)}{self.get_settings_list()}")
            self.command_Text.write(f'\n\n{PROCESS_FAILED}')
            self.command_Text.write(time_elapsed())
            playsound(FAIL_CHIME) if (task.is_task_complete if task else self.is_task_complete_var.get()) else None
            if not task:
                self.process_end(error=e)
            else:
                task.status = TASK_STATUS_FAILED
                raise e

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
