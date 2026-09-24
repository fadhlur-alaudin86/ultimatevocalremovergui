"""Model parameter configuration and customization dialogs for VR and MDX-Net models.
"""

from __future__ import annotations

import json
import logging
import math
import os
import tkinter as tk
import traceback
from tkinter import ttk
from typing import Any

import onnx
import torch

from gui_data.app_size_values import (
    COMBO_WIDTH,
    MENU_PADDING_1,
    MENU_PADDING_2,
    MENU_PADDING_3,
    READ_ONLY_COMBO_WIDTH,
    SET_MENUS_CHECK_WIDTH,
    SET_VOC_SPLIT_CHECK_WIDTH,
)
from gui_data.constants import (
    BALANCE_VALUE_TEXT,
    BALANCE_VALUES,
    BV_MODEL_TEXT,
    CANCEL_TEXT,
    CHANGE_MODEL_DEFAULT_TEXT,
    CHANGE_PARAMETERS_TEXT,
    CHOOSE_MODEL_PARAM_TEXT,
    CKPT,
    CLOSE_WINDOW,
    CONFIRM_TEXT,
    DELETE_PARAMETERS_TEXT,
    DEVERB_MAPPER,
    DEVERB_VOCALS_TEXT,
    ENABLE_VOCAL_SPLIT_MODE_TEXT,
    ENSEMBLE_CHECK,
    INPUT_STEM_NAME,
    INST_STEM,
    INVALID_PARAM_MODEL_ERROR,
    IS_BV_MODEL,
    IS_BV_MODEL_REBAL,
    IS_DEVERB_OPT_HELP,
    IS_DEVERB_VOC_HELP,
    IS_KARAOKEE,
    IS_VOC_SPLIT_INST_SAVE_SELECT_HELP,
    IS_VOC_SPLIT_MODEL_SELECT_HELP,
    JSON,
    KARAOKE_MODEL_TEXT,
    KARAOKEE_CHECK,
    MDXNET_C_MODEL_PARAMETERS_TEXT,
    NO_MODEL,
    NONE_SELECTED,
    NOUT_LSTM_SEL,
    NOUT_SEL,
    ONNX,
    OPERATING_SYSTEM,
    OTHER_STEM,
    PRIMARY_STEM_TEXT,
    READ_ONLY,
    REG_SHIFTS,
    SAVE_SPLIT_VOCAL_INSTRUMENTALS_TEXT,
    SELECT_MODEL_PARAM_TEXT,
    SELECT_MODEL_TEXT,
    SET_STEM_NAME_HELP,
    SPECIFY_MDX_NET_MODEL_PARAMETERS_TEXT,
    SPECIFY_PARAMETERS_TEXT,
    SPECIFY_VR_MODEL_PARAMETERS_TEXT,
    STEM_SET_MENU,
    VOC_SPLIT_MODEL_SELECT_HELP,
    VOCAL_DEVERB_OPTIONS_TEXT,
    VOCAL_SPLIT_MODE_OPTIONS_TEXT,
    VOCAL_SPLIT_OPTIONS_TEXT,
    VOCAL_STEM,
    VR_51_MODEL_TEXT,
    VR_MODEL_PARAM_HELP,
    YAML,
)
from uvr.constants import (
    IS_WINDOWS,
    MDX_C_CONFIG_PATH,
    MDX_HASH_DIR,
    VR_HASH_DIR,
    VR_PARAM_DIR,
)
from uvr.ui.components.combobox_editable import ComboBoxEditableMenu
from uvr.ui.components.combobox_menu import ComboBoxMenu
from uvr.ui.components.tooltip import ToolTip

logger = logging.getLogger(__name__)
is_macos = OPERATING_SYSTEM == "Darwin"


