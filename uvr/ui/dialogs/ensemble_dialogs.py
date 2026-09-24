"""Ensemble and custom stem configuration popup dialogs for UVR.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui_data.app_size_values import FONT_SIZE_1, MENU_PADDING_1
from gui_data.constants import (
    BATCH_SIZE,
    CANCEL_TEXT,
    CHUNKS,
    CONFIRM_TEXT,
    DEMUCS_ARCH_TYPE,
    DEMUCS_OVERLAP,
    DEMUCS_SEGMENTS,
    DEMUCS_SHIFTS,
    DONE_MENU_TEXT,
    ENSEMBLE_INPUT_RULE,
    ENSEMBLE_NAME_TEXT,
    ENSEMBLE_PARTITION,
    ENSEMBLE_WARNING_NOT_ENOUGH_SHORT_TEXT,
    ENSEMBLE_WARNING_NOT_ENOUGH_TEXT,
    INPUT_STEM_NAME_TEXT,
    INPUT_UNIQUE_STEM_NAME_TEXT,
    INST_STEM,
    IS_INVERSE_STEM_TEXT,
    MDX23_OVERLAP,
    MDX_ARCH_TYPE,
    MDX_OVERLAP,
    MDX_SEGMENTS,
    NO_STEM,
    OK_TEXT,
    OPERATING_SYSTEM,
    REG_INPUT_STEM_NAME,
    REG_SAVE_INPUT,
    RESET_TO_DEFAULT,
    SAVE_CURRENT_ENSEMBLE_TEXT,
    SAVE_TEXT,
    STEM_INPUT_RULE,
    STEM_NAME_TEXT,
    STEM_SET_MENU_2,
    VOCAL_STEM,
    VR_AGGRESSION,
    VR_ARCH_TYPE,
    VR_CROP,
    VR_WINDOW,
)
from uvr.constants import ENSEMBLE_CACHE_DIR, MAIN_FONT_NAME
from uvr.core.model_data import ModelData
from uvr.ui.components.combobox_menu import ComboBoxMenu

logger = logging.getLogger(__name__)


def pop_up_input_stem_name(root: Any, stem_var: tk.StringVar, parent_window: tk.Toplevel) -> None:
    """Opens modal dialog for defining a unique/custom stem identifier."""
    stem_input_save = tk.Toplevel(root)

    def close_window(is_cancel: bool = True) -> None:
        if is_cancel or not stem_input_save_var.get():
            stem_var.set(VOCAL_STEM)
        else:
            stem_input_save_text = stem_input_save_var.get().capitalize()
            if stem_input_save_text == VOCAL_STEM:
                stem_text = INST_STEM if is_inverse_stem_var.get() else stem_input_save_text
            elif stem_input_save_text == INST_STEM:
                stem_text = VOCAL_STEM if is_inverse_stem_var.get() else stem_input_save_text
            else:
                stem_text = (
                    f"{NO_STEM}{stem_input_save_text}"
                    if is_inverse_stem_var.get()
                    else stem_input_save_text
                )
            stem_var.set(stem_text)

        stem_input_save.destroy()
        if OPERATING_SYSTEM == "Linux":
            parent_window.attributes("-topmost", "true")
        parent_window.grab_set()
        root.wait_window(parent_window)

    stem_input_save_var = tk.StringVar(value="")
    is_inverse_stem_var = tk.BooleanVar(value=False)

    validation = lambda value: re.fullmatch(REG_INPUT_STEM_NAME, value) is not None

    stem_input_save_frame = root.menu_FRAME_SET(stem_input_save)
    stem_input_save_frame.grid(row=1)

    title_lbl = root.menu_title_LABEL_SET(stem_input_save_frame, INPUT_STEM_NAME_TEXT)
    title_lbl.grid(pady=0)

    name_lbl = root.menu_sub_LABEL_SET(stem_input_save_frame, STEM_NAME_TEXT)
    name_lbl.grid(pady=MENU_PADDING_1)
    name_entry = ttk.Combobox(
        stem_input_save_frame,
        textvariable=stem_input_save_var,
        values=STEM_SET_MENU_2,
        justify="center",
        width=25,
    )
    invalid_message = root.invalid_tooltip(name_entry, REG_INPUT_STEM_NAME)
    name_entry.grid(pady=MENU_PADDING_1)
    name_entry.focus_set()

    root.spacer_label(stem_input_save_frame)

    inverse_btn = ttk.Checkbutton(
        stem_input_save_frame,
        text=IS_INVERSE_STEM_TEXT,
        variable=is_inverse_stem_var,
    )
    inverse_btn.grid(pady=0)

    rules_lbl = tk.Label(
        stem_input_save_frame,
        text=STEM_INPUT_RULE,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
        foreground="#868687",
        justify="left",
    )
    rules_lbl.grid(pady=MENU_PADDING_1)

    done_btn = ttk.Button(
        stem_input_save_frame,
        text=DONE_MENU_TEXT,
        command=lambda: close_window(is_cancel=False)
        if validation(stem_input_save_var.get())
        else invalid_message(),
    )
    done_btn.grid(pady=MENU_PADDING_1)

    cancel_btn = ttk.Button(stem_input_save_frame, text=CANCEL_TEXT, command=close_window)
    cancel_btn.grid(pady=MENU_PADDING_1)

    stem_input_save.protocol("WM_DELETE_WINDOW", close_window)
    root.menu_placement(
        stem_input_save,
        INPUT_UNIQUE_STEM_NAME_TEXT,
        pop_up=True,
        frame_list=[stem_input_save_frame],
    )


def pop_up_save_ensemble_sub_json_dump(
    root: Any, selected_ensemble_model: list[str], ensemble_save_name: str
) -> None:
    """Dumps current ensemble settings to a json named after user input."""
    if ensemble_save_name:
        root.last_loaded_ensemble = ensemble_save_name
        root.chosen_ensemble_var.set(ensemble_save_name)
        file_save_name = ensemble_save_name.replace(" ", "_")
        saved_data = {
            "ensemble_main_stem": root.ensemble_main_stem_var.get(),
            "ensemble_type": root.ensemble_type_var.get(),
            "is_save_all_outputs_ensemble": root.is_save_all_outputs_ensemble_var.get(),
            "is_append_ensemble_name": root.is_append_ensemble_name_var.get(),
            "is_wav_ensemble": root.is_wav_ensemble_var.get(),
            "is_gpu_conversion": root.is_gpu_conversion_var.get(),
            "is_half_precision": root.is_half_precision_var.get(),
            "is_primary_stem_only": root.is_primary_stem_only_var.get(),
            "is_secondary_stem_only": root.is_secondary_stem_only_var.get(),
            "selected_models": selected_ensemble_model,
        }
        with open(
            os.path.join(ENSEMBLE_CACHE_DIR, f"{file_save_name}.json"),
            "w",
            encoding="utf-8",
        ) as outfile:
            outfile.write(json.dumps(saved_data, indent=4))


def pop_up_save_ensemble(root: Any) -> None:
    """Opens dialog to save current ensemble configuration to disk."""
    ensemble_save = tk.Toplevel(root)

    default_save_name = getattr(root, "last_loaded_ensemble", "")
    ensemble_save_var = tk.StringVar(value=default_save_name)

    ensemble_save_frame = root.menu_FRAME_SET(ensemble_save)
    ensemble_save_frame.grid(row=1)

    validation = lambda value: re.fullmatch(REG_SAVE_INPUT, value) is not None
    save_func = lambda: (
        pop_up_save_ensemble_sub_json_dump(
            root, root.ensemble_listbox_get_all_selected_models(), ensemble_save_var.get()
        ),
        ensemble_save.destroy(),
    )

    if len(root.ensemble_listbox_get_all_selected_models()) <= 1:
        warn_title = root.menu_title_LABEL_SET(
            ensemble_save_frame, ENSEMBLE_WARNING_NOT_ENOUGH_SHORT_TEXT, width=20
        )
        warn_title.grid()

        warn_sub = root.menu_sub_LABEL_SET(
            ensemble_save_frame, ENSEMBLE_WARNING_NOT_ENOUGH_TEXT
        )
        warn_sub.grid(pady=MENU_PADDING_1)

        ok_btn = ttk.Button(
            ensemble_save_frame, text=OK_TEXT, command=ensemble_save.destroy
        )
        ok_btn.grid()
    else:
        title_lbl = root.menu_title_LABEL_SET(
            ensemble_save_frame, SAVE_CURRENT_ENSEMBLE_TEXT
        )
        title_lbl.grid()

        name_lbl = root.menu_sub_LABEL_SET(ensemble_save_frame, ENSEMBLE_NAME_TEXT)
        name_lbl.grid(pady=MENU_PADDING_1)
        name_entry = ttk.Entry(
            ensemble_save_frame,
            textvariable=ensemble_save_var,
            justify="center",
            width=25,
        )
        name_entry.grid(pady=MENU_PADDING_1)
        invalid_message = root.invalid_tooltip(name_entry)
        name_entry.focus_set()
        if default_save_name:
            name_entry.select_range(0, tk.END)
        root.spacer_label(ensemble_save_frame)

        rules_lbl = tk.Label(
            ensemble_save_frame,
            text=ENSEMBLE_INPUT_RULE,
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
            foreground="#868687",
            justify="left",
        )
        rules_lbl.grid()

        save_btn = ttk.Button(
            ensemble_save_frame,
            text=SAVE_TEXT,
            command=lambda: save_func()
            if validation(ensemble_save_var.get())
            else invalid_message(),
        )
        save_btn.grid(pady=MENU_PADDING_1)

        cancel_btn = ttk.Button(
            ensemble_save_frame, text=CANCEL_TEXT, command=ensemble_save.destroy
        )
        cancel_btn.grid(pady=MENU_PADDING_1)

    root.menu_placement(ensemble_save, SAVE_CURRENT_ENSEMBLE_TEXT, pop_up=True)


def open_ensemble_model_settings(root: Any, event: Any = None) -> None:
    """Prepares model metadata and opens ensemble model settings window."""
    selected_indices = root.ensemble_listbox_Option.curselection()
    if not selected_indices:
        return

    models_info = []
    for idx in selected_indices:
        model_name = root.ensemble_listbox_Option.get(idx)
        process_method, _, actual_model_name = model_name.partition(ENSEMBLE_PARTITION)
        models_info.append((model_name, process_method, actual_model_name))

    pop_up_ensemble_model_settings(root, models_info)


def pop_up_ensemble_model_settings(root: Any, models_info: list[tuple[str, str, str]]) -> None:
    """Opens tabbed or single-panel ensemble model settings dialog."""
    settings_menu = tk.Toplevel()
    settings_frame = root.menu_FRAME_SET(settings_menu)
    settings_frame.grid(row=0)

    use_notebook = len(models_info) > 1
    if use_notebook:
        container: Any = ttk.Notebook(settings_frame)
        container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    else:
        title_text = f"Settings: {models_info[0][2]}"
        title_lbl = root.menu_title_LABEL_SET(settings_frame, title_text, width=35)
        title_lbl.grid(row=0, column=0, padx=0, pady=0)
        container = settings_frame

    vars_dict: dict[str, dict[str, tk.StringVar]] = {}
    row_idx_global = 1

    for full_model_name, process_method, actual_model_name in models_info:
        vars_dict[full_model_name] = {}
        model_settings = root.ensemble_model_settings.get(full_model_name, {})

        if use_notebook:
            page_frame = tk.Frame(container, bg="#070708")
            container.add(page_frame, text=actual_model_name)
            parent_frame: Any = page_frame
            row_idx = 0
        else:
            parent_frame = container
            row_idx = 1

        def add_option(
            label_text: str,
            key: str,
            values: list[str],
            default_val: str,
            pf: Any,
            r_idx: int,
            f_name: str,
            curr_settings: dict[str, Any] = model_settings,
        ) -> int:
            lbl = root.menu_sub_LABEL_SET(pf, label_text)
            lbl.grid(row=r_idx, pady=MENU_PADDING_1)
            r_idx += 1
            var = tk.StringVar(value=str(curr_settings.get(key, default_val)))
            vars_dict[f_name][key] = var
            opt = ComboBoxMenu(pf, textvariable=var, values=values, width=30)
            opt.grid(row=r_idx, padx=20, pady=MENU_PADDING_1)
            r_idx += 1
            return r_idx

        row_idx = add_option(
            "Weight (Weighted Ensemble)",
            "weight",
            [str(i) for i in range(1, 101)],
            "10",
            parent_frame,
            row_idx,
            full_model_name,
        )

        if process_method == MDX_ARCH_TYPE:
            is_mdx_c = False
            try:
                temp_model = ModelData(full_model_name, is_change_def=False, root=root)
                is_mdx_c = temp_model.is_mdx_c
            except Exception:
                pass

            row_idx = add_option(
                "Segment Size",
                "mdx_segment_size",
                MDX_SEGMENTS,
                root.mdx_segment_size_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )
            row_idx = add_option(
                "Batch Size",
                "mdx_batch_size",
                BATCH_SIZE,
                root.mdx_batch_size_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )

            if is_mdx_c:
                row_idx = add_option(
                    "Overlap",
                    "overlap_mdx23",
                    MDX23_OVERLAP,
                    root.overlap_mdx23_var.get(),
                    parent_frame,
                    row_idx,
                    full_model_name,
                )
            else:
                row_idx = add_option(
                    "Overlap",
                    "overlap_mdx",
                    MDX_OVERLAP,
                    root.overlap_mdx_var.get(),
                    parent_frame,
                    row_idx,
                    full_model_name,
                )

        elif process_method == VR_ARCH_TYPE:
            row_idx = add_option(
                "Window Size",
                "window_size",
                VR_WINDOW,
                root.window_size_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )
            row_idx = add_option(
                "Aggression",
                "aggression_setting",
                list(VR_AGGRESSION),
                root.aggression_setting_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )
            row_idx = add_option(
                "Crop Size",
                "crop_size",
                VR_CROP,
                root.crop_size_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )

        elif process_method == DEMUCS_ARCH_TYPE:
            row_idx = add_option(
                "Segment",
                "segment",
                DEMUCS_SEGMENTS,
                root.segment_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )
            row_idx = add_option(
                "Overlap",
                "overlap",
                DEMUCS_OVERLAP,
                root.overlap_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )
            row_idx = add_option(
                "Shifts",
                "shifts",
                DEMUCS_SHIFTS,
                root.shifts_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )
            row_idx = add_option(
                "Chunks",
                "chunks_demucs",
                CHUNKS,
                root.chunks_demucs_var.get(),
                parent_frame,
                row_idx,
                full_model_name,
            )

        if not use_notebook:
            row_idx_global = row_idx

    def save() -> None:
        for f_name, v_dict in vars_dict.items():
            new_settings = root.ensemble_model_settings.get(f_name, {})
            for k, v in v_dict.items():
                new_settings[k] = v.get()
            root.ensemble_model_settings[f_name] = new_settings
        settings_menu.destroy()

    def reset() -> None:
        for f_name in vars_dict:
            if f_name in root.ensemble_model_settings:
                del root.ensemble_model_settings[f_name]
        settings_menu.destroy()

    save_btn = ttk.Button(settings_frame, text=CONFIRM_TEXT, command=save)
    save_btn.grid(row=row_idx_global, pady=MENU_PADDING_1)
    row_idx_global += 1

    reset_btn = ttk.Button(settings_frame, text=RESET_TO_DEFAULT, command=reset)
    reset_btn.grid(row=row_idx_global, pady=MENU_PADDING_1)
    row_idx_global += 1

    cancel_btn = ttk.Button(settings_frame, text=CANCEL_TEXT, command=settings_menu.destroy)
    cancel_btn.grid(row=row_idx_global, pady=MENU_PADDING_1)

    settings_menu.protocol("WM_DELETE_WINDOW", settings_menu.destroy)
    root.menu_placement(settings_menu, "Model Settings", pop_up=True)
