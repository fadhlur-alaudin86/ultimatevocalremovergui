"""Settings dialog and advanced configuration menus for UVR."""

from __future__ import annotations

import logging
import os
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import Any

from gui_data.app_size_values import (
    DEMUCS_CHECKBOXS_WIDTH,
    ENSEMBLE_CHECKBOXS_WIDTH,
    FONT_SIZE_1,
    FONT_SIZE_2,
    FONT_SIZE_4,
    GEN_SETTINGS_WIDTH,
    HELP_HINT_CHECKBOX_WIDTH,
    MDX_CHECKBOXS_WIDTH,
    MENU_COMBOBOX_WIDTH,
    MENU_PADDING_1,
    MENU_PADDING_2,
    MENU_PADDING_4,
    READ_ONLY_COMBO_WIDTH,
    SETTINGS_BUT_WIDTH,
    UPDATE_LABEL_WIDTH,
    VR_BUT_WIDTH,
    VR_CHECKBOXS_WIDTH,
)
from gui_data.constants import (
    ACCEPT_ANY_INPUT_TEXT,
    ADDITIONAL_MENUS_INFORMATION_TEXT,
    ADDITIONAL_SETTINGS_TEXT,
    ADVANCED_ALIGN_TOOL_OPTIONS_TEXT,
    ADVANCED_DEMUCS_OPTIONS_TEXT,
    ADVANCED_ENSEMBLE_OPTIONS_TEXT,
    ADVANCED_MDXNET23_OPTIONS_TEXT,
    ADVANCED_MDXNET_OPTIONS_TEXT,
    ADVANCED_OPTION_MENU_TEXT,
    ADVANCED_VR_OPTIONS_TEXT,
    AGGRESSION_SETTING_HELP,
    AGGRESSION_SETTING_TEXT,
    ALIGN_PHASE_OPTIONS,
    APPEND_ENSEMBLE_NAME_TEXT,
    APPLICATION_DOWNLOAD_CENTER_TEXT,
    APPLICATION_UPDATES_TEXT,
    AUDIO_FORMAT_SETTINGS_TEXT,
    BACK_TO_MAIN_MENU,
    BATCH_SIZE,
    BATCH_SIZE_HELP,
    BATCH_SIZE_TEXT,
    CHANGE_MODEL_DEFAULTS_TEXT,
    CHOOSE_ADVANCED_MENU_TEXT,
    CLEAR_AUTOSET_CACHE_TEXT,
    CLEAR_CACHE_HELP,
    CLOSE_WINDOW,
    COMBINE_STEMS_TEXT,
    COMPENSATE_HELP,
    CUDA_NUM_TEXT,
    DELETE_MODEL_HELP,
    DELETE_MODEL_TEXT,
    DELETE_USER_SAVED_SETTING_TEXT,
    DELETE_YOUR_SETTINGS_HELP,
    DEMUCS_ARCH_TYPE,
    DEMUCS_OVERLAP,
    DEMUCS_SEGMENTS,
    DEMUCS_SHIFTS,
    DENOISE_M,
    DENOISE_OUTPUT_TEXT,
    DENOISE_S,
    DONATE_HELP,
    DONATE_LINK_BMAC,
    DOWNLOAD_CENTER_TEXT,
    DOWNLOAD_STOPPED,
    ENABLE_HELP_HINTS_TEXT,
    ENABLE_TTA_TEXT,
    ENSEMBLE_WAVFORMS_TEXT,
    FG_COLOR,
    GENERAL_MENU_TEXT,
    GENERAL_PROCESS_SETTINGS_TEXT,
    GENERATE_MODEL_FOLDER_TEXT,
    GPU_DEVICE_NUM_OPTS,
    HIGHEND_PROCESS_TEXT,
    IS_ACCEPT_ANY_INPUT_HELP,
    IS_ALIGN_TRACK_HELP,
    IS_APPEND_ENSEMBLE_NAME_HELP,
    IS_CREATE_MODEL_FOLDER_HELP,
    IS_CUDA_SELECT_HELP,
    IS_DEMUCS_COMBINE_STEMS_HELP,
    IS_DENOISE_HELP,
    IS_FREQUENCY_MATCH_HELP,
    IS_HIGH_END_PROCESS_HELP,
    IS_INVERT_SPEC_HELP,
    IS_MATCH_SILENCE_HELP,
    IS_MATCH_SPEC_HELP,
    IS_MODEL_TESTING_AUDIO_HELP,
    IS_NORMALIZATION_HELP,
    IS_PHASE_HELP,
    IS_POST_PROCESS_HELP,
    IS_REPLAYGAIN_HELP,
    IS_SAVE_ALL_OUTPUTS_ENSEMBLE_HELP,
    IS_SPLIT_MODE_HELP,
    IS_TASK_COMPLETE_HELP,
    IS_TESTING_AUDIO_HELP,
    IS_TTA_HELP,
    IS_WAV_ENSEMBLE_HELP,
    MATCH_FREQ_CUTOFF_TEXT,
    MDX23_OVERLAP,
    MDX_ARCH_TYPE,
    MDX_DENOISE_OPTION,
    MDX_OVERLAP,
    MDX_SEGMENT_SIZE_HELP,
    MDX_SEGMENTS,
    MODEL_SAMPLE_MODE_SETTINGS_TEXT,
    MODEL_TEST_MODE_TEXT,
    MP3_BIT_RATES,
    MP3_BITRATE_TEXT,
    NORMALIZE_OUTPUT_TEXT,
    NOTIFICATION_CHIMES_TEXT,
    OPEN_APPLICATION_DIRECTORY_TEXT,
    OPEN_MODELS_FOLDER_TEXT,
    OPTION_LIST,
    OVERLAP_23_HELP,
    OVERLAP_HELP,
    OVERLAP_TEXT,
    PHASE_SHIFTS_ALIGN_HELP,
    PHASE_SHIFTS_OPT,
    PHASE_SHIFTS_TEXT,
    PITCH_SHIFT_HELP,
    POST_PROCESS_TEXT,
    POST_PROCESS_THREASHOLD_HELP,
    POST_PROCESS_THRESHOLD_TEXT,
    POST_PROCESSES_THREASHOLD_VALUES,
    READ_ONLY,
    REFRESH_LIST_TEXT,
    REG_AGGRESSION,
    REG_BATCHES,
    REG_COMPENSATION,
    REG_MDX_SEG,
    REG_OVERLAP,
    REG_OVERLAP23,
    REG_SEGMENTS,
    REG_SEMITONES,
    REG_SHIFTS,
    REG_THES_POSTPORCESS,
    REG_WINDOW,
    REMOVE_SAVED_ENSEMBLE_TEXT,
    REPLAYGAIN_TEXT,
    RESET_ALL_SETTINGS_TO_DEFAULT_TEXT,
    RESTART_APPLICATION_TEXT,
    SAMPLE_CLIP_DURATION_TEXT,
    SAMPLE_MODE_CHECKBOX,
    SAVE_ALIGNED_TRACK_TEXT,
    SAVE_ALL_OUTPUTS_TEXT,
    SECONDARY_PHASE_TEXT,
    SECONDS_TEXT,
    SEGMENT_HELP,
    SEGMENT_SIZE_TEXT,
    SEGMENTS_TEXT,
    SELECT_DOWNLOAD_TEXT,
    SELECT_SAVED_ENSEMBLE,
    SELECT_SAVED_SETTING,
    SEMI_DEF,
    SEMITONE_SEL,
    SETTINGS_GUIDE_TEXT,
    SETTINGS_TEST_MODE_TEXT,
    SHIFT_CONVERSION_PITCH_TEXT,
    SHIFTS_HELP,
    SHIFTS_TEXT,
    SILENCE_MATCHING_TEXT,
    SPECTRAL_INVERSION_TEXT,
    SPECTRAL_MATCHING_TEXT,
    SPLIT_MODE_TEXT,
    STOP_DOWNLOAD_TEXT,
    TRY_MANUAL_DOWNLOAD_TEXT,
    VOL_COMPENSATION,
    VOLUME_COMPENSATION_TEXT,
    VR_AGGRESSION,
    VR_ARCH_PM,
    VR_ARCH_TYPE,
    VR_WINDOW,
    WAV_TYPE,
    WAV_TYPE_TEXT,
    WINDOW_SIZE_HELP,
    WINDOW_SIZE_TEXT,
)
from uvr.constants import (
    BASE_PATH,
    DEMUCS_MODELS_DIR,
    DENOISER_MODEL_PATH,
    ENSEMBLE_CACHE_DIR,
    IS_MACOS,
    IS_WINDOWS,
    MAIN_FONT_NAME,
    MDX_MODELS_DIR,
    SETTINGS_CACHE_DIR,
    VR_MODELS_DIR,
)
from uvr.ui.components import ComboBoxEditableMenu, ComboBoxMenu
from uvr.utils.file_utils import open_file_or_folder