def pop_up_change_model_defaults(root: Any, top_window: Any) -> None:
    """Opens modal dialog to customize or reset default parameters for models."""

    def message_box_(text: str, is_success_message: bool) -> None:
        tooltip.hidetip()
        tooltip.showtip(text, True, is_success_message)

    def delete_entry() -> None:
        model_data = root.assemble_model_data(
            model=change_model_defaults_var.get(),
            arch_type=ENSEMBLE_CHECK,
            is_change_def=True,
            is_get_hash_dir_only=True,
        )[0]
        hash_file = model_data.model_hash_dir
        if hash_file:
            if os.path.isfile(hash_file):
                os.remove(hash_file)
                message_box_("Defined Parameters Deleted", True)
            else:
                message_box_("No Defined Parameters Found", False)

            root.update_checkbox_text()

    def change_default() -> None:
        model_data = root.assemble_model_data(
            model=change_model_defaults_var.get(),
            arch_type=ENSEMBLE_CHECK,
            is_change_def=True,
        )[0]
        if model_data.model_status:
            message_box_("Model Parameters Changed", True)
            root.update_checkbox_text()

    change_model_defaults = tk.Toplevel(root)
    change_model_defaults_var = tk.StringVar(value=NO_MODEL)

    default_change_model_list = list(root.default_change_model_list)
    default_change_model_list.insert(0, NO_MODEL)

    change_model_defaults_frame = root.menu_FRAME_SET(change_model_defaults)
    change_model_defaults_frame.grid(row=1)

    change_model_defaults_title = root.menu_title_LABEL_SET(
        change_model_defaults_frame, CHANGE_MODEL_DEFAULT_TEXT
    )
    change_model_defaults_title.grid()

    model_param_label = root.menu_sub_LABEL_SET(change_model_defaults_frame, SELECT_MODEL_TEXT)
    model_param_label.grid(pady=MENU_PADDING_1)
    model_param_option = ComboBoxMenu(
        change_model_defaults_frame,
        dropdown_name="changemodeldefault",
        textvariable=change_model_defaults_var,
        values=default_change_model_list,
        offset=310,
        width=READ_ONLY_COMBO_WIDTH,
    )
    model_param_option.grid(pady=MENU_PADDING_1)
    tooltip = ToolTip(model_param_option)

    root.spacer_label(change_model_defaults_frame)

    change_params_button = ttk.Button(
        change_model_defaults_frame,
        text=CHANGE_PARAMETERS_TEXT,
        command=change_default,
        width=20,
    )
    change_params_button.grid(pady=MENU_PADDING_1)

    delete_params_button = ttk.Button(
        change_model_defaults_frame,
        text=DELETE_PARAMETERS_TEXT,
        command=delete_entry,
        width=20,
    )
    delete_params_button.grid(pady=MENU_PADDING_1)

    cancel_button = ttk.Button(
        change_model_defaults_frame,
        text=CANCEL_TEXT,
        command=change_model_defaults.destroy,
    )
    cancel_button.grid(pady=MENU_PADDING_1)

    root.menu_placement(
        change_model_defaults, CHANGE_MODEL_DEFAULT_TEXT, top_window=top_window
    )


