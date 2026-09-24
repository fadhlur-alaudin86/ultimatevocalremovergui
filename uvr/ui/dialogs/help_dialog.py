"""Help, error log, model selection, and manual download dialog builders for UVR."""

from __future__ import annotations

import json
import logging
import os
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import ttk
from typing import Any

from __version__ import VERSION
from gui_data.app_size_values import (
    DEMUCS_PRE_CHECKBOXS_WIDTH,
    FONT_SIZE_1,
    FONT_SIZE_2,
    FONT_SIZE_3,
    FONT_SIZE_4,
    FONT_SIZE_6,
    MENU_PADDING_1,
    MENU_PADDING_2,
    MENU_PADDING_3,
    MENU_PADDING_4,
    READ_ONLY_COMBO_WIDTH,
)
from gui_data.constants import (
    ACTIVATE_PRE_PROCESS_MODEL_TEXT,
    ACTIVATE_SECONDARY_MODEL_TEXT,
    BACK_TO_MAIN_MENU,
    BASS_PAIR,
    CKPT,
    CLOSE_WINDOW,
    COPY_ALL_TEXT_TEXT,
    DEMUCS_ARCH_TYPE,
    DONATE_LINK_BMAC,
    DRUM_PAIR,
    ERROR_CONSOLE_TEXT,
    FG_COLOR,
    ISSUE_LINK,
    LICENSE_TEXT,
    MANUAL_DOWNLOADS_TEXT,
    MDX23_CONFIG_CHECKS,
    MDX_23_NAME,
    MDX_ARCH_TYPE,
    NO_MODEL,
    NORMAL_REPO,
    ONNX,
    OPEN_LINK_TO_MODEL_TEXT,
    OPEN_MODEL_DIRECTORY_TEXT,
    OTHER_PAIR,
    PRE_PROC_MODEL_ACTIVATE_HELP,
    PRE_PROC_MODEL_INST_MIX_HELP,
    PREPROCESS_MODEL_CHOOSE_TEXT,
    READ_ONLY,
    REPORT_ISSUE_TEXT,
    SECONDARY_MODEL_ACTIVATE_HELP,
    SECONDARY_MODEL_HELP,
    SECONDARY_MODEL_SCALE_HELP,
    SECONDARY_MODEL_TEXT,
    SELECT_MODEL_TEXT,
    SELECTED_MODEL_PLACE_PATH_TEXT,
    UVR_ERROR_LOG_TEXT,
    VOCAL_PAIR,
    VR_ARCH_TYPE,
)
from uvr.constants import (
    DEMUCS_MODELS_DIR,
    DEMUCS_NEWER_REPO_DIR,
    DOWNLOAD_MODEL_CACHE,
    MAIN_FONT_NAME,
    MDX_C_CONFIG_PATH,
    MDX_MODELS_DIR,
    VR_MODELS_DIR,
)
from uvr.ui.components import ComboBoxMenu

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Help / Information guide
# ---------------------------------------------------------------------------


