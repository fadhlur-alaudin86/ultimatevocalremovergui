"""Download center and model deletion manager for UVR.
Handles checking updates, downloading models, verifying VIP codes, and deleting models.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import subprocess
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import messagebox, ttk
from typing import Any

import natsort
import wget
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from kthread import KThread

from __version__ import PATCH, PATCH_LINUX, PATCH_MAC
from gui_data.app_size_values import (
    FONT_SIZE_1,
    FONT_SIZE_3,
    MENU_PADDING_1,
    MENU_PADDING_2,
)
from gui_data.constants import (
    ALL_TYPES,
    ARM,
    BETA_VERSION,
    BMAC_UVR_TEXT,
    BULLETIN_CHECK,
    CANCEL_TEXT,
    CHECK_FOR_UPDATES_TEXT,
    CHOOSE_ENSEMBLE_OPTION,
    CHOOSE_MODEL,
    CKPT,
    CONFIRM_TEXT,
    CONFIRM_UPDATE_TEXT,
    DELETE_ENS_ENTRY,
    DELETE_MODEL_CONFIRM_TEXT,
    DEMUCS_ARCH_TYPE,
    DEMUCS_MODEL_NAME_DATA_LINK,
    DEMUCS_NEWER_ARCH_TYPES,
    DEMUCS_NEWER_TAGS,
    DONATE_LINK_BMAC,
    DONATE_LINK_PATREON,
    DOWNLOAD_CHECKS,
    DOWNLOAD_CODE_TEXT,
    DOWNLOAD_COMPLETE,
    DOWNLOAD_FAILED,
    DOWNLOAD_MORE,
    DOWNLOAD_STOPPED,
    DOWNLOAD_UPDATE_COMPLETE,
    DOWNLOADING_ITEM,
    DOWNLOADING_UPDATE,
    FG_COLOR,
    FILE_EXISTS,
    GET_DL_VIP_CODE_TEXT,
    INFO_UNAVAILABLE_TEXT,
    INPUT_CODE_TEXT,
    LOADING_VERSION_INFO_TEXT,
    MDX23_CONFIG_CHECKS,
    MDX_23_NAME,
    MDX_ARCH_TYPE,
    MDX_MODEL_DATA_LINK,
    MDX_MODEL_NAME_DATA_LINK,
    NO_CODE,
    NO_CONNECTION,
    NO_MODEL,
    NO_NEW_MODELS,
    NO_TEXT,
    NORMAL_REPO,
    ONNX,
    OPERATING_SYSTEM,
    OPT_SEPARATOR,
    READ_ONLY,
    ROLL_BACK_TEXT,
    SELECT_SAVED_ENSEMBLE,
    SELECT_SAVED_SET,
    SINGLE_DOWNLOAD,
    SUPPORT_UVR_TEXT,
    SYSTEM_ARCH,
    SYSTEM_PROC,
    UPDATE_CONFIRMATION_TEXT,
    UPDATE_FOUND_TEXT,
    UPDATE_LINUX_REPO,
    UPDATE_MAC_ARM_REPO,
    UPDATE_MAC_X86_64_REPO,
    UPDATE_REPO,
    USER_DOWNLOAD_CODES_TEXT,
    UVR_PATREON_LINK_TEXT,
    VIP_REPO,
    VIP_SELECTION,
    VR_ARCH_TYPE,
    VR_MODEL_DATA_LINK,
    YES_TEXT,
)
from gui_data.error_handling import error_text
from uvr.constants import (
    BASE_PATH,
    CR_TEXT,
    DEMUCS_MODEL_NAME_SELECT,
    DEMUCS_MODELS_DIR,
    DEMUCS_NEWER_REPO_DIR,
    IS_WINDOWS,
    MAIN_FONT_NAME,
    MDX_C_CONFIG_PATH,
    MDX_HASH_DIR,
    MDX_HASH_JSON,
    MDX_MODEL_NAME_SELECT,
    MDX_MODELS_DIR,
    PREVIOUS_PATCH_WIN,
    VR_HASH_JSON,
    VR_MODELS_DIR,
)
from uvr.core.settings import load_model_hash_data
from uvr.ui.components.tooltip import ToolTip

logger = logging.getLogger(__name__)

if OPERATING_SYSTEM == "Darwin":
    CURRENT_PATCH = PATCH_MAC
    APPLICATION_EXTENSION = ".dmg"
elif OPERATING_SYSTEM == "Linux":
    CURRENT_PATCH = PATCH_LINUX
    APPLICATION_EXTENSION = ".zip"
else:
    CURRENT_PATCH = PATCH
    APPLICATION_EXTENSION = ".exe"


def read_bulliten_text_mac(path: str, data: str) -> str:
    """Write bulletin data to file and read back replacing formatting characters."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

        if os.path.isfile(path):
            with open(path, encoding="utf-8") as file:
                data = file.read().replace("~", "•")
    except Exception:
        data = "No information available."

    return data


def vip_downloads(password: str, link_type: Any = VIP_REPO) -> str:
    """Attempts to decrypt VIP model link with given input code."""
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=link_type[0],
            iterations=390000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(bytes(password, "utf-8")))
        f = Fernet(key)

        return str(f.decrypt(link_type[1]), "UTF-8")
    except Exception:
        return NO_CODE