logger = logging.getLogger(__name__)


def open_settings_menu(root: Any, select_tab_2: bool = False, select_tab_3: bool = False) -> None:
    """Open Settings and Download Center modal dialog."""
    settings_menu = tk.Toplevel()

    option_var = tk.StringVar(value=SELECT_SAVED_SETTING)
    root.is_menu_settings_open = True

    tab_control = ttk.Notebook(settings_menu)

    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    tab3 = ttk.Frame(tab_control)

    tab_control.add(tab1, text=SETTINGS_GUIDE_TEXT)
    tab_control.add(tab2, text=ADDITIONAL_SETTINGS_TEXT)
    tab_control.add(tab3, text=DOWNLOAD_CENTER_TEXT)

    tab_control.pack(expand=1, fill="both")

    tab1.grid_rowconfigure(0, weight=1)
    tab1.grid_columnconfigure(0, weight=1)
    tab2.grid_rowconfigure(0, weight=1)
    tab2.grid_columnconfigure(0, weight=1)
    tab3.grid_rowconfigure(0, weight=1)
    tab3.grid_columnconfigure(0, weight=1)

    root.disable_tabs = lambda: (tab_control.tab(0, state="disabled"), tab_control.tab(1, state="disabled"))
    root.enable_tabs = lambda: (tab_control.tab(0, state="normal"), tab_control.tab(1, state="normal"))
    root.main_menu_var = tk.StringVar(value=CHOOSE_ADVANCED_MENU_TEXT)

    root.download_progress_bar_var.set(0)
    root.download_progress_info_var.set("")
    root.download_progress_percent_var.set("")

    def close_window() -> None:
        if root.thread_check(root.active_download_thread):
            root.active_download_thread.terminate()
        root.is_menu_settings_open = False
        root.select_download_var.set("")
        settings_menu.destroy()

    def set_vars_for_sample_mode(event: Any) -> None:
        val = int(float(event))
        val = round(val / 5) * 5
        root.model_sample_mode_duration_var.set(val)
        root.model_sample_mode_duration_checkbox_var.set(SAMPLE_MODE_CHECKBOX(val))
        root.model_sample_mode_duration_label_var.set(f"{val} {SECONDS_TEXT}")

    # Settings Tab 1
    settings_menu_main_frame = root.menu_FRAME_SET(tab1)
    settings_menu_main_frame.grid(row=0)
    settings_title_label = root.menu_title_LABEL_SET(settings_menu_main_frame, GENERAL_MENU_TEXT)
    settings_title_label.grid(pady=MENU_PADDING_2)

    select_label = root.menu_sub_LABEL_SET(settings_menu_main_frame, ADDITIONAL_MENUS_INFORMATION_TEXT)
    select_label.grid(pady=MENU_PADDING_1)

    select_option = ComboBoxMenu(
        settings_menu_main_frame,
        textvariable=root.main_menu_var,
        values=OPTION_LIST,
        width=GEN_SETTINGS_WIDTH + 3,
    )
    select_option.update_dropdown_size(
        OPTION_LIST,
        "menuchoose",
        command=lambda e: (root.check_is_menu_open(root.main_menu_var.get()), close_window()),
    )
    select_option.grid(pady=MENU_PADDING_1)

    help_hints_option = ttk.Checkbutton(
        settings_menu_main_frame,
        text=ENABLE_HELP_HINTS_TEXT,
        variable=root.help_hints_var,
        width=HELP_HINT_CHECKBOX_WIDTH,
    )
    help_hints_option.grid(pady=MENU_PADDING_1)

    open_app_dir_button = ttk.Button(
        settings_menu_main_frame,
        text=OPEN_APPLICATION_DIRECTORY_TEXT,
        command=lambda: open_file_or_folder(BASE_PATH),
        width=SETTINGS_BUT_WIDTH,
    )
    open_app_dir_button.grid(pady=MENU_PADDING_1)

    reset_all_app_settings_button = ttk.Button(
        settings_menu_main_frame,
        text=RESET_ALL_SETTINGS_TO_DEFAULT_TEXT,
        command=lambda: root.load_to_default_confirm(),
        width=SETTINGS_BUT_WIDTH,
    )
    reset_all_app_settings_button.grid(pady=MENU_PADDING_1)

    if IS_WINDOWS:
        restart_app_button = ttk.Button(
            settings_menu_main_frame,
            text=RESTART_APPLICATION_TEXT,
            command=lambda: root.restart(),
        )
        restart_app_button.grid(pady=MENU_PADDING_1)

    delete_your_settings_label = root.menu_title_LABEL_SET(
        settings_menu_main_frame, DELETE_USER_SAVED_SETTING_TEXT
    )
    delete_your_settings_label.grid(pady=MENU_PADDING_2)
    root.help_hints(delete_your_settings_label, text=DELETE_YOUR_SETTINGS_HELP)

    delete_your_settings_option = ComboBoxMenu(
        settings_menu_main_frame, textvariable=option_var, width=GEN_SETTINGS_WIDTH + 3
    )
    delete_your_settings_option.grid(padx=20, pady=MENU_PADDING_1)
    root.deletion_list_fill(
        delete_your_settings_option, option_var, SETTINGS_CACHE_DIR, SELECT_SAVED_SETTING, menu_name="deletesetting"
    )

    delete_model_label = root.menu_title_LABEL_SET(settings_menu_main_frame, DELETE_MODEL_TEXT)
    delete_model_label.grid(pady=MENU_PADDING_2)
    root.help_hints(delete_model_label, text=DELETE_MODEL_HELP)

    root.delete_model_var = tk.StringVar(value="Select Model to Delete")
    root.delete_model_Option = ComboBoxMenu(
        settings_menu_main_frame, textvariable=root.delete_model_var, width=GEN_SETTINGS_WIDTH + 3
    )
    root.delete_model_Option.grid(padx=20, pady=MENU_PADDING_1)
    root.update_delete_model_list()

    app_update_label = root.menu_title_LABEL_SET(settings_menu_main_frame, APPLICATION_UPDATES_TEXT)
    app_update_label.grid(pady=MENU_PADDING_2)

    root.app_update_button = ttk.Button(
        settings_menu_main_frame,
        textvariable=root.app_update_button_Text_var,
        width=SETTINGS_BUT_WIDTH - 2,
        command=lambda: root.pop_up_update_confirmation(),
    )
    root.app_update_button.grid(pady=MENU_PADDING_1)

    root.app_update_status_Label = tk.Label(
        settings_menu_main_frame,
        textvariable=root.app_update_status_Text_var,
        padx=3,
        pady=3,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}"),
        width=UPDATE_LABEL_WIDTH,
        justify="center",
        relief="ridge",
        fg="#13849f",
    )
    root.app_update_status_Label.grid(pady=20)

    donate_button = ttk.Button(
        settings_menu_main_frame,
        image=root.donate_img,
        command=lambda: webbrowser.open_new_tab(DONATE_LINK_BMAC),
    )
    donate_button.grid(pady=MENU_PADDING_2)
    root.help_hints(donate_button, text=DONATE_HELP)

    close_settings_win_button = ttk.Button(
        settings_menu_main_frame, text=CLOSE_WINDOW, command=lambda: close_window()
    )
    close_settings_win_button.grid(pady=MENU_PADDING_1)

    # Settings Tab 2
    settings_menu_format_frame = root.menu_FRAME_SET(tab2)
    settings_menu_format_frame.grid(row=0)

    audio_format_title_label = root.menu_title_LABEL_SET(
        settings_menu_format_frame, AUDIO_FORMAT_SETTINGS_TEXT, width=20
    )
    audio_format_title_label.grid(pady=MENU_PADDING_2)

    wav_type_set_label = root.menu_sub_LABEL_SET(settings_menu_format_frame, WAV_TYPE_TEXT)
    wav_type_set_label.grid(pady=MENU_PADDING_1)

    wav_type_set_option = ComboBoxMenu(
        settings_menu_format_frame,
        textvariable=root.wav_type_set_var,
        values=WAV_TYPE,
        width=HELP_HINT_CHECKBOX_WIDTH,
    )
    wav_type_set_option.grid(padx=20, pady=MENU_PADDING_1)

    mp3_bit_set_label = root.menu_sub_LABEL_SET(settings_menu_format_frame, MP3_BITRATE_TEXT)
    mp3_bit_set_label.grid(pady=MENU_PADDING_1)

    mp3_bit_set_option = ComboBoxMenu(
        settings_menu_format_frame,
        textvariable=root.mp3_bit_set_var,
        values=MP3_BIT_RATES,
        width=HELP_HINT_CHECKBOX_WIDTH,
    )
    mp3_bit_set_option.grid(padx=20, pady=MENU_PADDING_1)

    general_proc_title_label = root.menu_title_LABEL_SET(
        settings_menu_format_frame, GENERAL_PROCESS_SETTINGS_TEXT
    )
    general_proc_title_label.grid(pady=MENU_PADDING_2)

    is_testing_audio_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=SETTINGS_TEST_MODE_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_testing_audio_var,
    )
    is_testing_audio_option.grid()
    root.help_hints(is_testing_audio_option, text=IS_TESTING_AUDIO_HELP)

    is_add_model_name_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=MODEL_TEST_MODE_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_add_model_name_var,
    )
    is_add_model_name_option.grid()
    root.help_hints(is_add_model_name_option, text=IS_MODEL_TESTING_AUDIO_HELP)

    is_create_model_folder_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=GENERATE_MODEL_FOLDER_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_create_model_folder_var,
    )
    is_create_model_folder_option.grid()
    root.help_hints(is_create_model_folder_option, text=IS_CREATE_MODEL_FOLDER_HELP)

    is_accept_any_input_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=ACCEPT_ANY_INPUT_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_accept_any_input_var,
    )
    is_accept_any_input_option.grid()
    root.help_hints(is_accept_any_input_option, text=IS_ACCEPT_ANY_INPUT_HELP)

    is_task_complete_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=NOTIFICATION_CHIMES_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_task_complete_var,
    )
    is_task_complete_option.grid()
    root.help_hints(is_task_complete_option, text=IS_TASK_COMPLETE_HELP)

    is_normalization_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=NORMALIZE_OUTPUT_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_normalization_var,
    )
    is_normalization_option.grid()
    root.help_hints(is_normalization_option, text=IS_NORMALIZATION_HELP)

    is_replaygain_option = ttk.Checkbutton(
        settings_menu_format_frame,
        text=REPLAYGAIN_TEXT,
        width=GEN_SETTINGS_WIDTH,
        variable=root.is_replaygain_var,
    )
    is_replaygain_option.grid()
    root.help_hints(is_replaygain_option, text=IS_REPLAYGAIN_HELP)

    change_model_default_button = ttk.Button(
        settings_menu_format_frame,
        text=CHANGE_MODEL_DEFAULTS_TEXT,
        command=lambda: root.pop_up_change_model_defaults(settings_menu),
        width=SETTINGS_BUT_WIDTH - 2,
    )
    change_model_default_button.grid(pady=MENU_PADDING_4)

    root.vocal_splitter_Button_opt(
        settings_menu, settings_menu_format_frame, width=SETTINGS_BUT_WIDTH - 2, pady=MENU_PADDING_4
    )

    if not IS_MACOS and root.is_gpu_available:
        gpu_list_options = lambda: root.loop_gpu_list(device_set_option, "gpudevice", root.cuda_device_list)
        device_set_label = root.menu_title_LABEL_SET(settings_menu_format_frame, CUDA_NUM_TEXT)
        device_set_label.grid(pady=MENU_PADDING_2)

        device_set_option = ComboBoxMenu(
            settings_menu_format_frame,
            textvariable=root.device_set_var,
            values=GPU_DEVICE_NUM_OPTS,
            width=GEN_SETTINGS_WIDTH + 1,
        )
        device_set_option.grid(padx=20, pady=MENU_PADDING_1)
        gpu_list_options()
        root.help_hints(device_set_label, text=IS_CUDA_SELECT_HELP)

    model_sample_mode_label = root.menu_title_LABEL_SET(
        settings_menu_format_frame, MODEL_SAMPLE_MODE_SETTINGS_TEXT
    )
    model_sample_mode_label.grid(pady=MENU_PADDING_2)

    model_sample_mode_duration_label = root.menu_sub_LABEL_SET(
        settings_menu_format_frame, SAMPLE_CLIP_DURATION_TEXT
    )
    model_sample_mode_duration_label.grid(pady=MENU_PADDING_1)

    tk.Label(
        settings_menu_format_frame,
        textvariable=root.model_sample_mode_duration_label_var,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
        foreground=FG_COLOR,
    ).grid(pady=2)
    model_sample_mode_duration_option = ttk.Scale(
        settings_menu_format_frame,
        variable=root.model_sample_mode_duration_var,
        from_=5,
        to=120,
        command=set_vars_for_sample_mode,
        orient="horizontal",
    )
    model_sample_mode_duration_option.grid(pady=2)

    # Settings Tab 3
    settings_menu_download_center_frame = root.menu_FRAME_SET(tab3)
    settings_menu_download_center_frame.grid(row=0)

    download_center_title_label = root.menu_title_LABEL_SET(
        settings_menu_download_center_frame, APPLICATION_DOWNLOAD_CENTER_TEXT
    )
    download_center_title_label.grid(padx=20, pady=MENU_PADDING_2)

    select_download_label = root.menu_sub_LABEL_SET(
        settings_menu_download_center_frame, SELECT_DOWNLOAD_TEXT
    )
    select_download_label.grid(pady=MENU_PADDING_2)

    root.model_download_vr_Button = ttk.Radiobutton(
        settings_menu_download_center_frame,
        text="VR Arch",
        width=8,
        variable=root.select_download_var,
        value="VR Arc",
        command=lambda: root.download_list_state(),
    )
    root.model_download_vr_Button.grid(pady=MENU_PADDING_1)
    root.model_download_vr_Option = ComboBoxMenu(
        settings_menu_download_center_frame,
        textvariable=root.model_download_vr_var,
        width=READ_ONLY_COMBO_WIDTH,
    )
    root.model_download_vr_Option.grid(pady=MENU_PADDING_1)

    root.model_download_mdx_Button = ttk.Radiobutton(
        settings_menu_download_center_frame,
        text="MDX-Net",
        width=8,
        variable=root.select_download_var,
        value="MDX-Net",
        command=lambda: root.download_list_state(),
    )
    root.model_download_mdx_Button.grid(pady=MENU_PADDING_1)
    root.model_download_mdx_Option = ComboBoxMenu(
        settings_menu_download_center_frame,
        textvariable=root.model_download_mdx_var,
        width=READ_ONLY_COMBO_WIDTH,
    )
    root.model_download_mdx_Option.grid(pady=MENU_PADDING_1)

    root.model_download_demucs_Button = ttk.Radiobutton(
        settings_menu_download_center_frame,
        text="Demucs",
        width=8,
        variable=root.select_download_var,
        value="Demucs",
        command=lambda: root.download_list_state(),
    )
    root.model_download_demucs_Button.grid(pady=MENU_PADDING_1)
    root.model_download_demucs_Option = ComboBoxMenu(
        settings_menu_download_center_frame,
        textvariable=root.model_download_demucs_var,
        width=READ_ONLY_COMBO_WIDTH,
    )
    root.model_download_demucs_Option.grid(pady=MENU_PADDING_1)

    root.download_Button = ttk.Button(
        settings_menu_download_center_frame,
        image=root.download_img,
        command=lambda: root.download_item(),
    )
    root.download_Button.grid(pady=MENU_PADDING_1)

    root.download_progress_info_Label = tk.Label(
        settings_menu_download_center_frame,
        textvariable=root.download_progress_info_var,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_2}"),
        foreground=FG_COLOR,
        borderwidth=0,
    )
    root.download_progress_info_Label.grid(pady=MENU_PADDING_1)

    root.download_progress_percent_Label = tk.Label(
        settings_menu_download_center_frame,
        textvariable=root.download_progress_percent_var,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_2}"),
        wraplength=350,
        foreground=FG_COLOR,
    )
    root.download_progress_percent_Label.grid(pady=MENU_PADDING_1)

    root.download_progress_bar_Progressbar = ttk.Progressbar(
        settings_menu_download_center_frame, variable=root.download_progress_bar_var
    )
    root.download_progress_bar_Progressbar.grid(pady=MENU_PADDING_1)

    root.stop_download_Button = ttk.Button(
        settings_menu_download_center_frame,
        textvariable=root.download_stop_var,
        width=15,
        command=lambda: root.download_post_action(DOWNLOAD_STOPPED),
    )
    root.stop_download_Button.grid(pady=MENU_PADDING_1)
    root.stop_download_Button_DISABLE = lambda: (
        root.download_stop_var.set(""),
        root.stop_download_Button.configure(state=tk.DISABLED),
    )
    root.stop_download_Button_ENABLE = lambda: (
        root.download_stop_var.set(STOP_DOWNLOAD_TEXT),
        root.stop_download_Button.configure(state=tk.NORMAL),
    )

    root.refresh_list_Button = ttk.Button(
        settings_menu_download_center_frame,
        text=REFRESH_LIST_TEXT,
        command=lambda: root.online_data_refresh(refresh_list_Button=True),
    )
    root.refresh_list_Button.grid(pady=MENU_PADDING_1)

    root.download_key_Button = ttk.Button(
        settings_menu_download_center_frame,
        image=root.key_img,
        command=lambda: root.pop_up_user_code_input(),
    )
    root.download_key_Button.grid(pady=MENU_PADDING_1)

    root.manual_download_Button = ttk.Button(
        settings_menu_download_center_frame,
        text=TRY_MANUAL_DOWNLOAD_TEXT,
        command=root.menu_manual_downloads,
    )
    root.manual_download_Button.grid(pady=MENU_PADDING_1)

    root.download_center_Buttons = (
        root.model_download_vr_Button,
        root.model_download_mdx_Button,
        root.model_download_demucs_Button,
        root.download_Button,
        root.download_key_Button,
    )

    root.download_lists = (
        root.model_download_vr_Option,
        root.model_download_mdx_Option,
        root.model_download_demucs_Option,
    )

    root.download_list_vars = (
        root.model_download_vr_var,
        root.model_download_mdx_var,
        root.model_download_demucs_var,
    )

    root.online_data_refresh()

    root.menu_placement(
        settings_menu,
        SETTINGS_GUIDE_TEXT,
        is_help_hints=True,
        close_function=lambda: close_window(),
    )

    if select_tab_2:
        tab_control.select(tab2)
        settings_menu.update_idletasks()

    if select_tab_3:
        tab_control.select(tab3)
        settings_menu.update_idletasks()

    settings_menu.protocol("WM_DELETE_WINDOW", close_window)