def open_help_menu(
    root: Any,
    right_click_button: str,
    right_click_release_linux: Any,
    is_macos: bool,
    current_patch: str,
    auto_hyperlink: Any,
) -> None:
    """Open the Help / Information Guide toplevel window."""

    help_guide_opt = tk.Toplevel()

    root.is_open_menu_help.set(True)
    root.menu_help_close_window = lambda: (
        root.is_open_menu_help.set(False),
        help_guide_opt.destroy(),
    )
    help_guide_opt.protocol("WM_DELETE_WINDOW", root.menu_help_close_window)

    tabControl = ttk.Notebook(help_guide_opt)

    tab1 = ttk.Frame(tabControl)
    tab2 = ttk.Frame(tabControl)
    tab3 = ttk.Frame(tabControl)
    tab4 = ttk.Frame(tabControl)

    tabControl.add(tab1, text="Credits")
    tabControl.add(tab2, text="Resources")
    tabControl.add(tab3, text="Application License & Version Information")
    tabControl.add(tab4, text="Additional Information")

    tabControl.pack(expand=1, fill="both")

    tab1.grid_rowconfigure(0, weight=1)
    tab1.grid_columnconfigure(0, weight=1)

    tab2.grid_rowconfigure(0, weight=1)
    tab2.grid_columnconfigure(0, weight=1)

    tab3.grid_rowconfigure(0, weight=1)
    tab3.grid_columnconfigure(0, weight=1)

    tab4.grid_rowconfigure(0, weight=1)
    tab4.grid_columnconfigure(0, weight=1)

    section_title_Label = lambda place, frame, text, font_size=FONT_SIZE_4: tk.Label(
        master=frame,
        text=text,
        font=(MAIN_FONT_NAME, f"{font_size}", "bold"),
        justify="center",
        fg="#F4F4F4",
    ).grid(row=place, column=0, padx=0, pady=MENU_PADDING_4)

    description_Label = lambda place, frame, text, font=FONT_SIZE_2: tk.Label(
        master=frame,
        text=text,
        font=(MAIN_FONT_NAME, f"{font}"),
        justify="center",
        fg="#F6F6F7",
    ).grid(row=place, column=0, padx=0, pady=MENU_PADDING_4)

    def credit_label(place, frame, text, link=None, message=None, is_link=False, is_top=False):
        if is_top:
            thank = tk.Label(
                master=frame,
                text=text,
                font=(MAIN_FONT_NAME, f"{FONT_SIZE_3}", "bold"),
                justify="center",
                fg="#13849f",
            )
        else:
            thank = tk.Label(
                master=frame,
                text=text,
                font=(MAIN_FONT_NAME, f"{FONT_SIZE_3}", "underline" if is_link else "normal"),
                justify="center",
                fg="#13849f",
            )
        thank.configure(cursor="hand2") if is_link else None
        thank.grid(row=place, column=0, padx=0, pady=1)
        if link:
            thank.bind("<Button-1>", lambda e: webbrowser.open_new_tab(link))
        if message:
            description_Label(place + 1, frame, message)

    def Link(place, frame, text, link, description, font=FONT_SIZE_2):
        link_label = tk.Label(
            master=frame,
            text=text,
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}", "underline"),
            foreground=FG_COLOR,
            justify="center",
            cursor="hand2",
        )
        link_label.grid(row=place, column=0, padx=0, pady=MENU_PADDING_1)
        link_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab(link))
        description_Label(place + 1, frame, description, font=font)

    def right_click_menu(event):
        rc_menu = tk.Menu(root, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
        rc_menu.add_command(
            label="Return to Settings Menu",
            command=lambda: (
                root.menu_help_close_window(),
                root.check_is_menu_settings_open(),
            ),
        )
        rc_menu.add_command(label="Exit Window", command=lambda: root.menu_help_close_window())
        try:
            rc_menu.tk_popup(event.x_root, event.y_root)
            right_click_release_linux(rc_menu, help_guide_opt)
        finally:
            rc_menu.grab_release()

    help_guide_opt.bind(right_click_button, lambda e: right_click_menu(e))

    credits_Frame = tk.Frame(tab1, highlightthicknes=50)
    credits_Frame.grid(row=0, column=0, padx=0, pady=0)
    tk.Label(credits_Frame, image=root.credits_img).grid(row=1, column=0, padx=0, pady=MENU_PADDING_1)

    section_title_Label(place=0, frame=credits_Frame, text="Core UVR Developers")

    credit_label(place=2, frame=credits_Frame, text="Anjok07\nAufr33", is_top=True)

    section_title_Label(place=3, frame=credits_Frame, text="Special Thanks")

    credit_label(
        place=6,
        frame=credits_Frame,
        text="Tsurumeso",
        message="Developed the original VR Architecture AI code.",
        link="https://github.com/tsurumeso/vocal-remover",
        is_link=True,
    )

    credit_label(
        place=8,
        frame=credits_Frame,
        text="Kuielab & Woosung Choi",
        message="Developed the original MDX-Net AI code.",
        link="https://github.com/kuielab",
        is_link=True,
    )

    credit_label(
        place=10,
        frame=credits_Frame,
        text="Adefossez & Demucs",
        message="Core developer of Facebook's Demucs Music Source Separation.",
        link="https://github.com/facebookresearch/demucs",
        is_link=True,
    )

    credit_label(
        place=12,
        frame=credits_Frame,
        text="Bas Curtiz",
        message="Designed the official UVR logo, icon, banner, splash screen.",
    )

    credit_label(
        place=14,
        frame=credits_Frame,
        text="DilanBoskan",
        message="Your contributions at the start of this project were essential to the success of UVR. Thank you!",
    )

    credit_label(
        place=16,
        frame=credits_Frame,
        text="Audio Separation and CC Karaoke & Friends Discord Communities",
        message="Thank you for the support!",
    )

    more_info_tab_Frame = tk.Frame(tab2, highlightthicknes=30)
    more_info_tab_Frame.grid(row=0, column=0, padx=0, pady=0)

    section_title_Label(place=3, frame=more_info_tab_Frame, text="Resources")

    Link(
        place=4,
        frame=more_info_tab_Frame,
        text="Ultimate Vocal Remover (Official GitHub)",
        link="https://github.com/Anjok07/ultimatevocalremovergui",
        description="You can find updates, report issues, and give us a shout via our official GitHub.",
        font=FONT_SIZE_1,
    )

    Link(
        place=8,
        frame=more_info_tab_Frame,
        text="X-Minus AI",
        link="https://x-minus.pro/ai",
        description=(
            "Many of the models provided are also on X-Minus.\n"
            "X-Minus benefits users without the computing resources to run the GUI or models locally."
        ),
        font=FONT_SIZE_1,
    )

    Link(
        place=12,
        frame=more_info_tab_Frame,
        text="MVSep",
        link="https://mvsep.com/quality_checker/leaderboard.php",
        description=(
            "Some of our models are also on MVSep.\n"
            "Click the link above for a list of some of the best settings \n"
            "and model combinations recorded by fellow UVR users.\n"
            "Special thanks to ZFTurbo for all his work on MVSep!"
        ),
        font=FONT_SIZE_1,
    )

    Link(
        place=18,
        frame=more_info_tab_Frame,
        text="FFmpeg",
        link="https://www.wikihow.com/Install-FFmpeg-on-Windows",
        description=(
            "UVR relies on FFmpeg for processing non-wav audio files.\n"
            "If you are missing FFmpeg, please see the installation guide via the link provided."
        ),
        font=FONT_SIZE_1,
    )

    Link(
        place=22,
        frame=more_info_tab_Frame,
        text="Rubber Band Library",
        link="https://breakfastquay.com/rubberband/",
        description=(
            "UVR uses the Rubber Band library for the sound stretch and pitch shift tool.\n"
            "You can get more information on it via the link provided."
        ),
        font=FONT_SIZE_1,
    )

    Link(
        place=26,
        frame=more_info_tab_Frame,
        text="Matchering",
        link="https://github.com/sergree/matchering",
        description=(
            'UVR uses the Matchering library for the "Matchering" Audio Tool.\n'
            "You can get more information on it via the link provided."
        ),
        font=FONT_SIZE_1,
    )

    Link(
        place=30,
        frame=more_info_tab_Frame,
        text="Official UVR BMAC",
        link=DONATE_LINK_BMAC,
        description="If you wish to support and donate to this project, click the link above!",
        font=FONT_SIZE_1,
    )

    appplication_license_tab_Frame = tk.Frame(tab3)
    appplication_license_tab_Frame.grid(row=0, column=0, padx=0, pady=0)

    appplication_license_Label = tk.Label(
        appplication_license_tab_Frame,
        text="UVR License Information",
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_6}", "bold"),
        justify="center",
        fg="#f4f4f4",
    )
    appplication_license_Label.grid(row=0, column=0, padx=0, pady=25)

    appplication_license_Text = tk.Text(
        appplication_license_tab_Frame,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}"),
        fg="white",
        bg="black",
        width=72,
        wrap=tk.WORD,
        borderwidth=0,
    )
    appplication_license_Text.grid(row=1, column=0, padx=0, pady=0)
    appplication_license_Text_scroll = ttk.Scrollbar(appplication_license_tab_Frame, orient=tk.VERTICAL)
    appplication_license_Text.config(yscrollcommand=appplication_license_Text_scroll.set)
    appplication_license_Text_scroll.configure(command=appplication_license_Text.yview)
    appplication_license_Text.grid(row=4, sticky=tk.W)
    appplication_license_Text_scroll.grid(row=4, column=1, sticky=tk.NS)
    appplication_license_Text.insert("insert", LICENSE_TEXT(VERSION, current_patch))
    appplication_license_Text.configure(state=tk.DISABLED)

    application_change_log_tab_Frame = tk.Frame(tab4)
    application_change_log_tab_Frame.grid(row=0, column=0, padx=0, pady=0)

    application_change_log_Label = tk.Label(
        application_change_log_tab_Frame,
        text="Additional Information",
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_6}", "bold"),
        justify="center",
        fg="#f4f4f4",
    )
    application_change_log_Label.grid(row=0, column=0, padx=0, pady=25)

    application_change_log_Text = tk.Text(
        application_change_log_tab_Frame,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}"),
        fg="white",
        bg="black",
        width=72,
        wrap=tk.WORD,
        borderwidth=0,
    )
    application_change_log_Text.grid(row=1, column=0, padx=40 if is_macos else 30, pady=0)
    application_change_log_Text_scroll = ttk.Scrollbar(application_change_log_tab_Frame, orient=tk.VERTICAL)
    application_change_log_Text.config(yscrollcommand=application_change_log_Text_scroll.set)
    application_change_log_Text_scroll.configure(command=application_change_log_Text.yview)
    application_change_log_Text.grid(row=4, sticky=tk.W)
    application_change_log_Text_scroll.grid(row=4, column=1, sticky=tk.NS)
    application_change_log_Text.insert("insert", root.bulletin_data)
    auto_hyperlink(application_change_log_Text)
    application_change_log_Text.configure(state=tk.DISABLED)

    root.menu_placement(help_guide_opt, "Information Guide")


