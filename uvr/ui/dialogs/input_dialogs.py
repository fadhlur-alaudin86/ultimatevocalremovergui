"""Input viewing and dual audio batch processing dialogs for UVR."""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import ttk
from typing import Any

from kthread import KThread

from gui_data.app_size_values import (
    FONT_SIZE_1,
    MENU_PADDING_1,
    MENU_PADDING_2,
)
from gui_data.constants import (
    AUDIO_INPUT_TOTAL_TEXT,
    BATCH_MODE_DUAL,
    BROKEN_OR_INCOM_TEXT,
    CLOSE_WINDOW,
    CONFIRM_ENTRIES,
    DETECTED_VER,
    DUAL_AUDIO_PROCESSING,
    FG_COLOR,
    FILE_1_LB,
    FILE_2_LB,
    NO_FILES_TEXT,
    OPERATING_SYSTEM,
    REMOVED_FILES,
    SAMPLE_BEGIN,
    SELECT_INPUTS,
    SELECTED_INPUTS,
    SELECTED_VER,
    VERIFY_BEGIN,
    VERIFY_INPUTS_TEXT,
)
from gui_data.tkinterdnd2 import DND_FILES
from uvr.constants import MAIN_FONT_NAME
from uvr.ui.components.listbox_batch import ListboxBatchFrame

logger = logging.getLogger(__name__)