def open_advanced_vr_options(root: Any) -> None:
    """Open Advanced VR Options dialog."""
    vr_opt = tk.Toplevel()

    tab1 = root.menu_tab_control(vr_opt, root.vr_secondary_model_vars)

    root.is_open_menu_advanced_vr_options.set(True)
    root.menu_advanced_vr_options_close_window = lambda: (
        root.is_open_menu_advanced_vr_options.set(False),
        vr_opt.destroy(),
    )
    vr_opt.protocol("WM_DELETE_WINDOW", root.menu_advanced_vr_options_close_window)

    toggle_post_process = lambda: (
        root.post_process_threshold_Option.configure(state=READ_ONLY)
        if root.is_post_process_var.get()
        else root.post_process_threshold_Option.configure(state=tk.DISABLED)
    )

    vr_opt_frame = root.menu_FRAME_SET(tab1)
    vr_opt_frame.grid(pady=0 if root.chosen_process_method_var.get() != VR_ARCH_PM else 70)

    vr_title = root.menu_title_LABEL_SET(vr_opt_frame, ADVANCED_VR_OPTIONS_TEXT)
    vr_title.grid(padx=25, pady=MENU_PADDING_2)

    if root.chosen_process_method_var.get() != VR_ARCH_PM:
        window_size_label = root.menu_sub_LABEL_SET(vr_opt_frame, WINDOW_SIZE_TEXT)
        window_size_label.grid(pady=MENU_PADDING_1)
        window_size_option = ComboBoxEditableMenu(
            vr_opt_frame,
            values=VR_WINDOW,
            width=MENU_COMBOBOX_WIDTH,
            textvariable=root.window_size_var,
            pattern=REG_WINDOW,
            default=VR_WINDOW[1],
        )
        window_size_option.grid(pady=MENU_PADDING_1)
        root.help_hints(window_size_label, text=WINDOW_SIZE_HELP)

        aggression_setting_label = root.menu_sub_LABEL_SET(vr_opt_frame, AGGRESSION_SETTING_TEXT)
        aggression_setting_label.grid(pady=MENU_PADDING_1)
        aggression_setting_option = ComboBoxEditableMenu(
            vr_opt_frame,
            values=VR_AGGRESSION,
            width=MENU_COMBOBOX_WIDTH,
            textvariable=root.aggression_setting_var,
            pattern=REG_AGGRESSION,
            default=VR_AGGRESSION[5],
        )
        aggression_setting_option.grid(pady=MENU_PADDING_1)
        root.help_hints(aggression_setting_label, text=AGGRESSION_SETTING_HELP)

    root.batch_size_Label = root.menu_sub_LABEL_SET(vr_opt_frame, BATCH_SIZE_TEXT)
    root.batch_size_Label.grid(pady=MENU_PADDING_1)
    root.batch_size_Option = ComboBoxEditableMenu(
        vr_opt_frame,
        values=BATCH_SIZE,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.batch_size_var,
        pattern=REG_BATCHES,
        default=BATCH_SIZE,
    )
    root.batch_size_Option.grid(pady=MENU_PADDING_1)
    root.help_hints(root.batch_size_Label, text=BATCH_SIZE_HELP)

    root.post_process_threshold_Label = root.menu_sub_LABEL_SET(vr_opt_frame, POST_PROCESS_THRESHOLD_TEXT)
    root.post_process_threshold_Label.grid(pady=MENU_PADDING_1)
    root.post_process_threshold_Option = ComboBoxEditableMenu(
        vr_opt_frame,
        values=POST_PROCESSES_THREASHOLD_VALUES,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.post_process_threshold_var,
        pattern=REG_THES_POSTPORCESS,
        default=POST_PROCESSES_THREASHOLD_VALUES[1],
    )
    root.post_process_threshold_Option.grid(pady=MENU_PADDING_1)
    root.help_hints(root.post_process_threshold_Label, text=POST_PROCESS_THREASHOLD_HELP)

    root.is_tta_Option = ttk.Checkbutton(
        vr_opt_frame, text=ENABLE_TTA_TEXT, width=VR_CHECKBOXS_WIDTH, variable=root.is_tta_var
    )
    root.is_tta_Option.grid(pady=0)
    root.help_hints(root.is_tta_Option, text=IS_TTA_HELP)

    root.is_post_process_Option = ttk.Checkbutton(
        vr_opt_frame,
        text=POST_PROCESS_TEXT,
        width=VR_CHECKBOXS_WIDTH,
        variable=root.is_post_process_var,
        command=toggle_post_process,
    )
    root.is_post_process_Option.grid(pady=0)
    root.help_hints(root.is_post_process_Option, text=IS_POST_PROCESS_HELP)

    root.is_high_end_process_Option = ttk.Checkbutton(
        vr_opt_frame,
        text=HIGHEND_PROCESS_TEXT,
        width=VR_CHECKBOXS_WIDTH,
        variable=root.is_high_end_process_var,
    )
    root.is_high_end_process_Option.grid(pady=0)
    root.help_hints(root.is_high_end_process_Option, text=IS_HIGH_END_PROCESS_HELP)

    root.vocal_splitter_Button_opt(vr_opt, vr_opt_frame, pady=MENU_PADDING_1, width=VR_BUT_WIDTH)

    root.vr_clear_cache_Button = ttk.Button(
        vr_opt_frame,
        text=CLEAR_AUTOSET_CACHE_TEXT,
        command=lambda: root.clear_cache(VR_ARCH_TYPE),
        width=VR_BUT_WIDTH,
    )
    root.vr_clear_cache_Button.grid(pady=MENU_PADDING_1)
    root.help_hints(root.vr_clear_cache_Button, text=CLEAR_CACHE_HELP)

    root.open_vr_model_dir_Button = ttk.Button(
        vr_opt_frame,
        text=OPEN_MODELS_FOLDER_TEXT,
        command=lambda: open_file_or_folder(VR_MODELS_DIR),
        width=VR_BUT_WIDTH,
    )
    root.open_vr_model_dir_Button.grid(pady=MENU_PADDING_1)

    root.vr_return_Button = ttk.Button(
        vr_opt_frame,
        text=BACK_TO_MAIN_MENU,
        command=lambda: (root.menu_advanced_vr_options_close_window(), root.check_is_menu_settings_open()),
    )
    root.vr_return_Button.grid(pady=MENU_PADDING_1)

    root.vr_close_Button = ttk.Button(
        vr_opt_frame, text=CLOSE_WINDOW, command=lambda: root.menu_advanced_vr_options_close_window()
    )
    root.vr_close_Button.grid(pady=MENU_PADDING_1)

    toggle_post_process()

    frame_list = [vr_opt_frame]
    root.menu_placement(
        vr_opt,
        ADVANCED_VR_OPTIONS_TEXT,
        is_help_hints=True,
        close_function=root.menu_advanced_vr_options_close_window,
        frame_list=frame_list,
    )