# ---------------------------------------------------------------------------
# Error log dialog
# ---------------------------------------------------------------------------


def open_error_log(root: Any, right_click_button: str) -> None:
    """Open the Error Log toplevel window."""
    import pyperclip

    root.is_confirm_error_var.set(False)

    copied_var = tk.StringVar(value="")
    error_log_screen = tk.Toplevel()

    root.is_open_menu_error_log.set(True)
    root.menu_error_log_close_window = lambda: (
        root.is_open_menu_error_log.set(False),
        error_log_screen.destroy(),
    )
    error_log_screen.protocol("WM_DELETE_WINDOW", root.menu_error_log_close_window)

    error_log_frame = root.menu_FRAME_SET(error_log_screen)
    error_log_frame.grid(row=0)

    error_consol_title_Label = root.menu_title_LABEL_SET(error_log_frame, ERROR_CONSOLE_TEXT)
    error_consol_title_Label.grid(row=1, column=0, padx=20, pady=MENU_PADDING_2)

    error_details_Text = tk.Text(
        error_log_frame,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
        fg="#D37B7B",
        bg="black",
        width=110,
        wrap=tk.WORD,
        borderwidth=0,
    )
    error_details_Text.grid(row=2, column=0, padx=0, pady=0)
    error_details_Text.insert("insert", root.error_log_var.get())
    error_details_Text.bind(right_click_button, lambda e: root.right_click_menu_popup(e, text_box=True))
    root.current_text_box = error_details_Text
    error_details_Text_scroll = ttk.Scrollbar(error_log_frame, orient=tk.VERTICAL)
    error_details_Text.config(yscrollcommand=error_details_Text_scroll.set)
    error_details_Text_scroll.configure(command=error_details_Text.yview)
    error_details_Text.grid(row=2, sticky=tk.W)
    error_details_Text_scroll.grid(row=2, column=1, sticky=tk.NS)

    copy_text_Label = tk.Label(
        error_log_frame,
        textvariable=copied_var,
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
        justify="center",
        fg="#f4f4f4",
    )
    copy_text_Label.grid(padx=20, pady=0)

    copy_text_Button = ttk.Button(
        error_log_frame,
        text=COPY_ALL_TEXT_TEXT,
        width=14,
        command=lambda: (
            pyperclip.copy(error_details_Text.get(1.0, tk.END + "-1c")),
            copied_var.set("Copied!"),
        ),
    )
    copy_text_Button.grid(padx=20, pady=MENU_PADDING_1)

    report_issue_Button = ttk.Button(
        error_log_frame,
        text=REPORT_ISSUE_TEXT,
        width=14,
        command=lambda: webbrowser.open_new_tab(ISSUE_LINK),
    )
    report_issue_Button.grid(padx=20, pady=MENU_PADDING_1)

    error_log_return_Button = ttk.Button(
        error_log_frame,
        text=BACK_TO_MAIN_MENU,
        command=lambda: (root.menu_error_log_close_window(), root.menu_settings()),
    )
    error_log_return_Button.grid(padx=20, pady=MENU_PADDING_1)

    error_log_close_Button = ttk.Button(
        error_log_frame,
        text=CLOSE_WINDOW,
        command=lambda: root.menu_error_log_close_window(),
    )
    error_log_close_Button.grid(padx=20, pady=MENU_PADDING_1)

    root.menu_placement(error_log_screen, UVR_ERROR_LOG_TEXT)