def pop_up_set_vocal_splitter(root: Any, top_window: Any) -> None:
    """Opens modal configuration dialog for vocal splitter and deverberation settings."""
    try:
        set_vocal_splitter = tk.Toplevel(root)

        model_list = root.assemble_model_data(arch_type=KARAOKEE_CHECK, is_dry_check=True)
        if not model_list:
            root.set_vocal_splitter_var.set(NO_MODEL)
        model_list.insert(0, NO_MODEL)

        enable_voc_split_model = lambda: (
            model_select_option.configure(state=READ_ONLY),
            save_inst_button.configure(state=tk.NORMAL),
        )
        disable_voc_split_model = lambda: (
            model_select_option.configure(state=tk.DISABLED),
            save_inst_button.configure(state=tk.DISABLED),
            root.is_save_inst_set_vocal_splitter_var.set(False),
        )
        voc_split_model_toggle = (
            lambda: enable_voc_split_model()
            if root.is_set_vocal_splitter_var.get()
            else disable_voc_split_model()
        )

        set_vocal_splitter_frame = root.menu_FRAME_SET(set_vocal_splitter)
        set_vocal_splitter_frame.grid(row=1)

        set_vocal_splitter_title = root.menu_title_LABEL_SET(
            set_vocal_splitter_frame, VOCAL_SPLIT_MODE_OPTIONS_TEXT
        )
        set_vocal_splitter_title.grid(pady=MENU_PADDING_2)

        model_select_label = root.menu_sub_LABEL_SET(set_vocal_splitter_frame, SELECT_MODEL_TEXT)
        model_select_label.grid(pady=MENU_PADDING_1)
        model_select_option = ComboBoxMenu(
            set_vocal_splitter_frame,
            dropdown_name="setvocalsplit",
            textvariable=root.set_vocal_splitter_var,
            values=model_list,
            offset=310,
            width=READ_ONLY_COMBO_WIDTH,
        )
        model_select_option.grid(pady=7)
        root.help_hints(model_select_option, text=VOC_SPLIT_MODEL_SELECT_HELP)

        save_inst_button = ttk.Checkbutton(
            set_vocal_splitter_frame,
            text=SAVE_SPLIT_VOCAL_INSTRUMENTALS_TEXT,
            variable=root.is_save_inst_set_vocal_splitter_var,
            width=SET_VOC_SPLIT_CHECK_WIDTH,
            command=voc_split_model_toggle,
        )
        save_inst_button.grid()
        root.help_hints(save_inst_button, text=IS_VOC_SPLIT_INST_SAVE_SELECT_HELP)

        change_params_button = ttk.Checkbutton(
            set_vocal_splitter_frame,
            text=ENABLE_VOCAL_SPLIT_MODE_TEXT,
            variable=root.is_set_vocal_splitter_var,
            width=SET_VOC_SPLIT_CHECK_WIDTH,
            command=voc_split_model_toggle,
        )
        change_params_button.grid()
        root.help_hints(change_params_button, text=IS_VOC_SPLIT_MODEL_SELECT_HELP)

        deverb_title = root.menu_title_LABEL_SET(
            set_vocal_splitter_frame, VOCAL_DEVERB_OPTIONS_TEXT
        )
        deverb_title.grid(pady=MENU_PADDING_2)

        deverb_vocals_label = root.menu_sub_LABEL_SET(set_vocal_splitter_frame, SELECT_MODEL_TEXT)
        deverb_vocals_label.grid(pady=MENU_PADDING_1)

        vocal_deverb_model_option = ComboBoxMenu(
            set_vocal_splitter_frame,
            dropdown_name="setvocaldeverbmodel",
            textvariable=root.vocal_deverb_model_var,
            values=root.vocal_deverb_models_list,
            offset=310,
            width=READ_ONLY_COMBO_WIDTH,
        )
        vocal_deverb_model_option.grid(pady=7)
        root.help_hints(
            vocal_deverb_model_option,
            text="Select the Vocal Deverberation model to process the audio.",
        )

        type_label = root.menu_sub_LABEL_SET(
            set_vocal_splitter_frame, "Select Vocal Type to Deverb"
        )
        type_label.grid(pady=MENU_PADDING_1)
        deverb_vocals_option = ComboBoxMenu(
            set_vocal_splitter_frame,
            dropdown_name="setvocaldeverb",
            textvariable=root.deverb_vocal_opt_var,
            values=list(DEVERB_MAPPER.keys()),
            width=23,
        )
        deverb_vocals_option.grid(pady=7)
        root.help_hints(deverb_vocals_option, text=IS_DEVERB_OPT_HELP)

        is_deverb_vocals_option = ttk.Checkbutton(
            set_vocal_splitter_frame,
            text=DEVERB_VOCALS_TEXT,
            width=15 if IS_WINDOWS else 11,
            variable=root.is_deverb_vocals_var,
            command=lambda: deverb_opt_toggle(),
        )
        is_deverb_vocals_option.grid(pady=0)
        root.help_hints(is_deverb_vocals_option, text=IS_DEVERB_VOC_HELP)

        enable_deverb_opt = lambda: (
            deverb_vocals_option.configure(state=READ_ONLY),
            vocal_deverb_model_option.configure(state=READ_ONLY),
        )
        disable_deverb_opt = lambda: (
            deverb_vocals_option.configure(state=tk.DISABLED),
            vocal_deverb_model_option.configure(state=tk.DISABLED),
        )
        deverb_opt_toggle = (
            lambda: enable_deverb_opt()
            if root.is_deverb_vocals_var.get()
            else disable_deverb_opt()
        )

        if len(root.vocal_deverb_models_list) <= 1:
            root.is_deverb_vocals_var.set(False)
            is_deverb_vocals_option.configure(state=tk.DISABLED)
            disable_deverb_opt()
            vocal_deverb_model_option.configure(state=tk.DISABLED)

        cancel_button = ttk.Button(
            set_vocal_splitter_frame,
            text=CLOSE_WINDOW,
            command=set_vocal_splitter.destroy,
            width=16,
        )
        cancel_button.grid(pady=MENU_PADDING_3)

        voc_split_model_toggle()
        deverb_opt_toggle()

        root.menu_placement(
            set_vocal_splitter,
            VOCAL_SPLIT_OPTIONS_TEXT,
            top_window=top_window,
            pop_up=True,
        )
    except Exception as e:
        error_name = f"{type(e).__name__}"
        traceback_text = "".join(traceback.format_tb(e.__traceback__))
        message = f'{error_name}: "{e}"\n{traceback_text}"'
        root.error_log_var.set(message)