def open_view_inputs(
    root: Any,
    right_click_button: str,
    right_click_release_linux: Any,
    open_file_func: Any,
    drop_func: Any,
    is_dnd_compatible: bool,
) -> None:
    """Open the Selected Inputs window."""
    menu_view_inputs_top = tk.Toplevel(root)

    root.is_open_menu_view_inputs.set(True)
    root.menu_view_inputs_close_window = lambda: close_window()
    menu_view_inputs_top.protocol("WM_DELETE_WINDOW", root.menu_view_inputs_close_window)

    input_length_var = tk.StringVar(value="")
    input_info_text_var = tk.StringVar(value="")
    is_widen_box_var = tk.BooleanVar(value=False)
    is_play_file_var = tk.BooleanVar(value=False)
    varification_text_var = tk.StringVar(value=VERIFY_INPUTS_TEXT)

    reset_list = lambda: (
        input_files_listbox_Option.delete(0, "end"),
        [input_files_listbox_Option.insert(tk.END, inputs) for inputs in root.inputPaths],
    )
    audio_input_total = lambda: input_length_var.set(f"{AUDIO_INPUT_TOTAL_TEXT}: {len(root.inputPaths)}")
    audio_input_total()

    def list_diff(list1, list2):
        return list(set(list1).symmetric_difference(set(list2)))

    def list_to_string(list1):
        return "\n".join("".join(sub) for sub in list1)

    def close_window():
        root.verification_thread.kill() if root.thread_check(root.verification_thread) else None
        root.is_open_menu_view_inputs.set(False)
        menu_view_inputs_top.destroy()

    def drag_n_drop(e):
        input_info_text_var.set("")
        drop_func(e, accept_mode="files")
        reset_list()
        audio_input_total()

    def selected_files(is_remove=False):
        items_list = [input_files_listbox_Option.get(i) for i in input_files_listbox_Option.curselection()]
        inputPaths = list(root.inputPaths)
        if is_remove:
            [inputPaths.remove(i) for i in items_list if items_list]
        else:
            [inputPaths.remove(i) for i in root.inputPaths if i not in items_list]
        removed_files = list_diff(root.inputPaths, inputPaths)
        [input_files_listbox_Option.delete(input_files_listbox_Option.get(0, tk.END).index(i)) for i in removed_files]
        starting_len = len(root.inputPaths)
        root.inputPaths = tuple(inputPaths)
        root.update_inputPaths()
        audio_input_total()
        input_info_text_var.set(f"{starting_len - len(root.inputPaths)} input(s) removed.")

    def box_size():
        input_info_text_var.set("")
        input_files_listbox_Option.config(width=230, height=25) if is_widen_box_var.get() else input_files_listbox_Option.config(width=110, height=17)
        root.menu_placement(menu_view_inputs_top, "Selected Inputs", pop_up=True)

    def input_options(is_select_inputs=True):
        input_info_text_var.set("")
        if is_select_inputs:
            menu_view_inputs_top.withdraw()
            root.input_select_filedialog(parent_win=menu_view_inputs_top, is_append=True)
            menu_view_inputs_top.deiconify()
        else:
            root.inputPaths = ()
        reset_list()
        root.update_inputPaths()
        audio_input_total()

    def pop_open_file_path(is_play_file=False):
        if root.inputPaths:
            track_selected = root.inputPaths[input_files_listbox_Option.index(tk.ACTIVE)]
            if os.path.isfile(track_selected):
                open_file_func(track_selected if is_play_file else os.path.dirname(track_selected))

    def get_export_dir():
        if os.path.isdir(root.export_path_var.get()):
            export_dir = root.export_path_var.get()
        else:
            export_dir = root.export_select_filedialog()
        return export_dir

    def verify_audio(is_create_samples=False):
        inputPaths = list(root.inputPaths)
        iterated_list = root.inputPaths if not is_create_samples else [input_files_listbox_Option.get(i) for i in input_files_listbox_Option.curselection()]
        removed_files = []
        export_dir = None
        total_audio_count, current_file = len(iterated_list), 0
        if iterated_list:
            for i in iterated_list:
                current_file += 1
                input_info_text_var.set(f"{SAMPLE_BEGIN if is_create_samples else VERIFY_BEGIN}{current_file}/{total_audio_count}")
                if is_create_samples:
                    export_dir = get_export_dir()
                    if not export_dir:
                        input_info_text_var.set("No export directory selected.")
                        return
                is_good, error_data = root.verify_audio(i, is_process=False, sample_path=export_dir)
                if not is_good:
                    inputPaths.remove(i)
                    removed_files.append(error_data)

            varification_text_var.set(VERIFY_INPUTS_TEXT)
            input_files_listbox_Option.configure(state=tk.NORMAL)

            if removed_files:
                input_info_text_var.set(f"{len(removed_files)} {BROKEN_OR_INCOM_TEXT}")
                error_text = ""
                for i in removed_files:
                    error_text += i
                removed_files = list_diff(root.inputPaths, inputPaths)
                [input_files_listbox_Option.delete(input_files_listbox_Option.get(0, tk.END).index(i)) for i in removed_files]
                root.error_log_var.set(REMOVED_FILES(list_to_string(removed_files), error_text))
                root.inputPaths = tuple(inputPaths)
                root.update_inputPaths()
            else:
                input_info_text_var.set("No errors found!")

            audio_input_total()
        else:
            input_info_text_var.set(f"{NO_FILES_TEXT} {SELECTED_VER if is_create_samples else DETECTED_VER}")
            varification_text_var.set(VERIFY_INPUTS_TEXT)
            input_files_listbox_Option.configure(state=tk.NORMAL)
            return

        audio_input_total()

    def verify_audio_start_thread(is_create_samples=False):
        if not root.thread_check(root.active_processing_thread):
            if not root.thread_check(root.verification_thread):
                varification_text_var.set("Stop Progress")
                input_files_listbox_Option.configure(state=tk.DISABLED)
                root.verification_thread = KThread(target=lambda: verify_audio(is_create_samples=is_create_samples))
                root.verification_thread.start()
            else:
                input_files_listbox_Option.configure(state=tk.NORMAL)
                varification_text_var.set(VERIFY_INPUTS_TEXT)
                input_info_text_var.set("Process Stopped")
                root.verification_thread.kill()
        else:
            input_info_text_var.set("You cannot verify inputs during an active process.")

    def right_click_menu(event):
        rc_menu = tk.Menu(root, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
        rc_menu.add_command(label="Remove Selected Items Only", command=lambda: selected_files(is_remove=True))
        rc_menu.add_command(label="Keep Selected Items Only", command=lambda: selected_files(is_remove=False))
        rc_menu.add_command(label="Clear All Input(s)", command=lambda: input_options(is_select_inputs=False))
        rc_menu.add_separator()
        rc_menu_sub = tk.Menu(rc_menu, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=False)
        rc_menu.add_command(label="Verify and Create Samples of Selected Inputs", command=lambda: verify_audio_start_thread(is_create_samples=True))
        rc_menu.add_cascade(label="Preferred Double Click Action", menu=rc_menu_sub)
        if is_play_file_var.get():
            rc_menu_sub.add_command(
                label="Enable: Open Audio File Directory",
                command=lambda: (
                    input_files_listbox_Option.bind("<Double-Button>", lambda e: pop_open_file_path()),
                    is_play_file_var.set(False),
                ),
            )
        else:
            rc_menu_sub.add_command(
                label="Enable: Open Audio File",
                command=lambda: (
                    input_files_listbox_Option.bind("<Double-Button>", lambda e: pop_open_file_path(is_play_file=True)),
                    is_play_file_var.set(True),
                ),
            )

        try:
            rc_menu.tk_popup(event.x_root, event.y_root)
            right_click_release_linux(rc_menu, menu_view_inputs_top)
        finally:
            rc_menu.grab_release()

    def move_selected_input(direction):
        selected = input_files_listbox_Option.curselection()
        if not selected:
            return
        idx = selected[0]
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(root.inputPaths):
            return

        paths_list = list(root.inputPaths)
        paths_list[idx], paths_list[new_idx] = paths_list[new_idx], paths_list[idx]
        root.inputPaths = tuple(paths_list)

        reset_list()
        input_files_listbox_Option.selection_set(new_idx)
        input_files_listbox_Option.activate(new_idx)
        input_files_listbox_Option.see(new_idx)
        root.update_inputPaths()

    menu_view_inputs_Frame = root.menu_FRAME_SET(menu_view_inputs_top)
    menu_view_inputs_Frame.grid(row=0)

    root.main_window_LABEL_SET(menu_view_inputs_Frame, SELECTED_INPUTS).grid(row=0, column=0, padx=0, pady=MENU_PADDING_1)
    tk.Label(menu_view_inputs_Frame, textvariable=input_length_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR).grid(row=1, column=0, padx=0, pady=MENU_PADDING_1)
    if not OPERATING_SYSTEM == "Linux":
        ttk.Button(menu_view_inputs_Frame, text=SELECT_INPUTS, command=lambda: input_options()).grid(row=2, column=0, padx=0, pady=MENU_PADDING_2)
    input_files_listbox_Option = tk.Listbox(
        menu_view_inputs_Frame,
        selectmode=tk.EXTENDED,
        activestyle="dotbox",
        font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"),
        background="#101414",
        exportselection=0,
        width=150,
        height=20,
        relief=tk.SOLID,
        borderwidth=0,
    )
    input_files_listbox_vertical_scroll = ttk.Scrollbar(menu_view_inputs_Frame, orient=tk.VERTICAL)
    input_files_listbox_Option.config(yscrollcommand=input_files_listbox_vertical_scroll.set)
    input_files_listbox_vertical_scroll.configure(command=input_files_listbox_Option.yview)
    input_files_listbox_Option.grid(row=4, sticky=tk.W)
    input_files_listbox_vertical_scroll.grid(row=4, column=1, sticky=tk.NS)

    tk.Label(menu_view_inputs_Frame, textvariable=input_info_text_var, font=(MAIN_FONT_NAME, f"{FONT_SIZE_1}"), foreground=FG_COLOR).grid(row=5, column=0, padx=0, pady=0)
    inputs_buttons_frame = tk.Frame(menu_view_inputs_Frame, bg="#101414")
    inputs_buttons_frame.grid(row=6, column=0, pady=MENU_PADDING_1)

    ttk.Button(inputs_buttons_frame, text="Add New Files", command=lambda: input_options(is_select_inputs=True), width=15).pack(side="left", padx=5)
    ttk.Button(inputs_buttons_frame, text="Remove Selected", command=lambda: selected_files(is_remove=True), width=15).pack(side="left", padx=5)
    ttk.Button(inputs_buttons_frame, image=root.up_img, command=lambda: move_selected_input(-1)).pack(side="left", padx=5)
    ttk.Button(inputs_buttons_frame, image=root.down_img, command=lambda: move_selected_input(1)).pack(side="left", padx=5)

    if is_dnd_compatible:
        menu_view_inputs_top.drop_target_register(DND_FILES)
        menu_view_inputs_top.dnd_bind("<<Drop>>", lambda e: drag_n_drop(e))
    input_files_listbox_Option.bind(right_click_button, lambda e: right_click_menu(e))
    input_files_listbox_Option.bind("<Double-Button>", lambda e: pop_open_file_path())
    input_files_listbox_Option.bind("<Delete>", lambda e: selected_files(is_remove=True))
    input_files_listbox_Option.bind("<BackSpace>", lambda e: selected_files(is_remove=False))

    reset_list()

    root.menu_placement(menu_view_inputs_top, "Selected Inputs", pop_up=True)


def open_batch_dual(
    root: Any,
    right_click_button: str,
    right_click_release_linux: Any,
    open_file_func: Any,
    drop_func: Any,
) -> None:
    """Open Dual Audio Batch Processing dialog."""
    menu_batch_dual_top = tk.Toplevel(root)

    def drag_n_drop(event, accept_mode):
        listbox = left_frame if accept_mode == FILE_1_LB else right_frame
        paths = drop_func(event, accept_mode)
        for item in paths:
            if item not in listbox.path_list:
                basename = os.path.basename(item)
                listbox.listbox.insert(tk.END, basename)
                listbox.path_list.append(item)
        listbox.update_displayed_index()

    def move_entry(is_primary=True):
        if is_primary:
            selected_frame, other_frame = left_frame, right_frame
        else:
            selected_frame, other_frame = right_frame, left_frame

        selected = selected_frame.listbox.curselection()

        if selected:
            basename = selected_frame.listbox.get(selected[0]).split(": ", 1)[1]

            if basename in other_frame.basename_to_path:
                return

            path = selected_frame.basename_to_path[basename]

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
                open_file_func(selected_path if is_play_file else os.path.dirname(selected_path))

    def clear_all_data(lb):
        selected_frame = left_frame if lb == FILE_1_LB else right_frame
        selected_frame.listbox.delete(0, "end")
        selected_frame.path_list.clear()
        selected_frame.basename_to_path.clear()

    def clear_all(event, lb):
        selected_frame = left_frame if lb == FILE_1_LB else right_frame
        selected = selected_frame.listbox.curselection()

        right_click_menu = tk.Menu(root, font=(MAIN_FONT_NAME, FONT_SIZE_1), tearoff=0)
        if selected:
            right_click_menu.add_command(label="Open Location", command=lambda: open_selected_path(lb))
            right_click_menu.add_command(label="Open File", command=lambda: open_selected_path(lb, is_play_file=True))
        right_click_menu.add_command(label="Clear All", command=lambda: clear_all_data(lb))

        try:
            right_click_menu.tk_popup(event.x_root, event.y_root)
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

        root.DualBatch_inputPaths = list(zip(left_paths, right_paths))
        root.check_dual_paths()
        menu_batch_dual_top.destroy()

    menu_view_inputs_Frame = root.menu_FRAME_SET(menu_batch_dual_top)
    menu_view_inputs_Frame.grid(row=0)

    left_frame = ListboxBatchFrame(
        menu_view_inputs_Frame,
        root.file_one_sub_var.get().title(),
        move_entry,
        root.right_img,
        root.img_mapper,
    )
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

    right_frame = ListboxBatchFrame(
        menu_view_inputs_Frame,
        root.file_two_sub_var.get().title(),
        lambda: move_entry(False),
        root.left_img,
        root.img_mapper,
    )
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    left_frame.listbox.drop_target_register(DND_FILES)
    right_frame.listbox.drop_target_register(DND_FILES)
    left_frame.listbox.dnd_bind("<<Drop>>", lambda e: drag_n_drop(e, FILE_1_LB))
    right_frame.listbox.dnd_bind("<<Drop>>", lambda e: drag_n_drop(e, FILE_2_LB))
    left_frame.listbox.dnd_bind(right_click_button, lambda e: clear_all(e, FILE_1_LB))
    right_frame.listbox.dnd_bind(right_click_button, lambda e: clear_all(e, FILE_2_LB))

    menu_view_inputs_bottom_Frame = root.menu_FRAME_SET(menu_batch_dual_top)
    menu_view_inputs_bottom_Frame.grid(row=1)

    confirm_btn = ttk.Button(menu_view_inputs_bottom_Frame, text=CONFIRM_ENTRIES, command=gather_input_list)
    confirm_btn.grid(pady=MENU_PADDING_1)

    close_btn = ttk.Button(menu_view_inputs_bottom_Frame, text=CLOSE_WINDOW, command=lambda: menu_batch_dual_top.destroy())
    close_btn.grid(pady=MENU_PADDING_1)

    if root.check_dual_paths():
        left_frame_pane = [i[0] for i in root.DualBatch_inputPaths]
        right_frame_pane = [i[1] for i in root.DualBatch_inputPaths]
        left_frame.update_displayed_index(left_frame_pane)
        right_frame.update_displayed_index(right_frame_pane)
        root.check_dual_paths()

    root.menu_placement(menu_batch_dual_top, DUAL_AUDIO_PROCESSING, pop_up=True)


def check_dual_paths(root: Any, is_fill_menu: bool = False) -> list:
    """Validate and update dual batch input paths state."""
    if root.DualBatch_inputPaths:
        first_paths = tuple(root.DualBatch_inputPaths)
        first_paths_len = len(first_paths)
        first_paths = first_paths[0]

        if first_paths_len == 1:
            file1_base_text = os.path.basename(first_paths[0])
            file2_base_text = os.path.basename(first_paths[1])
        else:
            first_paths_len = first_paths_len - 1
            file1_base_text = f"{os.path.basename(first_paths[0])}, +{first_paths_len} file(s){BATCH_MODE_DUAL}"
            file2_base_text = f"{os.path.basename(first_paths[1])}, +{first_paths_len} file(s){BATCH_MODE_DUAL}"

        root.fileOneEntry_var.set(file1_base_text)
        root.fileOneEntry_Full_var.set(f"{first_paths[0]}")
        root.fileTwoEntry_var.set(file2_base_text)
        root.fileTwoEntry_Full_var.set(f"{first_paths[1]}")
    else:
        if is_fill_menu:
            file_one = root.fileOneEntry_Full_var.get()
            file_two = root.fileTwoEntry_Full_var.get()

            if file_one and file_two and BATCH_MODE_DUAL not in file_one and BATCH_MODE_DUAL not in file_two:
                root.DualBatch_inputPaths = [(file_one, file_two)]
        else:
            if BATCH_MODE_DUAL in root.fileOneEntry_var.get():
                root.fileOneEntry_var.set("")
                root.fileOneEntry_Full_var.set("")
            if BATCH_MODE_DUAL in root.fileTwoEntry_var.get():
                root.fileTwoEntry_var.set("")
                root.fileTwoEntry_Full_var.set("")

    return root.DualBatch_inputPaths