def open_advanced_demucs_options(root: Any) -> None:
    """Open Advanced Demucs Options dialog."""
    demuc_opt = tk.Toplevel()

    root.is_open_menu_advanced_demucs_options.set(True)
    root.menu_advanced_demucs_options_close_window = lambda: (
        root.is_open_menu_advanced_demucs_options.set(False),
        demuc_opt.destroy(),
    )
    demuc_opt.protocol("WM_DELETE_WINDOW", root.menu_advanced_demucs_options_close_window)

    tab1, tab3 = root.menu_tab_control(demuc_opt, root.demucs_secondary_model_vars, is_demucs=True)

    demucs_frame = root.menu_FRAME_SET(tab1)
    demucs_frame.grid(pady=0 if root.chosen_process_method_var.get() != DEMUCS_ARCH_TYPE else 55)

    demucs_pre_model_frame = root.menu_FRAME_SET(tab3)
    demucs_pre_model_frame.grid(row=0)

    demucs_title_label = root.menu_title_LABEL_SET(demucs_frame, ADVANCED_DEMUCS_OPTIONS_TEXT)
    demucs_title_label.grid(pady=MENU_PADDING_2)

    if root.chosen_process_method_var.get() != DEMUCS_ARCH_TYPE:
        segment_label = root.menu_sub_LABEL_SET(demucs_frame, SEGMENTS_TEXT)
        segment_label.grid(pady=MENU_PADDING_2)
        segment_option = ComboBoxEditableMenu(
            demucs_frame,
            values=DEMUCS_SEGMENTS,
            width=MENU_COMBOBOX_WIDTH,
            textvariable=root.segment_var,
            pattern=REG_SEGMENTS,
            default=DEMUCS_SEGMENTS,
        )
        segment_option.grid()
        root.help_hints(segment_label, text=SEGMENT_HELP)

    root.shifts_Label = root.menu_sub_LABEL_SET(demucs_frame, SHIFTS_TEXT)
    root.shifts_Label.grid(pady=MENU_PADDING_1)
    root.shifts_Option = ComboBoxEditableMenu(
        demucs_frame,
        values=DEMUCS_SHIFTS,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.shifts_var,
        pattern=REG_SHIFTS,
        default=DEMUCS_SHIFTS[2],
    )
    root.shifts_Option.grid(pady=MENU_PADDING_1)
    root.help_hints(root.shifts_Label, text=SHIFTS_HELP)

    root.overlap_Label = root.menu_sub_LABEL_SET(demucs_frame, OVERLAP_TEXT)
    root.overlap_Label.grid(pady=MENU_PADDING_1)
    root.overlap_Option = ComboBoxEditableMenu(
        demucs_frame,
        values=DEMUCS_OVERLAP,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.overlap_var,
        pattern=REG_OVERLAP,
        default=DEMUCS_OVERLAP,
    )
    root.overlap_Option.grid(pady=MENU_PADDING_1)
    root.help_hints(root.overlap_Label, text=OVERLAP_HELP)

    pitch_shift_label = root.menu_sub_LABEL_SET(demucs_frame, SHIFT_CONVERSION_PITCH_TEXT)
    pitch_shift_label.grid(pady=MENU_PADDING_1)
    pitch_shift_option = ComboBoxEditableMenu(
        demucs_frame,
        values=SEMITONE_SEL,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.semitone_shift_var,
        pattern=REG_SEMITONES,
        default=SEMI_DEF,
    )
    pitch_shift_option.grid(pady=MENU_PADDING_1)
    root.help_hints(pitch_shift_label, text=PITCH_SHIFT_HELP)

    root.is_split_mode_Option = ttk.Checkbutton(
        demucs_frame,
        text=SPLIT_MODE_TEXT,
        width=DEMUCS_CHECKBOXS_WIDTH,
        variable=root.is_split_mode_var,
    )
    root.is_split_mode_Option.grid()
    root.help_hints(root.is_split_mode_Option, text=IS_SPLIT_MODE_HELP)

    root.is_demucs_combine_stems_Option = ttk.Checkbutton(
        demucs_frame,
        text=COMBINE_STEMS_TEXT,
        width=DEMUCS_CHECKBOXS_WIDTH,
        variable=root.is_demucs_combine_stems_var,
    )
    root.is_demucs_combine_stems_Option.grid()
    root.help_hints(root.is_demucs_combine_stems_Option, text=IS_DEMUCS_COMBINE_STEMS_HELP)

    is_invert_spec_option = ttk.Checkbutton(
        demucs_frame,
        text=SPECTRAL_INVERSION_TEXT,
        width=DEMUCS_CHECKBOXS_WIDTH,
        variable=root.is_invert_spec_var,
    )
    is_invert_spec_option.grid()
    root.help_hints(is_invert_spec_option, text=IS_INVERT_SPEC_HELP)

    is_demucs_tta_option = ttk.Checkbutton(
        demucs_frame,
        text=ENABLE_TTA_TEXT,
        width=DEMUCS_CHECKBOXS_WIDTH,
        variable=root.is_demucs_tta_var,
    )
    is_demucs_tta_option.grid()
    root.help_hints(is_demucs_tta_option, text=IS_TTA_HELP)

    root.vocal_splitter_Button_opt(demuc_opt, demucs_frame, width=VR_BUT_WIDTH, pady=MENU_PADDING_1)

    root.open_demucs_model_dir_Button = ttk.Button(
        demucs_frame,
        text=OPEN_MODELS_FOLDER_TEXT,
        command=lambda: open_file_or_folder(DEMUCS_MODELS_DIR),
        width=VR_BUT_WIDTH,
    )
    root.open_demucs_model_dir_Button.grid(pady=MENU_PADDING_1)

    root.demucs_return_Button = ttk.Button(
        demucs_frame,
        text=BACK_TO_MAIN_MENU,
        command=lambda: (
            root.menu_advanced_demucs_options_close_window(),
            root.check_is_menu_settings_open(),
        ),
    )
    root.demucs_return_Button.grid(pady=MENU_PADDING_1)

    root.demucs_close_Button = ttk.Button(
        demucs_frame, text=CLOSE_WINDOW, command=lambda: root.menu_advanced_demucs_options_close_window()
    )
    root.demucs_close_Button.grid(pady=MENU_PADDING_1)

    frame_list = [demucs_pre_model_frame, demucs_frame]
    root.menu_placement(
        demuc_opt,
        ADVANCED_DEMUCS_OPTIONS_TEXT,
        is_help_hints=True,
        close_function=root.menu_advanced_demucs_options_close_window,
        frame_list=frame_list,
    )