def pop_up_mdx_model_sub_json_dump(root: Any, mdx_model_params: dict[str, Any], mdx_model_hash: str) -> None:
    """Dumps current selected MDX-Net model settings to a json named after model hash."""
    root.mdx_model_params = mdx_model_params
    mdx_model_params_dump = json.dumps(mdx_model_params, indent=4)
    with open(os.path.join(MDX_HASH_DIR, f"{mdx_model_hash}.json"), "w", encoding="utf-8") as outfile:
        outfile.write(mdx_model_params_dump)


def pop_up_mdx_c_param(root: Any, mdx_model_hash: str) -> None:
    """Opens MDX-C param configuration settings."""
    mdx_c_param_menu = tk.Toplevel()

    get_mdx_c_params = lambda d, ext: tuple(
        os.path.splitext(x)[0] for x in os.listdir(d) if x.endswith(ext)
    )
    new_mdx_c_params = get_mdx_c_params(MDX_C_CONFIG_PATH, YAML)
    mdx_c_model_param_var = tk.StringVar(value=NONE_SELECTED)

    def pull_data() -> None:
        mdx_c_model_params = {"config_yaml": f"{mdx_c_model_param_var.get()}{YAML}"}

        if mdx_c_model_param_var.get() != NONE_SELECTED:
            pop_up_mdx_model_sub_json_dump(root, mdx_c_model_params, mdx_model_hash)
            mdx_c_param_menu.destroy()
        else:
            root.mdx_model_params = None

    def cancel() -> None:
        root.mdx_model_params = None
        mdx_c_param_menu.destroy()

    mdx_c_param_frame = root.menu_FRAME_SET(mdx_c_param_menu)
    mdx_c_param_frame.grid(row=0)

    title_lbl = root.menu_title_LABEL_SET(
        mdx_c_param_frame, MDXNET_C_MODEL_PARAMETERS_TEXT, width=28
    )
    title_lbl.grid(row=0, column=0, padx=0, pady=0)

    param_lbl = root.menu_sub_LABEL_SET(mdx_c_param_frame, SELECT_MODEL_PARAM_TEXT)
    param_lbl.grid(pady=MENU_PADDING_1)
    param_opt = ComboBoxMenu(
        mdx_c_param_frame,
        textvariable=mdx_c_model_param_var,
        values=new_mdx_c_params,
        width=30,
    )
    param_opt.grid(padx=20, pady=MENU_PADDING_1)
    root.help_hints(param_lbl, text=VR_MODEL_PARAM_HELP)

    confirm_btn = ttk.Button(mdx_c_param_frame, text=CONFIRM_TEXT, command=pull_data)
    confirm_btn.grid(pady=MENU_PADDING_1)

    cancel_btn = ttk.Button(mdx_c_param_frame, text=CANCEL_TEXT, command=cancel)
    cancel_btn.grid(pady=MENU_PADDING_1)

    mdx_c_param_menu.protocol("WM_DELETE_WINDOW", cancel)
    root.menu_placement(mdx_c_param_menu, CHOOSE_MODEL_PARAM_TEXT, pop_up=True)


