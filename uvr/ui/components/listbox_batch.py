"""Batch input listbox frame with file reordering and duplication controls.
"""

from __future__ import annotations

import os
import tkinter as tk
from collections import Counter
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from gui_data.app_size_values import FONT_SIZE_4, FONT_SIZE_5
from gui_data.constants import FG_COLOR, MULTIPLE_FILE, SELECT_INPUTS
from uvr.constants import MAIN_FONT_NAME
from uvr.core.model_data import get_app_root


class ListboxBatchFrame(tk.Frame):
    """Listbox widget for organizing, reordering, and deduplicating batch file selections."""

    def __init__(
        self,
        master: Any = None,
        name: str = "Listbox",
        command: Callable | None = None,
        image_sel: Any = None,
        img_mapper: dict[str, Any] | None = None,
    ):
        super().__init__(master)
        self.master = master
        self.path_list: list[str] = []
        self.basename_to_path: dict[str, str] = {}

        self.label = tk.Label(
            self,
            text=name,
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_5}"),
            foreground=FG_COLOR,
        )
        self.label.pack(pady=(10, 8))

        self.input_button = ttk.Button(self, text=SELECT_INPUTS, command=self.select_input)
        self.input_button.pack(pady=(0, 10))

        self.listbox = tk.Listbox(
            self,
            activestyle="dotbox",
            font=(MAIN_FONT_NAME, f"{FONT_SIZE_4}"),
            foreground="#cdd3ce",
            background="#101414",
            exportselection=0,
            width=70,
            height=15,
        )
        self.listbox.pack(fill="both", expand=True)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack()

        img_map = img_mapper or {}
        if "up" in img_map:
            self.up_button = ttk.Button(self.button_frame, image=img_map["up"], command=self.move_up)
            self.up_button.grid(row=0, column=0)

        if "down" in img_map:
            self.down_button = ttk.Button(
                self.button_frame, image=img_map["down"], command=self.move_down
            )
            self.down_button.grid(row=0, column=1)

        if command and image_sel:
            self.move_button = ttk.Button(self.button_frame, image=image_sel, command=command)
            self.move_button.grid(row=0, column=2)

        if "copy" in img_map:
            self.duplicate_button = ttk.Button(
                self.button_frame, image=img_map["copy"], command=self.duplicate_selected
            )
            self.duplicate_button.grid(row=0, column=3)

        if "clear" in img_map:
            self.delete_button = ttk.Button(
                self.button_frame, image=img_map["clear"], command=self.delete_selected
            )
            self.delete_button.grid(row=0, column=4)

    def delete_selected(self) -> None:
        selected = self.listbox.curselection()
        if selected:
            basename = self.listbox.get(selected[0]).split(": ", 1)[1]
            path_to_delete = self.basename_to_path.get(basename)
            if basename in self.basename_to_path:
                del self.basename_to_path[basename]
            if path_to_delete in self.path_list:
                self.path_list.remove(path_to_delete)
            self.listbox.delete(selected)
            self.update_displayed_index()

    def select_input(self, inputs: list[str] | None = None) -> None:
        root = get_app_root()
        files = inputs if inputs else (root.show_file_dialog(dialoge_type=MULTIPLE_FILE) if root else [])
        for file in files:
            if file not in self.path_list:
                basename = os.path.basename(file)
                self.listbox.insert(tk.END, basename)
                self.path_list.append(file)
                self.basename_to_path[basename] = file
        self.update_displayed_index(is_acc_dupe=False)

    def duplicate_selected(self) -> None:
        selected = self.listbox.curselection()
        if selected:
            basename = self.listbox.get(selected[0]).split(": ", 1)[1]
            path_to_duplicate = self.basename_to_path.get(basename)
            if path_to_duplicate:
                self.path_list.append(path_to_duplicate)
                self.update_displayed_index()

    def update_displayed_index(self, inputs: list[str] | None = None, is_acc_dupe: bool = True) -> None:
        self.basename_to_path = {}
        if inputs:
            self.path_list = inputs

        basename_count = Counter(self.path_list)

        for i in range(len(self.path_list)):
            basename = os.path.basename(self.path_list[i])

            if basename_count[self.path_list[i]] > 1 and is_acc_dupe:
                j = 1
                new_basename = f"{basename} ({j})"
                while new_basename in self.basename_to_path:
                    j += 1
                    new_basename = f"{basename} ({j})"
                basename = new_basename

            self.basename_to_path[basename] = self.path_list[i]
            self.listbox.delete(i)
            self.listbox.insert(i, f"{i + 1}: {basename}")

    def move_up(self) -> None:
        selected = self.listbox.curselection()
        if selected and selected[0] > 0:
            self.path_list[selected[0] - 1], self.path_list[selected[0]] = (
                self.path_list[selected[0]],
                self.path_list[selected[0] - 1],
            )
            self.update_displayed_index()
            self.listbox.select_set(selected[0] - 1)

    def move_down(self) -> None:
        selected = self.listbox.curselection()
        if selected and selected[0] < self.listbox.size() - 1:
            self.path_list[selected[0] + 1], self.path_list[selected[0]] = (
                self.path_list[selected[0]],
                self.path_list[selected[0] + 1],
            )
            self.update_displayed_index()
            self.listbox.select_set(selected[0] + 1)

    def get_selected_path(self) -> str | None:
        selected = self.listbox.curselection()
        if selected:
            basename = self.listbox.get(selected[0]).split(": ", 1)[1]
            return self.basename_to_path.get(basename)
        return None