def open_advanced_mdx_options(root: Any) -> None:
    """Open Advanced MDX Options dialog."""
    mdx_net_opt = tk.Toplevel()

    root.is_open_menu_advanced_mdx_options.set(True)
    root.menu_advanced_mdx_options_close_window = lambda: (
        root.is_open_menu_advanced_mdx_options.set(False),
        mdx_net_opt.destroy(),
    )
    mdx_net_opt.protocol("WM_DELETE_WINDOW", root.menu_advanced_mdx_options_close_window)

    tab1, tab3 = root.menu_tab_control(mdx_net_opt, root.mdx_secondary_model_vars, is_mdxnet=True)

    mdx_net_frame = root.menu_FRAME_SET(tab1)
    mdx_net_frame.grid(pady=0)

    mdx_net23_frame = root.menu_FRAME_SET(tab3)
    mdx_net23_frame.grid(pady=0)

    mdx_opt_title = root.menu_title_LABEL_SET(mdx_net_frame, ADVANCED_MDXNET_OPTIONS_TEXT)
    mdx_opt_title.grid(pady=MENU_PADDING_1)

    compensate_label = root.menu_sub_LABEL_SET(mdx_net_frame, VOLUME_COMPENSATION_TEXT)
    compensate_label.grid(pady=MENU_PADDING_4)
    compensate_option = ComboBoxEditableMenu(
        mdx_net_frame,
        values=VOL_COMPENSATION,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.compensate_var,
        pattern=REG_COMPENSATION,
        default=VOL_COMPENSATION,
    )
    compensate_option.grid(pady=MENU_PADDING_4)
    root.help_hints(compensate_label, text=COMPENSATE_HELP)

    mdx_segment_size_label = root.menu_sub_LABEL_SET(mdx_net_frame, SEGMENT_SIZE_TEXT)
    mdx_segment_size_label.grid(pady=MENU_PADDING_4)
    mdx_segment_size_option = ComboBoxEditableMenu(
        mdx_net_frame,
        values=MDX_SEGMENTS,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.mdx_segment_size_var,
        pattern=REG_MDX_SEG,
        default="Default",
    )
    mdx_segment_size_option.grid(pady=MENU_PADDING_4)
    root.help_hints(mdx_segment_size_label, text=MDX_SEGMENT_SIZE_HELP)

    overlap_mdx_label = root.menu_sub_LABEL_SET(mdx_net_frame, OVERLAP_TEXT)
    overlap_mdx_label.grid(pady=MENU_PADDING_4)
    overlap_mdx_option = ComboBoxEditableMenu(
        mdx_net_frame,
        values=MDX_OVERLAP,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.overlap_mdx_var,
        pattern=REG_OVERLAP,
        default=MDX_OVERLAP,
    )
    overlap_mdx_option.grid(pady=MENU_PADDING_4)
    root.help_hints(overlap_mdx_label, text=OVERLAP_HELP)

    pitch_shift_label = root.menu_sub_LABEL_SET(mdx_net_frame, SHIFT_CONVERSION_PITCH_TEXT)
    pitch_shift_label.grid(pady=MENU_PADDING_4)
    pitch_shift_option = ComboBoxEditableMenu(
        mdx_net_frame,
        values=SEMITONE_SEL,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.semitone_shift_var,
        pattern=REG_SEMITONES,
        default=SEMI_DEF,
    )
    pitch_shift_option.grid(pady=MENU_PADDING_4)
    root.help_hints(pitch_shift_label, text=PITCH_SHIFT_HELP)

    if not os.path.isfile(DENOISER_MODEL_PATH):
        denoise_options_var_text = root.denoise_option_var.get()
        denoise_options = [option for option in MDX_DENOISE_OPTION if option != DENOISE_M]
        root.denoise_option_var.set(
            DENOISE_S if denoise_options_var_text == DENOISE_M else denoise_options_var_text
        )
    else:
        denoise_options = MDX_DENOISE_OPTION

    denoise_option_label = root.menu_sub_LABEL_SET(mdx_net_frame, DENOISE_OUTPUT_TEXT)
    denoise_option_label.grid(pady=MENU_PADDING_4)
    denoise_option_option = ComboBoxMenu(
        mdx_net_frame,
        textvariable=root.denoise_option_var,
        values=denoise_options,
        width=MENU_COMBOBOX_WIDTH,
    )
    denoise_option_option.grid(pady=MENU_PADDING_4)
    root.help_hints(denoise_option_label, text=IS_DENOISE_HELP)

    is_match_frequency_pitch_option = ttk.Checkbutton(
        mdx_net_frame,
        text=MATCH_FREQ_CUTOFF_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_match_frequency_pitch_var,
    )
    is_match_frequency_pitch_option.grid(pady=0)
    root.help_hints(is_match_frequency_pitch_option, text=IS_FREQUENCY_MATCH_HELP)

    is_invert_spec_option = ttk.Checkbutton(
        mdx_net_frame,
        text=SPECTRAL_INVERSION_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_invert_spec_var,
    )
    is_invert_spec_option.grid(pady=0)
    root.help_hints(is_invert_spec_option, text=IS_INVERT_SPEC_HELP)

    is_mdx_tta_option = ttk.Checkbutton(
        mdx_net_frame,
        text=ENABLE_TTA_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_mdx_tta_var,
    )
    is_mdx_tta_option.grid(pady=0)
    root.help_hints(is_mdx_tta_option, text=IS_TTA_HELP)

    root.vocal_splitter_Button_opt(mdx_net_opt, mdx_net_frame, pady=MENU_PADDING_1, width=VR_BUT_WIDTH)

    clear_mdx_cache_button = ttk.Button(
        mdx_net_frame,
        text=CLEAR_AUTOSET_CACHE_TEXT,
        command=lambda: root.clear_cache(MDX_ARCH_TYPE),
        width=VR_BUT_WIDTH,
    )
    clear_mdx_cache_button.grid(pady=MENU_PADDING_1)
    root.help_hints(clear_mdx_cache_button, text=CLEAR_CACHE_HELP)

    open_mdx_model_dir_button = ttk.Button(
        mdx_net_frame,
        text=OPEN_MODELS_FOLDER_TEXT,
        command=lambda: open_file_or_folder(MDX_MODELS_DIR),
        width=VR_BUT_WIDTH,
    )
    open_mdx_model_dir_button.grid(pady=MENU_PADDING_1)

    mdx_return_button = ttk.Button(
        mdx_net_frame,
        text=BACK_TO_MAIN_MENU,
        command=lambda: (
            root.menu_advanced_mdx_options_close_window(),
            root.check_is_menu_settings_open(),
        ),
    )
    mdx_return_button.grid(pady=MENU_PADDING_1)

    mdx_close_button = ttk.Button(
        mdx_net_frame, text=CLOSE_WINDOW, command=lambda: root.menu_advanced_mdx_options_close_window()
    )
    mdx_close_button.grid(pady=MENU_PADDING_1)

    mdx23_opt_title = root.menu_title_LABEL_SET(mdx_net23_frame, ADVANCED_MDXNET23_OPTIONS_TEXT)
    mdx23_opt_title.grid(pady=MENU_PADDING_2)

    mdx_batch_size_label = root.menu_sub_LABEL_SET(mdx_net23_frame, BATCH_SIZE_TEXT)
    mdx_batch_size_label.grid(pady=MENU_PADDING_1)
    mdx_batch_size_option = ComboBoxEditableMenu(
        mdx_net23_frame,
        values=BATCH_SIZE,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.mdx_batch_size_var,
        pattern=REG_BATCHES,
        default=BATCH_SIZE,
    )
    mdx_batch_size_option.grid(pady=MENU_PADDING_1)
    root.help_hints(mdx_batch_size_label, text=BATCH_SIZE_HELP)

    overlap_mdx23_label = root.menu_sub_LABEL_SET(mdx_net23_frame, OVERLAP_TEXT)
    overlap_mdx23_label.grid(pady=MENU_PADDING_1)
    overlap_mdx23_option = ComboBoxEditableMenu(
        mdx_net23_frame,
        values=MDX23_OVERLAP,
        width=MENU_COMBOBOX_WIDTH,
        textvariable=root.overlap_mdx23_var,
        pattern=REG_OVERLAP23,
        default="8",
    )
    overlap_mdx23_option.grid(pady=MENU_PADDING_1)
    root.help_hints(overlap_mdx23_label, text=OVERLAP_23_HELP)

    is_mdx_combine_stems_option = ttk.Checkbutton(
        mdx_net23_frame,
        text=COMBINE_STEMS_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_mdx23_combine_stems_var,
    )
    is_mdx_combine_stems_option.grid()
    root.help_hints(is_mdx_combine_stems_option, text=IS_DEMUCS_COMBINE_STEMS_HELP)

    mdx23_close_button = ttk.Button(
        mdx_net23_frame, text=CLOSE_WINDOW, command=lambda: root.menu_advanced_mdx_options_close_window()
    )
    mdx23_close_button.grid(pady=MENU_PADDING_2)

    frame_list = [mdx_net_frame, mdx_net23_frame]
    root.menu_placement(
        mdx_net_opt,
        ADVANCED_MDXNET_OPTIONS_TEXT,
        is_help_hints=True,
        close_function=root.menu_advanced_mdx_options_close_window,
        frame_list=frame_list,
    )