class DownloadManager:
    """Manages update checks, model catalog downloads, and model file deletions."""

    def __init__(self, root: Any) -> None:
        self.root = root

    def deletion_list_fill(
        self,
        option_menu: Any,
        selection_var: tk.StringVar,
        selection_dir: str,
        var_set: str,
        menu_name: str | None = None,
    ) -> None:
        """Fills the saved settings menu located in tab 2 of the main settings window."""

        def command_callback(event: Any = None) -> None:
            self.deletion_entry(selection_var.get(), selection_dir, refresh_menu)
            selection_var.set(var_set)

        def refresh_menu(remove: str | None = None) -> None:
            selection_list = (
                self.root.last_found_ensembles
                if menu_name == "deleteensemble"
                else self.root.last_found_settings
            )
            main_var = (
                self.root.chosen_ensemble_var
                if menu_name == "deleteensemble"
                else self.root.save_current_settings_var
            )

            if remove and remove in selection_list:
                selection_list = list(selection_list)
                selection_list.remove(remove)
                main_var.set(CHOOSE_ENSEMBLE_OPTION)

            self.root.update_menus(
                option_widget=option_menu,
                style_name=menu_name,
                command=command_callback,
                new_items=selection_list,
            )

        refresh_menu()

    def deletion_entry(self, selection: str, path: str, callback: Any) -> None:
        """Deletes selected user saved application settings."""
        if selection not in [SELECT_SAVED_SET, SELECT_SAVED_ENSEMBLE]:
            saved_path = os.path.join(path, f'{selection.replace(" ", "_")}.json')
            confirm = self.root.message_box(DELETE_ENS_ENTRY)
            if confirm:
                if os.path.isfile(saved_path):
                    os.remove(saved_path)
                    callback(selection)

    def update_delete_model_list(self, remove: str | None = None) -> None:
        """Refreshes the delete model dropdown list with currently available models."""
        model_list = []
        try:
            for process_method, widget in [
                (VR_ARCH_TYPE, getattr(self.root, "vr_model_Option", None)),
                (MDX_ARCH_TYPE, getattr(self.root, "mdx_net_model_Option", None)),
                (DEMUCS_ARCH_TYPE, getattr(self.root, "demucs_model_Option", None)),
            ]:
                if widget:
                    models = widget.cget("values")
                    if models:
                        if isinstance(models, str):
                            models = self.root.tk.splitlist(models)
                        for model in models:
                            if model and model not in [CHOOSE_MODEL, OPT_SEPARATOR, DOWNLOAD_MORE]:
                                model_list.append(f"[{process_method}] {model}")
        except Exception:
            pass

        model_list = natsort.natsorted(model_list)
        if remove and remove in model_list:
            model_list.remove(remove)

        if hasattr(self.root, "delete_model_Option"):
            self.root.delete_model_Option["values"] = model_list
            if not self.root.delete_model_Option.bind("<<ComboboxSelected>>"):
                self.root.delete_model_Option.bind(
                    "<<ComboboxSelected>>",
                    lambda e: self.delete_model_command(self.root.delete_model_var.get()),
                )

    def delete_model_command(self, selection: str) -> None:
        """Prompts confirmation and permanently deletes selected model file and metadata."""
        if not selection or selection == "Select Model to Delete":
            return

        confirm = self.root.message_box(DELETE_MODEL_CONFIRM_TEXT)
        if confirm:
            try:
                process_method = selection.split("] ")[0][1:]
                model_name = selection.split("] ", 1)[1]

                model_path = None

                if process_method == VR_ARCH_TYPE:
                    model_path = os.path.join(VR_MODELS_DIR, f"{model_name}.pth")
                elif process_method == MDX_ARCH_TYPE:
                    for file_name, names in self.root.mdx_name_select_MAPPER.items():
                        if model_name == names:
                            ext = (
                                ""
                                if file_name.endswith((CKPT, ".safetensors", ONNX, ".pth"))
                                else ONNX
                            )
                            model_path = os.path.join(MDX_MODELS_DIR, f"{file_name}{ext}")
                            break
                    if not model_path:
                        for ext in ["", ONNX, CKPT, ".safetensors", ".pth"]:
                            p = os.path.join(MDX_MODELS_DIR, f"{model_name}{ext}")
                            if os.path.isfile(p):
                                model_path = p
                                break
                elif process_method == DEMUCS_ARCH_TYPE:
                    for file_name, name in self.root.demucs_name_select_MAPPER.items():
                        if model_name == name:
                            demucs_newer = any(tag in model_name for tag in DEMUCS_NEWER_TAGS)
                            d = DEMUCS_NEWER_REPO_DIR if demucs_newer else DEMUCS_MODELS_DIR
                            model_path = os.path.join(d, file_name)
                            break
                    if not model_path:
                        for d in [DEMUCS_NEWER_REPO_DIR, DEMUCS_MODELS_DIR]:
                            for candidate in os.listdir(d) if os.path.isdir(d) else []:
                                base = os.path.splitext(candidate)[0]
                                if base == model_name or candidate == model_name:
                                    model_path = os.path.join(d, candidate)
                                    break
                            if model_path:
                                break

                if model_path and os.path.exists(model_path):
                    model_hash = None
                    if os.path.isfile(model_path):
                        try:
                            import hashlib

                            with open(model_path, "rb") as f:
                                f.seek(-10000 * 1024, 2)
                                model_hash = hashlib.md5(f.read()).hexdigest()
                        except Exception:
                            pass
                        os.remove(model_path)
                        if model_path.endswith(".yaml"):
                            yaml_dir = os.path.dirname(model_path)
                            for th_file in os.listdir(yaml_dir):
                                if th_file.endswith(".th"):
                                    try:
                                        os.remove(os.path.join(yaml_dir, th_file))
                                    except Exception:
                                        pass
                    elif os.path.isdir(model_path):
                        import shutil

                        shutil.rmtree(model_path)

                    if model_hash:
                        hash_json = os.path.join(MDX_HASH_DIR, f"{model_hash}.json")
                        if os.path.isfile(hash_json):
                            os.remove(hash_json)

                    self.root.update_available_models()
                    self.update_delete_model_list(remove=selection)
                    self.root.delete_model_var.set("Select Model to Delete")
                    messagebox.showinfo(
                        "Model Deleted",
                        f"Model '{model_name}' has been successfully deleted.",
                        parent=self.root,
                    )
                else:
                    messagebox.showwarning(
                        "Model Not Found",
                        f"Model file for '{model_name}' was not found.",
                        parent=self.root,
                    )
                    self.root.delete_model_var.set("Select Model to Delete")

            except Exception as e:
                self.root.error_log_var.set(error_text("Error Deleting Model", e))
        else:
            self.root.delete_model_var.set("Select Model to Delete")

    def _inject_community_name_mappings(self) -> None:
        """Injects custom community model name mappings into the MDX name mapper."""
        custom_mappings = {
            "mini-bs-roformer-v2-46.8M.safetensors": "Mini-BS-Roformer-V2-46.8M",
            "becruily_guitar.ckpt": "MB-Ro-Guitar-Becruily",
            "gilliaan_drumsV1.ckpt": "BS-Ro-Drums-Gilliaan",
            "bs_roformer_4stems_ft.pth": "BS-Ro-4Stems-SYH99999",
            "deverb_bs_roformer_8_256dim_8depth.ckpt": "BS-Ro-Dereverb-Old",
            "dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt": "BS-Ro-Dereverb-Anvuew",
            "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt": "MB-Ro-Denoise-Poiqazwsx",
            "model_BandSplit-Roformer_SW_by-jarredou.ckpt": "BS-Ro-SW-6Stems-Jarredou",
        }
        self.root.mdx_name_select_MAPPER.update(custom_mappings)

    def offline_state_set(self, is_start_up: bool = False) -> None:
        """Changes relevant settings and Download Center buttons if offline."""
        if not is_start_up and self.root.is_menu_settings_open:
            self.root.app_update_status_Text_var.set(f"Version Status: {NO_CONNECTION}")
            self.root.download_progress_info_var.set(NO_CONNECTION)
            self.root.app_update_button_Text_var.set("Refresh")
            self.root.refresh_list_Button.configure(state=tk.NORMAL)
            self.root.stop_download_Button_DISABLE()
            self.root.enable_tabs()

        self.root.is_online = False

    def online_data_refresh(
        self,
        user_refresh: bool = True,
        confirmation_box: bool = False,
        refresh_list_Button: bool = False,
        is_start_up: bool = False,
        is_download_complete: bool = False,
    ) -> bool:
        """Checks for application updates and refreshes downloadable model lists."""

        def online_check() -> bool:
            if not is_start_up:
                self.root.app_update_status_Text_var.set(LOADING_VERSION_INFO_TEXT)
                self.root.app_update_button_Text_var.set(CHECK_FOR_UPDATES_TEXT)

            is_new_update = False
            try:
                self.root.online_data = json.load(urllib.request.urlopen(DOWNLOAD_CHECKS))

                local_community_models = {
                    "Roformer Model: MB-Ro-Guitar-Becruily": {
                        "becruily_guitar.ckpt": "https://huggingface.co/becruily/mel-band-roformer-guitar/resolve/main/becruily_guitar.ckpt"
                    },
                    "Roformer Model: BS-Ro-Drums-Gilliaan": {
                        "gilliaan_drumsV1.ckpt": "https://huggingface.co/oulianov/BS-Roformer-DrumsOther-Duality/resolve/main/gilliaan_drumsV1.ckpt"
                    },
                    "Roformer Model: BS-Ro-4Stems-SYH99999": {
                        "bs_roformer_4stems_ft.pth": "https://huggingface.co/SYH99999/bs_roformer_4stems_ft/resolve/main/bs_roformer_4stems_ft.pth"
                    },
                }
                if "roformer_download_list" not in self.root.online_data:
                    self.root.online_data["roformer_download_list"] = {}
                self.root.online_data["roformer_download_list"].update(local_community_models)

                self.root.is_online = True

                try:
                    with urllib.request.urlopen(BULLETIN_CHECK) as response:
                        self.root.bulletin_data = response.read().decode("utf-8")

                    if not IS_WINDOWS:
                        self.root.bulletin_data = read_bulliten_text_mac(
                            CR_TEXT, self.root.bulletin_data
                        )
                    else:
                        self.root.bulletin_data = self.root.bulletin_data.replace("~", "•")

                except Exception as e:
                    self.root.bulletin_data = INFO_UNAVAILABLE_TEXT
                    print(e)

                if user_refresh:
                    self.download_list_state()
                    for widget in self.root.download_center_Buttons:
                        widget.configure(state=tk.NORMAL)

                if refresh_list_Button:
                    self.root.download_progress_info_var.set("Download List Refreshed!")

                if OPERATING_SYSTEM == "Darwin":
                    self.root.lastest_version = self.root.online_data["current_version_mac"]
                elif OPERATING_SYSTEM == "Linux":
                    self.root.lastest_version = self.root.online_data["current_version_linux"]
                else:
                    self.root.lastest_version = self.root.online_data["current_version"]

                if self.root.lastest_version == CURRENT_PATCH and not is_start_up:
                    self.root.app_update_status_Text_var.set("UVR Version Current")
                else:
                    is_new_update = True
                    is_beta_version = (
                        True
                        if self.root.lastest_version == PREVIOUS_PATCH_WIN
                        and BETA_VERSION in CURRENT_PATCH
                        else False
                    )

                    if not is_start_up:
                        if is_beta_version:
                            self.root.app_update_status_Text_var.set(
                                f"Roll Back: {self.root.lastest_version}"
                            )
                            self.root.app_update_button_Text_var.set(ROLL_BACK_TEXT)
                        else:
                            self.root.app_update_status_Text_var.set(
                                f"Update Found: {self.root.lastest_version}"
                            )
                            self.root.app_update_button_Text_var.set("Click Here to Update")

                        if OPERATING_SYSTEM == "Windows":
                            self.root.download_update_link_var.set(
                                f"{UPDATE_REPO}{self.root.lastest_version}{APPLICATION_EXTENSION}"
                            )
                            self.root.download_update_path_var.set(
                                os.path.join(
                                    BASE_PATH,
                                    f"{self.root.lastest_version}{APPLICATION_EXTENSION}",
                                )
                            )
                        elif OPERATING_SYSTEM == "Darwin":
                            self.root.download_update_link_var.set(
                                UPDATE_MAC_ARM_REPO
                                if SYSTEM_PROC == ARM or ARM in SYSTEM_ARCH
                                else UPDATE_MAC_X86_64_REPO
                            )
                        elif OPERATING_SYSTEM == "Linux":
                            self.root.download_update_link_var.set(UPDATE_LINUX_REPO)

                is_update_params = (
                    self.root.is_auto_update_model_params
                    if is_start_up
                    else self.root.is_auto_update_model_params_var.get()
                )

                if (is_update_params and is_start_up) or is_download_complete:
                    self.download_model_settings()

            except Exception as e:
                self.offline_state_set(is_start_up)
                is_new_update = False

                if user_refresh:
                    self.download_list_state(disable_only=True)
                    for widget in self.root.download_center_Buttons:
                        widget.configure(state=tk.DISABLED)

                try:
                    self.root.error_log_var.set(error_text("Online Data Refresh", e))
                except Exception as ex:
                    print(ex)

            return is_new_update

        if confirmation_box:
            return online_check()

        self.root.current_thread = KThread(target=online_check)
        if not IS_WINDOWS:
            self.root.current_thread.setDaemon(True)
        self.root.current_thread.start()
        return False

    def download_validate_code(self, confirm: bool = False, code_message: Any = None) -> None:
        """Verifies VIP download code and adds VIP model catalog."""
        self.root.decoded_vip_link = vip_downloads(self.root.user_code_var.get())

        if confirm:
            if self.root.decoded_vip_link != NO_CODE:
                info_text = "VIP Models Added!"
                is_success_message = True
            else:
                info_text = "Incorrect Code"
                is_success_message = False

            self.root.download_progress_info_var.set(info_text)
            self.root.user_code_validation_var.set(info_text)

            if code_message:
                code_message(info_text, is_success_message)

            self.download_list_fill()

    def download_list_fill(self, model_type: str = ALL_TYPES) -> None:
        """Fills download dropdown menus with catalog items retrieved from online check."""
        self.root.download_demucs_models_list.clear()

        model_download_mdx_list, model_download_mdx_name = [], "mdxdownload"
        model_download_vr_list, model_download_vr_name = [], "vrdownload"
        model_download_demucs_list, model_download_demucs_name = [], "demucsmdxdownload"

        self.root.vr_download_list = self.root.online_data.get("vr_download_list", {})
        self.root.mdx_download_list = self.root.online_data.get("mdx_download_list", {})
        self.root.demucs_download_list = self.root.online_data.get("demucs_download_list", {})
        self.root.mdx_download_list.update(self.root.online_data.get("mdx23c_download_list", {}))
        self.root.mdx_download_list.update(self.root.online_data.get("roformer_download_list", {}))
        self.root.mdx_download_list.update(self.root.online_data.get("other_network_list", {}))
        self.root.mdx_download_list.update(self.root.online_data.get("other_network_list_new", {}))

        deverb_key = "Roformer Model: BS Roformer Dereverb | (anvuew edition)"
        self.root.mdx_download_list[deverb_key] = {
            "dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt": "https://huggingface.co/anvuew/dereverb_bs_roformer/resolve/main/dereverb_bs_roformer_anvuew_sdr_22.5050.ckpt",
            "dereverb_bs_roformer_anvuew_sdr_22.5050.yaml": "https://huggingface.co/anvuew/dereverb_bs_roformer/resolve/main/config.yaml",
        }

        self.root.mdx_download_list.update(
            {
                "Roformer Model: MelBand Roformer Denoise | (poiqazwsx)": {
                    "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt": "https://huggingface.co/poiqazwsx/melband-roformer-denoise/resolve/main/denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt",
                    "model_mel_band_roformer_denoise.yaml": "https://huggingface.co/poiqazwsx/melband-roformer-denoise/resolve/main/model_mel_band_roformer_denoise.yaml",
                },
                "Roformer Model: BandSplit Roformer SW 6-Stems | (jarredou)": {
                    "model_BandSplit-Roformer_SW_by-jarredou.ckpt": "https://huggingface.co/cdjmix1991/bandsplit-roformer-sw-by-jarredou/resolve/main/model_BandSplit-Roformer_SW_by-jarredou.ckpt",
                    "config_BandSplit-Roformer_SW_by-jarredou.yaml": "https://huggingface.co/cdjmix1991/bandsplit-roformer-sw-by-jarredou/resolve/main/config_BandSplit-Roformer_SW_by-jarredou.yaml",
                },
            }
        )

        if self.root.decoded_vip_link is not NO_CODE:
            self.root.vr_download_list.update(self.root.online_data.get("vr_download_vip_list", {}))
            self.root.mdx_download_list.update(
                self.root.online_data.get("mdx_download_vip_list", {})
            )
            self.root.mdx_download_list.update(
                self.root.online_data.get("mdx23c_download_vip_list", {})
            )

        def configure_combobox(
            combobox: Any, values: list[str], variable: tk.StringVar, arch_type: str, name: str
        ) -> None:
            values = [NO_NEW_MODELS] if not values else values
            combobox["values"] = values
            combobox.update_dropdown_size(
                values,
                name,
                offset=310,
                command=lambda s: self.download_model_select(
                    variable.get(), arch_type, variable
                ),
            )

        if model_type in [VR_ARCH_TYPE, ALL_TYPES]:
            for selectable, model in self.root.vr_download_list.items():
                if not os.path.isfile(os.path.join(VR_MODELS_DIR, model)):
                    model_download_vr_list.append(selectable)

            configure_combobox(
                self.root.model_download_vr_Option,
                model_download_vr_list,
                self.root.model_download_vr_var,
                VR_ARCH_TYPE,
                model_download_vr_name,
            )

        if model_type in [MDX_ARCH_TYPE, ALL_TYPES]:
            for selectable, model in self.root.mdx_download_list.items():
                if isinstance(model, dict):
                    model_name = list(model.keys())[0]
                    config_filename = None
                    config_link = None
                    for key, val in model.items():
                        if key.endswith(".yaml") or key.endswith(".json"):
                            config_filename = key
                            config_link = (
                                val if val.startswith("http") else f"{MDX23_CONFIG_CHECKS}{val}"
                            )
                        elif (
                            key.endswith(CKPT)
                            or key.endswith(".safetensors")
                            or key.endswith(ONNX)
                            or key.endswith(".pth")
                        ):
                            model_name = key
                            if val.endswith(".yaml") or val.endswith(".json"):
                                config_filename = val
                                config_link = f"{MDX23_CONFIG_CHECKS}{val}"

                    if config_filename and config_link:
                        config_local = os.path.join(MDX_C_CONFIG_PATH, config_filename)
                        if not os.path.isfile(config_local):
                            try:
                                with urllib.request.urlopen(config_link) as response:
                                    with open(config_local, "wb") as out_file:
                                        out_file.write(response.read())
                            except Exception as e:
                                print(f"Error downloading config for {selectable}: {e}")
                else:
                    model_name = str(model)

                if not os.path.isfile(os.path.join(MDX_MODELS_DIR, model_name)):
                    model_download_mdx_list.append(selectable)

            configure_combobox(
                self.root.model_download_mdx_Option,
                model_download_mdx_list,
                self.root.model_download_mdx_var,
                MDX_ARCH_TYPE,
                model_download_mdx_name,
            )

        if model_type in [DEMUCS_ARCH_TYPE, ALL_TYPES]:
            for selectable, model in self.root.demucs_download_list.items():
                for name in model.items():
                    if [True for x in DEMUCS_NEWER_ARCH_TYPES if x in selectable]:
                        if not os.path.isfile(os.path.join(DEMUCS_NEWER_REPO_DIR, name[0])):
                            self.root.download_demucs_models_list.append(selectable)
                    else:
                        if not os.path.isfile(os.path.join(DEMUCS_MODELS_DIR, name[0])):
                            self.root.download_demucs_models_list.append(selectable)

            self.root.download_demucs_models_list = list(
                dict.fromkeys(self.root.download_demucs_models_list)
            )

            for option_name in self.root.download_demucs_models_list:
                model_download_demucs_list.append(option_name)

            configure_combobox(
                self.root.model_download_demucs_Option,
                model_download_demucs_list,
                self.root.model_download_demucs_var,
                DEMUCS_ARCH_TYPE,
                model_download_demucs_name,
            )

    def download_model_settings(self) -> None:
        """Update and persist latest online model hash mappings."""
        try:
            self.root.vr_hash_MAPPER = json.load(urllib.request.urlopen(VR_MODEL_DATA_LINK))
            self.root.mdx_hash_MAPPER = json.load(urllib.request.urlopen(MDX_MODEL_DATA_LINK))
            self.root.mdx_name_select_MAPPER = json.load(
                urllib.request.urlopen(MDX_MODEL_NAME_DATA_LINK)
            )
            self.root.demucs_name_select_MAPPER = json.load(
                urllib.request.urlopen(DEMUCS_MODEL_NAME_DATA_LINK)
            )

            if "mdx23c_download_list" in self.root.online_data:
                for name, data in self.root.online_data["mdx23c_download_list"].items():
                    if isinstance(data, dict):
                        for filename in data.keys():
                            self.root.mdx_name_select_MAPPER[filename] = name

            self._inject_community_name_mappings()

            for k, v in self.root.mdx_name_select_MAPPER.items():
                if v.startswith(f"{MDX_23_NAME}: "):
                    self.root.mdx_name_select_MAPPER[k] = v.replace(f"{MDX_23_NAME}: ", "")

            with open(VR_HASH_JSON, "w", encoding="utf-8") as outfile:
                outfile.write(json.dumps(self.root.vr_hash_MAPPER, indent=4))

            with open(MDX_HASH_JSON, "w", encoding="utf-8") as outfile:
                outfile.write(json.dumps(self.root.mdx_hash_MAPPER, indent=4))

            with open(MDX_MODEL_NAME_SELECT, "w", encoding="utf-8") as outfile:
                outfile.write(json.dumps(self.root.mdx_name_select_MAPPER, indent=4))

            with open(DEMUCS_MODEL_NAME_SELECT, "w", encoding="utf-8") as outfile:
                outfile.write(json.dumps(self.root.demucs_name_select_MAPPER, indent=4))

        except Exception as e:
            self.root.vr_hash_MAPPER = load_model_hash_data(VR_HASH_JSON)
            self.root.mdx_hash_MAPPER = load_model_hash_data(MDX_HASH_JSON)
            self.root.mdx_name_select_MAPPER = load_model_hash_data(MDX_MODEL_NAME_SELECT)
            self.root.demucs_name_select_MAPPER = load_model_hash_data(DEMUCS_MODEL_NAME_SELECT)
            self.root.error_log_var.set(e)
            print(e)

    def download_list_state(self, reset: bool = True, disable_only: bool = False) -> None:
        """Sets download widget enabled/disabled states based on selected architecture."""
        for widget in self.root.download_lists:
            widget.configure(state=tk.DISABLED)

        if reset:
            for download_list_var in self.root.download_list_vars:
                if self.root.is_online:
                    download_list_var.set(NO_MODEL)
                    self.root.download_Button.configure(state=tk.NORMAL)
                else:
                    download_list_var.set(NO_CONNECTION)
                    self.root.download_Button.configure(state=tk.DISABLED)
                    disable_only = True

        if not disable_only:
            self.root.download_Button.configure(state=tk.NORMAL)
            if self.root.select_download_var.get() == VR_ARCH_TYPE:
                self.root.model_download_vr_Option.configure(state=READ_ONLY)
                self.root.selected_download_var = self.root.model_download_vr_var
                self.download_list_fill(model_type=VR_ARCH_TYPE)
            if self.root.select_download_var.get() == MDX_ARCH_TYPE:
                self.root.model_download_mdx_Option.configure(state=READ_ONLY)
                self.root.selected_download_var = self.root.model_download_mdx_var
                self.download_list_fill(model_type=MDX_ARCH_TYPE)
            if self.root.select_download_var.get() == DEMUCS_ARCH_TYPE:
                self.root.model_download_demucs_Option.configure(state=READ_ONLY)
                self.root.selected_download_var = self.root.model_download_demucs_var
                self.download_list_fill(model_type=DEMUCS_ARCH_TYPE)

            self.root.stop_download_Button_DISABLE()

    def download_model_select(self, selection: str, model_type: str, var: tk.StringVar) -> None:
        """Prepares download paths and URLs for the selected model."""
        self.root.download_demucs_newer_models.clear()

        if selection == NO_NEW_MODELS:
            selection = NO_MODEL
            var.set(NO_MODEL)

        model_repo = (
            self.root.decoded_vip_link if VIP_SELECTION in selection else NORMAL_REPO
        )
        is_demucs_newer = [True for x in DEMUCS_NEWER_ARCH_TYPES if x in selection]

        if model_type == VR_ARCH_TYPE:
            for selected_model in self.root.vr_download_list.items():
                if selection in selected_model:
                    self.root.download_link_path_var.set(f"{model_repo}{selected_model[1]}")
                    self.root.download_save_path_var.set(
                        os.path.join(VR_MODELS_DIR, selected_model[1])
                    )
                    break

        if model_type == MDX_ARCH_TYPE:
            for selected_model in self.root.mdx_download_list.items():
                if selection in selected_model:
                    if isinstance(selected_model[1], dict):
                        model_name = list(selected_model[1].keys())[0]
                        download_link = f"{model_repo}{model_name}"
                        for key, val in selected_model[1].items():
                            if (
                                key.endswith(CKPT)
                                or key.endswith(".safetensors")
                                or key.endswith(ONNX)
                                or key.endswith(".pth")
                            ):
                                model_name = key
                                if val.startswith("http"):
                                    download_link = val
                                break
                    else:
                        model_name = str(selected_model[1])
                        download_link = f"{model_repo}{model_name}"
                    self.root.download_link_path_var.set(download_link)
                    self.root.download_save_path_var.set(os.path.join(MDX_MODELS_DIR, model_name))
                    break

        if model_type == DEMUCS_ARCH_TYPE:
            for selected_model, model_data in self.root.demucs_download_list.items():
                if selection == selected_model:
                    for key, value in model_data.items():
                        if is_demucs_newer:
                            self.root.download_demucs_newer_models.append(
                                [os.path.join(DEMUCS_NEWER_REPO_DIR, key), value]
                            )
                        else:
                            self.root.download_save_path_var.set(
                                os.path.join(DEMUCS_MODELS_DIR, key)
                            )
                            self.root.download_link_path_var.set(value)

    def download_item(self, is_update_app: bool = False) -> None:
        """Downloads the selected model or application update file."""
        if not is_update_app:
            if self.root.selected_download_var.get() == NO_MODEL:
                self.root.download_progress_info_var.set(NO_MODEL)
                return

        for widget in self.root.download_center_Buttons:
            widget.configure(state=tk.DISABLED)
        self.root.refresh_list_Button.configure(state=tk.DISABLED)
        self.root.manual_download_Button.configure(state=tk.DISABLED)

        is_demucs_newer = [
            True
            for x in DEMUCS_NEWER_ARCH_TYPES
            if x in self.root.selected_download_var.get()
        ]

        self.download_list_state(reset=False, disable_only=True)
        self.root.stop_download_Button_ENABLE()
        self.root.disable_tabs()

        def download_progress_bar(current: int, total: int, model: int = 80) -> None:
            progress = "%s" % (100 * current // total)
            self.root.download_progress_bar_var.set(int(progress))
            self.root.download_progress_percent_var.set(progress + " %")

        def robust_download(url: str, save_path: str, bar_fn: Any) -> None:
            """Download with fallback chain: wget -> requests -> urllib."""
            def _stream_with_requests(dl_url: str, dest_path: str) -> None:
                import requests as _req

                headers = {
                    "User-Agent": "Mozilla/5.0 (UVR/5.6; Linux; compatible)",
                    "Accept": "*/*",
                }
                with _req.get(
                    dl_url, stream=True, headers=headers, timeout=60, allow_redirects=True
                ) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("Content-Length", 0))
                    downloaded = 0
                    chunk_size = 1024 * 64
                    with open(dest_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if bar_fn and total:
                                    bar_fn(downloaded, total)

            is_hf_url = "huggingface.co" in url
            if is_hf_url:
                try:
                    _stream_with_requests(url, save_path)
                    return
                except Exception:
                    if os.path.isfile(save_path):
                        os.remove(save_path)

            try:
                wget.download(url, save_path, bar=bar_fn)
            except Exception as wget_err:
                if os.path.isfile(save_path):
                    os.remove(save_path)
                try:
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (UVR/5.6; compatible)"},
                    )
                    with urllib.request.urlopen(req) as response:
                        total = int(response.headers.get("Content-Length", 0))
                        downloaded = 0
                        with open(save_path, "wb") as out_file:
                            while True:
                                chunk = response.read(1024 * 64)
                                if not chunk:
                                    break
                                out_file.write(chunk)
                                downloaded += len(chunk)
                                if bar_fn and total:
                                    bar_fn(downloaded, total)
                except Exception as urllib_err:
                    raise wget_err from urllib_err

        def push_download() -> None:
            self.root.is_download_thread_active = True
            try:
                if is_update_app:
                    self.root.download_progress_info_var.set(DOWNLOADING_UPDATE)
                    if os.path.isfile(self.root.download_update_path_var.get()):
                        self.root.download_progress_info_var.set(FILE_EXISTS)
                    else:
                        robust_download(
                            self.root.download_update_link_var.get(),
                            self.root.download_update_path_var.get(),
                            download_progress_bar,
                        )

                    self.download_post_action(DOWNLOAD_UPDATE_COMPLETE)
                else:
                    if (
                        self.root.select_download_var.get() == DEMUCS_ARCH_TYPE
                        and is_demucs_newer
                    ):
                        for model_num, model_data in enumerate(
                            self.root.download_demucs_newer_models, start=1
                        ):
                            self.root.download_progress_info_var.set(
                                f"{DOWNLOADING_ITEM} {model_num}/{len(self.root.download_demucs_newer_models)}..."
                            )
                            if os.path.isfile(model_data[0]):
                                continue
                            robust_download(
                                model_data[1], model_data[0], download_progress_bar
                            )
                    else:
                        self.root.download_progress_info_var.set(SINGLE_DOWNLOAD)
                        if os.path.isfile(self.root.download_save_path_var.get()):
                            self.root.download_progress_info_var.set(FILE_EXISTS)
                        else:
                            robust_download(
                                self.root.download_link_path_var.get(),
                                self.root.download_save_path_var.get(),
                                download_progress_bar,
                            )

                    self.download_post_action(DOWNLOAD_COMPLETE)

            except Exception as e:
                self.root.error_log_var.set(error_text(DOWNLOADING_ITEM, e))
                self.root.download_progress_info_var.set(DOWNLOAD_FAILED)

                if type(e).__name__ == "URLError":
                    self.offline_state_set()
                else:
                    self.root.download_progress_percent_var.set(f"{type(e).__name__}")
                    self.download_post_action(DOWNLOAD_FAILED)

        self.root.active_download_thread = KThread(target=push_download)
        self.root.active_download_thread.start()

    def download_post_action(self, action: str) -> None:
        """Resets download widget states following download completion, cancellation, or failure."""
        for widget in self.root.download_center_Buttons:
            widget.configure(state=tk.NORMAL)
        self.root.refresh_list_Button.configure(state=tk.NORMAL)
        self.root.manual_download_Button.configure(state=tk.NORMAL)

        self.root.enable_tabs()
        self.root.stop_download_Button_DISABLE()

        if action == DOWNLOAD_FAILED:
            try:
                self.root.active_download_thread.terminate()
            finally:
                self.root.download_progress_info_var.set(DOWNLOAD_FAILED)
                self.download_list_state(reset=False)
        elif action == DOWNLOAD_STOPPED:
            try:
                self.root.active_download_thread.terminate()
            finally:
                self.root.download_progress_info_var.set(DOWNLOAD_STOPPED)
                self.download_list_state(reset=False)
        elif action == DOWNLOAD_COMPLETE:
            self.online_data_refresh(is_download_complete=True)
            self.root.download_progress_info_var.set(DOWNLOAD_COMPLETE)
            self.download_list_state()
        elif action == DOWNLOAD_UPDATE_COMPLETE:
            self.root.download_progress_info_var.set(DOWNLOAD_UPDATE_COMPLETE)
            if os.path.isfile(self.root.download_update_path_var.get()):
                subprocess.Popen(self.root.download_update_path_var.get())
            self.download_list_state()

        self.root.is_download_thread_active = False
        self.root.delete_temps()

    def pop_up_update_confirmation(self) -> None:
        """Ask user if they want to update."""
        is_new_update = self.online_data_refresh(confirmation_box=True)
        is_download_in_app_var = tk.BooleanVar(value=False)

        def update_type():
            if is_download_in_app_var.get():
                self.download_item(is_update_app=True)
            else:
                webbrowser.open_new_tab(self.root.download_update_link_var.get())

            update_confirmation_win.destroy()

        if is_new_update:
            update_confirmation_win = tk.Toplevel()

            update_confirmation_Frame = self.root.menu_FRAME_SET(update_confirmation_win)
            update_confirmation_Frame.grid(row=0)

            update_found_label = self.root.menu_title_LABEL_SET(update_confirmation_Frame, UPDATE_FOUND_TEXT, width=15)
            update_found_label.grid(row=0, column=0, padx=0, pady=MENU_PADDING_2)

            confirm_update_label = self.root.menu_sub_LABEL_SET(update_confirmation_Frame, UPDATE_CONFIRMATION_TEXT, font_size=FONT_SIZE_3)
            confirm_update_label.grid(row=1, column=0, padx=0, pady=MENU_PADDING_1)

            yes_button = ttk.Button(update_confirmation_Frame, text=YES_TEXT, command=update_type)
            yes_button.grid(row=2, column=0, padx=0, pady=MENU_PADDING_1)

            no_button = ttk.Button(update_confirmation_Frame, text=NO_TEXT, command=lambda: update_confirmation_win.destroy())
            no_button.grid(row=3, column=0, padx=0, pady=MENU_PADDING_1)

            if IS_WINDOWS:
                download_outside_application_button = ttk.Checkbutton(update_confirmation_Frame, variable=is_download_in_app_var, text="Download Update in Application")
                download_outside_application_button.grid(row=4, column=0, padx=0, pady=MENU_PADDING_1)

            self.root.menu_placement(update_confirmation_win, CONFIRM_UPDATE_TEXT, pop_up=True)

    def pop_up_user_code_input(self) -> None:
        """Input VIP Code dialog."""
        self.root.user_code_validation_var.set("")

        self.root.user_code = tk.Toplevel()

        user_code_Frame = self.root.menu_FRAME_SET(self.root.user_code)
        user_code_Frame.grid(row=0)

        user_code_title_Label = self.root.menu_title_LABEL_SET(user_code_Frame, USER_DOWNLOAD_CODES_TEXT, width=20)
        user_code_title_Label.grid(row=0, column=0, padx=0, pady=MENU_PADDING_1)

        user_code_Label = self.root.menu_sub_LABEL_SET(user_code_Frame, DOWNLOAD_CODE_TEXT)
        user_code_Label.grid(pady=MENU_PADDING_1)

        self.root.user_code_Entry = ttk.Entry(user_code_Frame, textvariable=self.root.user_code_var, justify="center")
        self.root.user_code_Entry.grid(pady=MENU_PADDING_1)
        self.root.user_code_Entry.bind(self.root.right_click_button, self.root.right_click_menu_popup)
        self.root.current_text_box = self.root.user_code_Entry

        tooltip = ToolTip(self.root.user_code_Entry)

        def invalid_message_(text, is_success_message):
            tooltip.hidetip()
            tooltip.showtip(text, True, is_success_message)

        self.root.spacer_label(user_code_Frame)

        user_code_confrim_Button = ttk.Button(user_code_Frame, text=CONFIRM_TEXT, command=lambda: self.download_validate_code(confirm=True, code_message=invalid_message_))
        user_code_confrim_Button.grid(pady=MENU_PADDING_1)

        user_code_cancel_Button = ttk.Button(user_code_Frame, text=CANCEL_TEXT, command=lambda: self.root.user_code.destroy())
        user_code_cancel_Button.grid(pady=MENU_PADDING_1)

        support_title_Label = self.root.menu_title_LABEL_SET(user_code_Frame, text=SUPPORT_UVR_TEXT, width=20)
        support_title_Label.grid(pady=MENU_PADDING_1)

        support_sub_Label = tk.Label(user_code_Frame, text=GET_DL_VIP_CODE_TEXT, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR)
        support_sub_Label.grid(pady=MENU_PADDING_1)

        uvr_patreon_Button = ttk.Button(user_code_Frame, text=UVR_PATREON_LINK_TEXT, command=lambda: webbrowser.open_new_tab(DONATE_LINK_PATREON))
        uvr_patreon_Button.grid(pady=MENU_PADDING_1)

        bmac_patreon_Button = ttk.Button(user_code_Frame, text=BMAC_UVR_TEXT, command=lambda: webbrowser.open_new_tab(DONATE_LINK_BMAC))
        bmac_patreon_Button.grid(pady=MENU_PADDING_1)

        self.root.menu_placement(self.root.user_code, INPUT_CODE_TEXT, pop_up=True)