# ---------------------------------------------------------------------------
# Secondary model tab builder
# ---------------------------------------------------------------------------


def build_secondary_model_tab(root: Any, tab: tk.Frame, ai_network_vars: dict) -> None:
    """Populate the Secondary Model settings tab inside an advanced options menu."""

    secondary_model_Frame = root.menu_FRAME_SET(tab)
    secondary_model_Frame.grid(row=0)

    settings_title_Label = root.menu_title_LABEL_SET(secondary_model_Frame, SECONDARY_MODEL_TEXT)
    settings_title_Label.grid(row=0, column=0, padx=0, pady=MENU_PADDING_3)

    voc_inst_list = root.model_list("Vocals", "Instrumental", is_dry_check=True)
    other_list = root.model_list("Other", "No Other", is_dry_check=True)
    bass_list = root.model_list("Bass", "No Bass", is_dry_check=True)
    drum_list = root.model_list("Drums", "No Drums", is_dry_check=True)

    voc_inst_secondary_model_var = ai_network_vars["voc_inst_secondary_model"]
    other_secondary_model_var = ai_network_vars["other_secondary_model"]
    bass_secondary_model_var = ai_network_vars["bass_secondary_model"]
    drums_secondary_model_var = ai_network_vars["drums_secondary_model"]
    voc_inst_secondary_model_scale_var = ai_network_vars["voc_inst_secondary_model_scale"]
    other_secondary_model_scale_var = ai_network_vars["other_secondary_model_scale"]
    bass_secondary_model_scale_var = ai_network_vars["bass_secondary_model_scale"]
    drums_secondary_model_scale_var = ai_network_vars["drums_secondary_model_scale"]
    is_secondary_model_activate_var = ai_network_vars["is_secondary_model_activate"]

    change_state_lambda = lambda: change_state(
        tk.NORMAL if is_secondary_model_activate_var.get() else tk.DISABLED
    )
    init_convert_to_percentage = lambda raw_value: f"{int(float(raw_value) * 100)}%"

    voc_inst_secondary_model_scale_LABEL_var = tk.StringVar(
        value=init_convert_to_percentage(voc_inst_secondary_model_scale_var.get())
    )
    other_secondary_model_scale_LABEL_var = tk.StringVar(
        value=init_convert_to_percentage(other_secondary_model_scale_var.get())
    )
    bass_secondary_model_scale_LABEL_var = tk.StringVar(
        value=init_convert_to_percentage(bass_secondary_model_scale_var.get())
    )
    drums_secondary_model_scale_LABEL_var = tk.StringVar(
        value=init_convert_to_percentage(drums_secondary_model_scale_var.get())
    )

    def change_state(new_state):
        for child_widget in secondary_model_Frame.winfo_children():
            if type(child_widget) is ComboBoxMenu:
                effective = READ_ONLY if new_state == tk.NORMAL else new_state
                child_widget.configure(state=effective)
            elif type(child_widget) is ttk.Scale:
                child_widget.configure(state=new_state)

    def convert_to_percentage(raw_value, scale_var: tk.StringVar, label_var: tk.StringVar):
        raw_value = f"{float(raw_value):0.2f}"
        scale_var.set(raw_value)
        label_var.set(f"{int(float(raw_value) * 100)}%")

    def build_widgets(stem_pair: str, model_list: list, option_var: tk.StringVar, label_var: tk.StringVar, scale_var: tk.DoubleVar):
        model_list.insert(0, NO_MODEL)
        secondary_model_Label = root.menu_sub_LABEL_SET(secondary_model_Frame, f"{stem_pair}", font_size=FONT_SIZE_3)
        secondary_model_Label.grid(pady=MENU_PADDING_1)
        secondary_model_Option = ComboBoxMenu(
            secondary_model_Frame,
            textvariable=option_var,
            values=model_list,
            dropdown_name=stem_pair,
            offset=310,
            width=READ_ONLY_COMBO_WIDTH,
        )
        secondary_model_Option.grid(pady=MENU_PADDING_1)
        secondary_scale_info_Label = tk.Label(
            secondary_model_Frame,
            textvariable=label_var,
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
            foreground=FG_COLOR,
        )
        secondary_scale_info_Label.grid(pady=0)
        secondary_model_scale_Option = ttk.Scale(
            secondary_model_Frame,
            variable=scale_var,
            from_=0.01,
            to=0.99,
            command=lambda s: convert_to_percentage(s, scale_var, label_var),
            orient="horizontal",
        )
        secondary_model_scale_Option.grid(pady=2)
        root.help_hints(secondary_model_Label, text=SECONDARY_MODEL_HELP)
        root.help_hints(secondary_scale_info_Label, text=SECONDARY_MODEL_SCALE_HELP)

    build_widgets(
        stem_pair=VOCAL_PAIR,
        model_list=voc_inst_list,
        option_var=voc_inst_secondary_model_var,
        label_var=voc_inst_secondary_model_scale_LABEL_var,
        scale_var=voc_inst_secondary_model_scale_var,
    )

    build_widgets(
        stem_pair=OTHER_PAIR,
        model_list=other_list,
        option_var=other_secondary_model_var,
        label_var=other_secondary_model_scale_LABEL_var,
        scale_var=other_secondary_model_scale_var,
    )

    build_widgets(
        stem_pair=BASS_PAIR,
        model_list=bass_list,
        option_var=bass_secondary_model_var,
        label_var=bass_secondary_model_scale_LABEL_var,
        scale_var=bass_secondary_model_scale_var,
    )

    build_widgets(
        stem_pair=DRUM_PAIR,
        model_list=drum_list,
        option_var=drums_secondary_model_var,
        label_var=drums_secondary_model_scale_LABEL_var,
        scale_var=drums_secondary_model_scale_var,
    )

    is_secondary_model_activate_Option = ttk.Checkbutton(
        secondary_model_Frame,
        text=ACTIVATE_SECONDARY_MODEL_TEXT,
        variable=is_secondary_model_activate_var,
        command=change_state_lambda,
    )
    is_secondary_model_activate_Option.grid(row=21, pady=MENU_PADDING_1)
    root.help_hints(is_secondary_model_activate_Option, text=SECONDARY_MODEL_ACTIVATE_HELP)

    change_state_lambda()

    root.change_state_lambda = change_state_lambda