def open_advanced_ensemble_options(root: Any) -> None:
    """Open Ensemble Custom dialog."""
    custom_ens_opt = tk.Toplevel()

    root.is_open_menu_advanced_ensemble_options.set(True)
    root.menu_advanced_ensemble_options_close_window = lambda: (
        root.is_open_menu_advanced_ensemble_options.set(False),
        custom_ens_opt.destroy(),
    )
    custom_ens_opt.protocol("WM_DELETE_WINDOW", root.menu_advanced_ensemble_options_close_window)

    option_var = tk.StringVar(value=SELECT_SAVED_ENSEMBLE)

    custom_ens_opt_frame = root.menu_FRAME_SET(custom_ens_opt)
    custom_ens_opt_frame.grid(row=0)

    settings_title_label = root.menu_title_LABEL_SET(custom_ens_opt_frame, ADVANCED_OPTION_MENU_TEXT)
    settings_title_label.grid(pady=MENU_PADDING_2)

    delete_entry_label = root.menu_sub_LABEL_SET(custom_ens_opt_frame, REMOVE_SAVED_ENSEMBLE_TEXT)
    delete_entry_label.grid(pady=MENU_PADDING_1)
    delete_entry_option = ComboBoxMenu(
        custom_ens_opt_frame, textvariable=option_var, width=ENSEMBLE_CHECKBOXS_WIDTH + 2
    )
    delete_entry_option.grid(padx=20, pady=MENU_PADDING_1)

    is_save_all_outputs_ensemble_option = ttk.Checkbutton(
        custom_ens_opt_frame,
        text=SAVE_ALL_OUTPUTS_TEXT,
        width=ENSEMBLE_CHECKBOXS_WIDTH,
        variable=root.is_save_all_outputs_ensemble_var,
    )
    is_save_all_outputs_ensemble_option.grid(pady=0)
    root.help_hints(is_save_all_outputs_ensemble_option, text=IS_SAVE_ALL_OUTPUTS_ENSEMBLE_HELP)

    is_append_ensemble_name_option = ttk.Checkbutton(
        custom_ens_opt_frame,
        text=APPEND_ENSEMBLE_NAME_TEXT,
        width=ENSEMBLE_CHECKBOXS_WIDTH,
        variable=root.is_append_ensemble_name_var,
    )
    is_append_ensemble_name_option.grid(pady=0)
    root.help_hints(is_append_ensemble_name_option, text=IS_APPEND_ENSEMBLE_NAME_HELP)

    is_wav_ensemble_option = ttk.Checkbutton(
        custom_ens_opt_frame,
        text=ENSEMBLE_WAVFORMS_TEXT,
        width=ENSEMBLE_CHECKBOXS_WIDTH,
        variable=root.is_wav_ensemble_var,
    )
    is_wav_ensemble_option.grid(pady=0)
    root.help_hints(is_wav_ensemble_option, text=IS_WAV_ENSEMBLE_HELP)

    ensemble_return_button = ttk.Button(
        custom_ens_opt_frame,
        text=BACK_TO_MAIN_MENU,
        command=lambda: (
            root.menu_advanced_ensemble_options_close_window(),
            root.check_is_menu_settings_open(),
        ),
    )
    ensemble_return_button.grid(pady=MENU_PADDING_1)

    ensemble_close_button = ttk.Button(
        custom_ens_opt_frame,
        text=CLOSE_WINDOW,
        command=lambda: root.menu_advanced_ensemble_options_close_window(),
    )
    ensemble_close_button.grid(pady=MENU_PADDING_1)

    root.deletion_list_fill(
        delete_entry_option, option_var, ENSEMBLE_CACHE_DIR, SELECT_SAVED_ENSEMBLE, menu_name="deleteensemble"
    )

    root.menu_placement(
        custom_ens_opt,
        ADVANCED_ENSEMBLE_OPTIONS_TEXT,
        is_help_hints=True,
        close_function=root.menu_advanced_ensemble_options_close_window,
    )