def pop_up_mdx_model(root: Any, mdx_model_hash: str, model_path: str) -> None:
    """Opens MDX-Net model parameter configuration dialog."""
    is_compatible_model = True
    _is_ckpt = False
    primary_stem = VOCAL_STEM
    n_fft = "6144"
    dim_f = 0
    dim_t = 0

    try:
        if model_path.endswith(ONNX):
            model = onnx.load(model_path)
            model_shapes = [
                [d.dim_value for d in _input.type.tensor_type.shape.dim]
                for _input in model.graph.input
            ][0]
            dim_f = model_shapes[2]
            dim_t = int(math.log(model_shapes[3], 2))
            n_fft = "6144"

        elif model_path.endswith(CKPT):
            _is_ckpt = True
            model_params = torch.load(
                model_path, map_location=lambda storage, loc: storage, weights_only=False
            )
            model_params = model_params["hyper_parameters"]
            dim_f = model_params["dim_f"]
            dim_t = int(math.log(model_params["dim_t"], 2))
            n_fft = model_params["n_fft"]

            for stem in STEM_SET_MENU:
                if model_params["target_name"] == stem.lower():
                    primary_stem = (
                        INST_STEM if model_params["target_name"] == OTHER_STEM.lower() else stem
                    )

        elif model_path.endswith(".safetensors"):
            is_compatible_model = False
            pop_up_mdx_c_param(root, mdx_model_hash)

    except Exception:
        is_compatible_model = False

    if is_compatible_model:
        mdx_model_set = tk.Toplevel()

        mdx_model_stem_var = tk.StringVar(value=primary_stem)
        mdx_model_n_fft_var = tk.StringVar(value=n_fft)
        mdx_model_dim_f_var = tk.StringVar(value=dim_f)
        mdx_model_dim_t_var = tk.StringVar(value=dim_t)
        compensate_var = tk.StringVar(value=1.035)

        def pull_data() -> None:
            mdx_model_params = {
                "n_fft_scale_set": int(mdx_model_n_fft_var.get()),
                "dim_f": int(mdx_model_dim_f_var.get()),
                "dim_t": 2 ** int(mdx_model_dim_t_var.get()),
                "compensate": float(compensate_var.get()),
                "primary_stem": mdx_model_stem_var.get(),
            }
            pop_up_mdx_model_sub_json_dump(root, mdx_model_params, mdx_model_hash)
            mdx_model_set.destroy()

        def cancel() -> None:
            root.mdx_model_params = None
            mdx_model_set.destroy()

        mdx_model_set_frame = root.menu_FRAME_SET(mdx_model_set)
        mdx_model_set_frame.grid(row=0)

        title_lbl = root.menu_title_LABEL_SET(
            mdx_model_set_frame, SPECIFY_MDX_NET_MODEL_PARAMETERS_TEXT, width=35
        )
        title_lbl.grid(row=0, column=0, padx=0, pady=0)

        stem_lbl = root.menu_sub_LABEL_SET(mdx_model_set_frame, PRIMARY_STEM_TEXT)
        stem_lbl.grid(pady=MENU_PADDING_1)
        stem_opt = ttk.OptionMenu(
            mdx_model_set_frame,
            mdx_model_stem_var,
            None,
            *STEM_SET_MENU,
            command=lambda s: None,
        )
        stem_opt.configure(width=15)
        stem_opt.grid(pady=MENU_PADDING_1)
        stem_opt["menu"].insert_separator(len(STEM_SET_MENU))
        stem_opt["menu"].add_radiobutton(
            label=INPUT_STEM_NAME,
            command=tk._setit(
                mdx_model_stem_var,
                INPUT_STEM_NAME,
                lambda e: root.pop_up_input_stem_name(mdx_model_stem_var, mdx_model_set),
            ),
        )

        confirm_btn = ttk.Button(mdx_model_set_frame, text=CONFIRM_TEXT, command=pull_data)
        confirm_btn.grid(pady=MENU_PADDING_1)

        cancel_btn = ttk.Button(mdx_model_set_frame, text=CANCEL_TEXT, command=cancel)
        cancel_btn.grid(pady=MENU_PADDING_1)

        mdx_model_set.protocol("WM_DELETE_WINDOW", cancel)
        root.menu_placement(
            mdx_model_set,
            SPECIFY_PARAMETERS_TEXT,
            pop_up=False if is_macos else True,
            frame_list=[mdx_model_set_frame],
        )


def pop_up_vr_param_sub_json_dump(root: Any, vr_model_params: dict[str, Any], vr_model_hash: str) -> None:
    """Dumps current selected VR model settings to a json named after model hash."""
    root.vr_model_params = vr_model_params
    vr_model_params_dump = json.dumps(vr_model_params, indent=4)
    with open(os.path.join(VR_HASH_DIR, f"{vr_model_hash}.json"), "w", encoding="utf-8") as outfile:
        outfile.write(vr_model_params_dump)