# ---------------------------------------------------------------------------
# Pre-process model tab builder
# ---------------------------------------------------------------------------


def build_preproc_model_tab(root: Any, tab: tk.Frame) -> None:
    """Populate the Pre-process Model settings tab inside an advanced options menu."""

    preproc_model_Frame = root.menu_FRAME_SET(tab)
    preproc_model_Frame.grid(row=0)

    demucs_pre_proc_model_title_Label = root.menu_title_LABEL_SET(
        preproc_model_Frame, PREPROCESS_MODEL_CHOOSE_TEXT
    )
    demucs_pre_proc_model_title_Label.grid(pady=MENU_PADDING_3)

    pre_proc_list = root.model_list("Vocals", "Instrumental", is_dry_check=True, is_no_demucs=True)
    pre_proc_list.insert(0, NO_MODEL)

    enable_pre_proc_model = lambda: (
        is_demucs_pre_proc_model_inst_mix_Option.configure(state=tk.NORMAL),
        demucs_pre_proc_model_Option.configure(state=READ_ONLY),
    )
    disable_pre_proc_model = lambda: (
        is_demucs_pre_proc_model_inst_mix_Option.configure(state=tk.DISABLED),
        demucs_pre_proc_model_Option.configure(state=tk.DISABLED),
        root.is_demucs_pre_proc_model_inst_mix_var.set(False),
    )
    pre_proc_model_toggle = lambda: (
        enable_pre_proc_model() if root.is_demucs_pre_proc_model_activate_var.get() else disable_pre_proc_model()
    )

    demucs_pre_proc_model_Label = root.menu_sub_LABEL_SET(
        preproc_model_Frame, SELECT_MODEL_TEXT, font_size=FONT_SIZE_3
    )
    demucs_pre_proc_model_Label.grid()
    demucs_pre_proc_model_Option = ComboBoxMenu(
        preproc_model_Frame,
        textvariable=root.demucs_pre_proc_model_var,
        values=pre_proc_list,
        dropdown_name="demucspre",
        offset=310,
        width=READ_ONLY_COMBO_WIDTH,
    )
    demucs_pre_proc_model_Option.grid(pady=MENU_PADDING_2)

    is_demucs_pre_proc_model_inst_mix_Option = ttk.Checkbutton(
        preproc_model_Frame,
        text="Save Instrumental Mixture",
        width=DEMUCS_PRE_CHECKBOXS_WIDTH,
        variable=root.is_demucs_pre_proc_model_inst_mix_var,
    )
    is_demucs_pre_proc_model_inst_mix_Option.grid()
    root.help_hints(is_demucs_pre_proc_model_inst_mix_Option, text=PRE_PROC_MODEL_INST_MIX_HELP)

    is_demucs_pre_proc_model_activate_Option = ttk.Checkbutton(
        preproc_model_Frame,
        text=ACTIVATE_PRE_PROCESS_MODEL_TEXT,
        width=DEMUCS_PRE_CHECKBOXS_WIDTH,
        variable=root.is_demucs_pre_proc_model_activate_var,
        command=pre_proc_model_toggle,
    )
    is_demucs_pre_proc_model_activate_Option.grid()
    root.help_hints(is_demucs_pre_proc_model_activate_Option, text=PRE_PROC_MODEL_ACTIVATE_HELP)

    pre_proc_model_toggle()