def open_advanced_align_options(root: Any) -> None:
    """Open Advanced Align Options dialog."""
    advanced_align_opt = tk.Toplevel()

    root.is_open_menu_advanced_align_options.set(True)
    root.menu_advanced_align_options_close_window = lambda: (
        root.is_open_menu_advanced_align_options.set(False),
        advanced_align_opt.destroy(),
    )
    advanced_align_opt.protocol("WM_DELETE_WINDOW", root.menu_advanced_align_options_close_window)

    advanced_align_opt_frame = root.menu_FRAME_SET(advanced_align_opt)
    advanced_align_opt_frame.grid(row=0)

    settings_title_label = root.menu_title_LABEL_SET(
        advanced_align_opt_frame, ADVANCED_ALIGN_TOOL_OPTIONS_TEXT
    )
    settings_title_label.grid(pady=MENU_PADDING_2)

    phase_option_label = root.menu_sub_LABEL_SET(advanced_align_opt_frame, SECONDARY_PHASE_TEXT)
    phase_option_label.grid(pady=4)
    phase_option_option = ComboBoxMenu(
        advanced_align_opt_frame,
        textvariable=root.phase_option_var,
        values=ALIGN_PHASE_OPTIONS,
        width=MENU_COMBOBOX_WIDTH,
    )
    phase_option_option.grid(pady=4)
    root.help_hints(phase_option_label, text=IS_PHASE_HELP)

    phase_shifts_label = root.menu_sub_LABEL_SET(advanced_align_opt_frame, PHASE_SHIFTS_TEXT)
    phase_shifts_label.grid(pady=4)
    phase_shifts_option = ComboBoxMenu(
        advanced_align_opt_frame,
        textvariable=root.phase_shifts_var,
        values=list(PHASE_SHIFTS_OPT.keys()),
        width=MENU_COMBOBOX_WIDTH,
    )
    phase_shifts_option.grid(pady=4)
    root.help_hints(phase_shifts_label, text=PHASE_SHIFTS_ALIGN_HELP)

    is_save_align_option = ttk.Checkbutton(
        advanced_align_opt_frame,
        text=SAVE_ALIGNED_TRACK_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_save_align_var,
    )
    is_save_align_option.grid(pady=0)
    root.help_hints(is_save_align_option, text=IS_ALIGN_TRACK_HELP)

    is_match_silence_option = ttk.Checkbutton(
        advanced_align_opt_frame,
        text=SILENCE_MATCHING_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_match_silence_var,
    )
    is_match_silence_option.grid(pady=0)
    root.help_hints(is_match_silence_option, text=IS_MATCH_SILENCE_HELP)

    is_spec_match_option = ttk.Checkbutton(
        advanced_align_opt_frame,
        text=SPECTRAL_MATCHING_TEXT,
        width=MDX_CHECKBOXS_WIDTH,
        variable=root.is_spec_match_var,
    )
    is_spec_match_option.grid(pady=0)
    root.help_hints(is_spec_match_option, text=IS_MATCH_SPEC_HELP)

    ensemble_return_button = ttk.Button(
        advanced_align_opt_frame,
        text=BACK_TO_MAIN_MENU,
        command=lambda: (
            root.menu_advanced_align_options_close_window(),
            root.check_is_menu_settings_open(),
        ),
    )
    ensemble_return_button.grid(pady=MENU_PADDING_1)

    ensemble_close_button = ttk.Button(
        advanced_align_opt_frame,
        text=CLOSE_WINDOW,
        command=lambda: root.menu_advanced_align_options_close_window(),
    )
    ensemble_close_button.grid(pady=MENU_PADDING_1)

    root.menu_placement(
        advanced_align_opt,
        ADVANCED_ALIGN_TOOL_OPTIONS_TEXT,
        is_help_hints=True,
        close_function=root.menu_advanced_align_options_close_window,
    )