def pop_up_vr_param(root: Any, vr_model_hash: str) -> None:
    """Opens VR parameter configuration dialog."""
    vr_param_menu = tk.Toplevel()

    get_vr_params = lambda d, ext: tuple(
        os.path.splitext(x)[0] for x in os.listdir(d) if x.endswith(ext)
    )
    new_vr_params = get_vr_params(VR_PARAM_DIR, JSON)
    vr_model_param_var = tk.StringVar(value=NONE_SELECTED)
    vr_model_stem_var = tk.StringVar(value="Vocals")
    vr_model_nout_var = tk.StringVar(value=32)
    vr_model_nout_lstm_var = tk.StringVar(value=128)
    is_new_vr_model_var = tk.BooleanVar(value=False)
    balance_value_var = tk.StringVar(value=0)
    is_kara_model_var = tk.BooleanVar(value=False)
    is_bv_model_var = tk.BooleanVar(value=False)

    enable_new_vr_op = lambda: (
        vr_model_nout_option.configure(state=READ_ONLY),
        vr_model_nout_lstm_option.configure(state=READ_ONLY),
    )
    disable_new_vr_op = lambda: (
        vr_model_nout_option.configure(state=tk.DISABLED),
        vr_model_nout_lstm_option.configure(state=tk.DISABLED),
    )
    vr_new_toggle = (
        lambda: enable_new_vr_op()
        if is_new_vr_model_var.get()
        else disable_new_vr_op()
    )

    def pull_data() -> None:
        if is_new_vr_model_var.get():
            vr_model_params = {
                "vr_model_param": vr_model_param_var.get(),
                "primary_stem": vr_model_stem_var.get(),
                "nout": int(vr_model_nout_var.get()),
                "nout_lstm": int(vr_model_nout_lstm_var.get()),
                IS_KARAOKEE: bool(is_kara_model_var.get()),
                IS_BV_MODEL: bool(is_bv_model_var.get()),
                IS_BV_MODEL_REBAL: float(balance_value_var.get()),
            }
        else:
            vr_model_params = {
                "vr_model_param": vr_model_param_var.get(),
                "primary_stem": vr_model_stem_var.get(),
                IS_KARAOKEE: bool(is_kara_model_var.get()),
                IS_BV_MODEL: bool(is_bv_model_var.get()),
                IS_BV_MODEL_REBAL: float(balance_value_var.get()),
            }

        if vr_model_param_var.get() != NONE_SELECTED:
            pop_up_vr_param_sub_json_dump(root, vr_model_params, vr_model_hash)
            vr_param_menu.destroy()
        else:
            root.vr_model_params = None
            root.error_dialoge(INVALID_PARAM_MODEL_ERROR)

    def cancel() -> None:
        root.vr_model_params = None
        vr_param_menu.destroy()

    def toggle_kara() -> None:
        if is_kara_model_var.get():
            is_bv_model_var.set(False)
            balance_value_option.configure(state=tk.DISABLED)

    def toggle_bv() -> None:
        if is_bv_model_var.get():
            is_kara_model_var.set(False)
            balance_value_option.configure(state=READ_ONLY)
        else:
            balance_value_option.configure(state=tk.DISABLED)

    def opt_menu_selection(selection: str) -> None:
        if selection not in [VOCAL_STEM, INST_STEM]:
            balance_value_option.configure(state=tk.DISABLED)
            is_kara_model_option.configure(state=tk.DISABLED)
            is_bv_model_option.configure(state=tk.DISABLED)
            is_kara_model_var.set(False)
            is_bv_model_var.set(False)
            balance_value_var.set(0)
        else:
            is_kara_model_option.configure(state=tk.NORMAL)
            is_bv_model_option.configure(state=tk.NORMAL)

    vr_param_frame = root.menu_FRAME_SET(vr_param_menu)
    vr_param_frame.grid(row=0, padx=20)

    title_lbl = root.menu_title_LABEL_SET(
        vr_param_frame, SPECIFY_VR_MODEL_PARAMETERS_TEXT
    )
    title_lbl.grid()

    stem_lbl = root.menu_sub_LABEL_SET(vr_param_frame, PRIMARY_STEM_TEXT)
    stem_lbl.grid(pady=MENU_PADDING_1)
    vr_model_stem_option = ttk.OptionMenu(
        vr_param_frame,
        vr_model_stem_var,
        None,
        *STEM_SET_MENU,
        command=opt_menu_selection,
    )
    vr_model_stem_option.configure(width=15)
    vr_model_stem_option.grid(pady=MENU_PADDING_1)
    vr_model_stem_option["menu"].insert_separator(len(STEM_SET_MENU))
    vr_model_stem_option["menu"].add_radiobutton(
        label=INPUT_STEM_NAME,
        command=tk._setit(
            vr_model_stem_var,
            INPUT_STEM_NAME,
            lambda e: root.pop_up_input_stem_name(vr_model_stem_var, vr_param_menu),
        ),
    )
    root.help_hints(stem_lbl, text=SET_STEM_NAME_HELP)

    is_kara_model_option = ttk.Checkbutton(
        vr_param_frame,
        text=KARAOKE_MODEL_TEXT,
        width=SET_MENUS_CHECK_WIDTH,
        variable=is_kara_model_var,
        command=toggle_kara,
    )
    is_kara_model_option.grid(pady=0)

    is_bv_model_option = ttk.Checkbutton(
        vr_param_frame,
        text=BV_MODEL_TEXT,
        width=SET_MENUS_CHECK_WIDTH,
        variable=is_bv_model_var,
        command=toggle_bv,
    )
    is_bv_model_option.grid(pady=0)

    balance_lbl = root.menu_sub_LABEL_SET(vr_param_frame, BALANCE_VALUE_TEXT)
    balance_lbl.grid(pady=MENU_PADDING_1)
    balance_value_option = ComboBoxMenu(
        vr_param_frame,
        textvariable=balance_value_var,
        values=BALANCE_VALUES,
        width=COMBO_WIDTH,
    )
    balance_value_option.configure(state=tk.DISABLED)
    balance_value_option.grid(pady=MENU_PADDING_1)

    is_new_vr_model_option = ttk.Checkbutton(
        vr_param_frame,
        text=VR_51_MODEL_TEXT,
        width=SET_MENUS_CHECK_WIDTH,
        variable=is_new_vr_model_var,
        command=vr_new_toggle,
    )
    is_new_vr_model_option.grid(pady=MENU_PADDING_1)

    nout_lbl = root.menu_sub_LABEL_SET(vr_param_frame, "Out Channels")
    nout_lbl.grid(pady=MENU_PADDING_1)
    vr_model_nout_option = ComboBoxEditableMenu(
        vr_param_frame,
        values=NOUT_SEL,
        textvariable=vr_model_nout_var,
        pattern=REG_SHIFTS,
        default="32",
        width=COMBO_WIDTH,
    )
    vr_model_nout_option.grid(pady=MENU_PADDING_1)

    lstm_lbl = root.menu_sub_LABEL_SET(vr_param_frame, "Out Channels (LSTM layer)")
    lstm_lbl.grid(pady=MENU_PADDING_1)
    vr_model_nout_lstm_option = ComboBoxEditableMenu(
        vr_param_frame,
        values=NOUT_LSTM_SEL,
        textvariable=vr_model_nout_lstm_var,
        pattern=REG_SHIFTS,
        default="128",
        width=COMBO_WIDTH,
    )
    vr_model_nout_lstm_option.grid(pady=MENU_PADDING_1)

    param_lbl = root.menu_sub_LABEL_SET(vr_param_frame, SELECT_MODEL_PARAM_TEXT)
    param_lbl.grid(pady=MENU_PADDING_1)
    vr_model_param_option = ComboBoxMenu(
        vr_param_frame,
        textvariable=vr_model_param_var,
        values=new_vr_params,
        width=30,
    )
    vr_model_param_option.grid(pady=MENU_PADDING_1)
    root.help_hints(param_lbl, text=VR_MODEL_PARAM_HELP)

    confirm_btn = ttk.Button(vr_param_frame, text=CONFIRM_TEXT, command=pull_data)
    confirm_btn.grid(pady=MENU_PADDING_1)

    cancel_btn = ttk.Button(vr_param_frame, text=CANCEL_TEXT, command=cancel)
    cancel_btn.grid(pady=MENU_PADDING_1)

    vr_new_toggle()
    opt_menu_selection(vr_model_stem_var.get())

    vr_param_menu.protocol("WM_DELETE_WINDOW", cancel)
    root.menu_placement(
        vr_param_menu,
        CHOOSE_MODEL_PARAM_TEXT,
        pop_up=False if is_macos else True,
        frame_list=[vr_param_frame],
    )