# ---------------------------------------------------------------------------
# Manual downloads dialog
# ---------------------------------------------------------------------------


def open_manual_downloads(root: Any, open_file_func: Any) -> None:
    """Open the Manual Downloads toplevel window."""

    manual_downloads_menu = tk.Toplevel()
    model_selection_var = tk.StringVar(value=SELECT_MODEL_TEXT)

    if root.is_online:
        model_data = root.online_data
        with open(DOWNLOAD_MODEL_CACHE, "w") as json_file:
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
        return lambda: webbrowser.open_new_tab(link)

    def get_links():
        for widget in manual_downloads_link_Frame.winfo_children():
            widget.destroy()

        main_selection = model_selection_var.get()
        MAIN_ROW = 0

        root.menu_sub_LABEL_SET(manual_downloads_link_Frame, "Download Link(s)").grid(
            row=0, column=0, padx=0, pady=MENU_PADDING_4
        )

        if VR_ARCH_TYPE in main_selection:
            main_selection = vr_download_list[main_selection]
            model_dir = VR_MODELS_DIR
        elif MDX_ARCH_TYPE in main_selection or MDX_23_NAME in main_selection:
            mdata = mdx_download_list[main_selection]
            if isinstance(mdata, dict):
                has_custom_urls = any(val.startswith("http") for val in mdata.values())
                if has_custom_urls:
                    main_selection = mdata
                else:
                    main_selection = list(mdata.keys())[0]
            else:
                main_selection = mdata
            model_dir = MDX_MODELS_DIR
        elif DEMUCS_ARCH_TYPE in main_selection:
            model_dir = (
                DEMUCS_NEWER_REPO_DIR
                if "v3" in main_selection or "v4" in main_selection
                else DEMUCS_MODELS_DIR
            )
            main_selection = demucs_download_list[main_selection]
        else:
            model_dir = VR_MODELS_DIR

        if isinstance(main_selection, dict):
            for links in main_selection.values():
                MAIN_ROW += 1
                button_text = f" - Item {MAIN_ROW}" if len(main_selection.keys()) >= 2 else ""
                link = create_link(links)
                ttk.Button(
                    manual_downloads_link_Frame,
                    text=f"Open Link to Model{button_text}",
                    command=link,
                ).grid(row=MAIN_ROW, column=0, padx=0, pady=MENU_PADDING_1)
        else:
            link = f"{NORMAL_REPO}{main_selection}"
            link_button = ttk.Button(
                manual_downloads_link_Frame,
                text=OPEN_LINK_TO_MODEL_TEXT,
                command=lambda: webbrowser.open_new_tab(link),
            )
            link_button.grid(row=1, column=0, padx=0, pady=MENU_PADDING_2)

        root.menu_sub_LABEL_SET(manual_downloads_link_Frame, SELECTED_MODEL_PLACE_PATH_TEXT).grid(
            row=MAIN_ROW + 2, column=0, padx=0, pady=MENU_PADDING_4
        )
        ttk.Button(
            manual_downloads_link_Frame,
            text=OPEN_MODEL_DIRECTORY_TEXT,
            command=lambda: open_file_func(model_dir),
        ).grid(row=MAIN_ROW + 3, column=0, padx=0, pady=MENU_PADDING_1)

    manual_downloads_menu_Frame = root.menu_FRAME_SET(manual_downloads_menu)
    manual_downloads_menu_Frame.grid(row=0)

    manual_downloads_link_Frame = root.menu_FRAME_SET(manual_downloads_menu, thickness=5)
    manual_downloads_link_Frame.grid(row=1)

    manual_downloads_menu_title_Label = root.menu_title_LABEL_SET(
        manual_downloads_menu_Frame, MANUAL_DOWNLOADS_TEXT, width=45
    )
    manual_downloads_menu_title_Label.grid(row=0, column=0, padx=0, pady=MENU_PADDING_3)

    manual_downloads_menu_select_Label = root.menu_sub_LABEL_SET(
        manual_downloads_menu_Frame, SELECT_MODEL_TEXT
    )
    manual_downloads_menu_select_Label.grid(row=1, column=0, padx=0, pady=MENU_PADDING_1)

    manual_downloads_menu_select_Option = ttk.OptionMenu(manual_downloads_menu_Frame, model_selection_var)
    manual_downloads_menu_select_VR_Option = tk.Menu(manual_downloads_menu_select_Option["menu"])
    manual_downloads_menu_select_MDX_Option = tk.Menu(manual_downloads_menu_select_Option["menu"])
    manual_downloads_menu_select_DEMUCS_Option = tk.Menu(manual_downloads_menu_select_Option["menu"])
    manual_downloads_menu_select_Option["menu"].add_cascade(
        label="VR Models", menu=manual_downloads_menu_select_VR_Option
    )
    manual_downloads_menu_select_Option["menu"].add_cascade(
        label="MDX-Net Models", menu=manual_downloads_menu_select_MDX_Option
    )
    manual_downloads_menu_select_Option["menu"].add_cascade(
        label="Demucs Models", menu=manual_downloads_menu_select_DEMUCS_Option
    )

    for model_selection_vr in vr_download_list.keys():
        if not os.path.isfile(os.path.join(VR_MODELS_DIR, vr_download_list[model_selection_vr])):
            manual_downloads_menu_select_VR_Option.add_radiobutton(
                label=model_selection_vr, variable=model_selection_var, command=get_links
            )

    for model_selection_mdx in mdx_download_list.keys():
        model_name = mdx_download_list[model_selection_mdx]

        if isinstance(model_name, dict):
            model_filename = list(model_name.keys())[0]
            config_filename = None
            config_link = None
            for key, val in model_name.items():
                if key.endswith(".yaml") or key.endswith(".json"):
                    config_filename = key
                    config_link = val if val.startswith("http") else f"{MDX23_CONFIG_CHECKS}{val}"
                elif key.endswith(CKPT) or key.endswith(".safetensors") or key.endswith(ONNX):
                    model_filename = key
                    if val.endswith(".yaml") or val.endswith(".json"):
                        config_filename = val
                        config_link = f"{MDX23_CONFIG_CHECKS}{val}"
            model_name = model_filename
            if config_filename and config_link:
                config_local = os.path.join(MDX_C_CONFIG_PATH, config_filename)
                if not os.path.isfile(config_local):
                    try:
                        with urllib.request.urlopen(config_link) as response:
                            with open(config_local, "wb") as out_file:
                                out_file.write(response.read())
                    except Exception as exc:
                        logger.error("Error downloading config in manual downloads: %s", exc)
                        model_name = None

        if model_name:
            if not os.path.isfile(os.path.join(MDX_MODELS_DIR, model_name)):
                manual_downloads_menu_select_MDX_Option.add_radiobutton(
                    label=model_selection_mdx, variable=model_selection_var, command=get_links
                )

    for model_selection_demucs in demucs_download_list.keys():
        manual_downloads_menu_select_DEMUCS_Option.add_radiobutton(
            label=model_selection_demucs, variable=model_selection_var, command=get_links
        )

    manual_downloads_menu_select_Option.grid(row=2, column=0, padx=0, pady=MENU_PADDING_1)

    root.menu_placement(
        manual_downloads_menu,
        MANUAL_DOWNLOADS_TEXT,
        pop_up=True,
        close_function=lambda: manual_downloads_menu.destroy(),
    )
