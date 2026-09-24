"""Queue management and UI controls for UVR batch processing."""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from kthread import KThread

from gui_data.app_size_values import Y_OFFSET_QUEUE_1080P
from gui_data.constants import (
    AUDIO_TOOLS,
    CHIME_OFF_TEXT,
    CHIME_ON_TEXT,
    CHOOSE_ENSEMBLE_OPTION,
    CLEAR_PENDING_TEXT,
    ENSEMBLE_MODE,
    PROCESS_STOPPED_BY_USER,
    REMOVE_TASK_TEXT,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PAUSED,
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
)

logger = logging.getLogger(__name__)


class QueueUI:
    """Manages the UI presentation and worker processing loop for the task queue."""

    _COLLAPSED_HEIGHT = 30
    _LABEL_COLLAPSED = "Processing Queue  [+]"
    _LABEL_EXPANDED = "Processing Queue  [-]"

    def __init__(self, root: Any) -> None:
        self.root = root
        self._is_queue_expanded: bool = False

    def setup_ui(self) -> None:
        """Initializes the queue frame, treeview, and control buttons on the root window."""
        # Outer wrapper — always visible; height toggles between collapsed/expanded
        self.root.queue_frame = ttk.Frame(master=self.root)
        self.root.queue_frame.place(
            x=15,
            y=Y_OFFSET_QUEUE_1080P,
            width=-30,
            height=self._COLLAPSED_HEIGHT,
            relx=0,
            rely=0,
            relwidth=1,
            relheight=0,
        )

        # Toggle header button
        self._toggle_btn = ttk.Button(
            self.root.queue_frame,
            text=self._LABEL_COLLAPSED,
            command=self.toggle_queue_visibility,
        )
        self._toggle_btn.pack(side="top", fill="x")

        # Inner content frame — shown/hidden by toggle
        self._queue_content = ttk.Frame(self.root.queue_frame)

        queue_buttons_frame = ttk.Frame(self._queue_content)
        queue_buttons_frame.pack(side="bottom", fill="x", pady=5)

        scrollbar = ttk.Scrollbar(self._queue_content, orient="vertical")

        self.root.queue_treeview = ttk.Treeview(
            self._queue_content,
            columns=("id", "inputs", "method", "status"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=4,
        )
        scrollbar.config(command=self.root.queue_treeview.yview)
        scrollbar.pack(side="right", fill="y")
        self.root.queue_treeview.pack(side="top", fill="both", expand=True)

        self.root.queue_treeview.heading("id", text="ID")
        self.root.queue_treeview.heading("inputs", text="Input Files")
        self.root.queue_treeview.heading("method", text="Model / Method")
        self.root.queue_treeview.heading("status", text="Status")

        self.root.queue_treeview.column("id", width=50, anchor="center")
        self.root.queue_treeview.column("inputs", width=260, anchor="w")
        self.root.queue_treeview.column("method", width=160, anchor="w")
        self.root.queue_treeview.column("status", width=100, anchor="center")

        def _queue_scroll(event: Any) -> str:
            if event.num == 5 or event.delta < 0:
                self.root.queue_treeview.yview_scroll(2, "units")
            elif event.num == 4 or event.delta > 0:
                self.root.queue_treeview.yview_scroll(-2, "units")
            return "break"

        self.root.queue_treeview.bind("<MouseWheel>", _queue_scroll)
        self.root.queue_treeview.bind("<Button-4>", _queue_scroll)
        self.root.queue_treeview.bind("<Button-5>", _queue_scroll)

        self.root.remove_task_button = ttk.Button(
            queue_buttons_frame,
            text=REMOVE_TASK_TEXT,
            command=self.remove_selected_task,
            width=15,
        )
        self.root.remove_task_button.pack(side="left", padx=5)

        self.root.pause_resume_task_button = ttk.Button(
            queue_buttons_frame,
            image=self.root.pause_img,
            command=self.pause_resume_selected_task,
        )
        self.root.pause_resume_task_button.pack(side="left", padx=5)

        self.root.move_up_task_button = ttk.Button(
            queue_buttons_frame,
            image=self.root.up_img,
            command=self.move_task_up,
        )
        self.root.move_up_task_button.pack(side="left", padx=5)

        self.root.move_down_task_button = ttk.Button(
            queue_buttons_frame,
            image=self.root.down_img,
            command=self.move_task_down,
        )
        self.root.move_down_task_button.pack(side="left", padx=5)

        self.root.clear_queue_button = ttk.Button(
            queue_buttons_frame,
            text=CLEAR_PENDING_TEXT,
            command=self.clear_task_queue,
            width=15,
        )
        self.root.clear_queue_button.pack(side="right", padx=5)

        self.root.chime_toggle_button = ttk.Button(
            queue_buttons_frame,
            text=CHIME_ON_TEXT if self.root.is_task_complete_var.get() else CHIME_OFF_TEXT,
            command=self.toggle_chime,
            width=3,
        )
        self.root.chime_toggle_button.pack(side="right", padx=5)

        self.root.is_task_complete_var.trace_add("write", self.update_chime_button_text)

        self.root.queue_treeview.bind("<<TreeviewSelect>>", self.queue_selection_changed)

        self.update_queue_ui_display()

    def toggle_queue_visibility(self) -> None:
        """Expand or collapse the queue treeview panel."""
        self._is_queue_expanded = not self._is_queue_expanded
        if self._is_queue_expanded:
            self._queue_content.pack(side="top", fill="both", expand=True)
            self._toggle_btn.configure(text=self._LABEL_EXPANDED)
            self.root.queue_frame.place_configure(height=self.root.QUEUE_HEIGHT)
        else:
            self._queue_content.pack_forget()
            self._toggle_btn.configure(text=self._LABEL_COLLAPSED)
            self.root.queue_frame.place_configure(height=self._COLLAPSED_HEIGHT)



    def start_worker(self) -> None:
        """Starts the queue worker thread if it is not already running."""
        if not self.root.is_queue_worker_running:
            self.root.queue_worker_thread = KThread(target=self.queue_worker_loop)
            self.root.queue_worker_thread.start()

    def queue_worker_loop(self) -> None:
        """Main background processing loop consuming tasks from the processing queue."""
        self.root.is_queue_worker_running = True
        last_task_error = None
        while True:
            # Find the first pending task under lock
            task = None
            with self.root.queue_lock:
                for t in self.root.processing_queue:
                    if t.status == TASK_STATUS_PENDING and not t.is_paused:
                        task = t
                        break
                if not task:
                    break

                self.root.active_queue_task = task
                task.status = TASK_STATUS_RUNNING

            self.update_queue_ui_display()

            # Reset is_process_stopped flag before starting
            self.root.is_process_stopped = False
            # Keep button enabled so user can still enqueue while processing
            self.root.after(0, self.root.process_button_queue_mode)

            task_error: list[Any] = [None]

            # Prepare target function with error capture
            def make_target(t: Any, err_holder: list[Any]) -> Any:
                if t.process_method == AUDIO_TOOLS:
                    base_fn = lambda: self.root.process_tool_start(task=t)
                else:
                    base_fn = lambda: self.root.process_start(task=t)

                def wrapped() -> None:
                    try:
                        base_fn()
                    except Exception as exc:
                        err_holder[0] = exc

                return wrapped

            # Start the task in a KThread
            self.root.active_processing_thread = KThread(target=make_target(task, task_error))
            self.root.active_processing_thread.start()

            # Wait for the task thread to complete
            self.root.active_processing_thread.join()

            # Post-processing status update
            with self.root.queue_lock:
                if self.root.is_process_stopped:
                    task.status = TASK_STATUS_FAILED
                    self.root.command_Text.write(f"\nTask {task.id} stopped by user.\n")
                elif task_error[0] is not None:
                    task.status = TASK_STATUS_FAILED
                    last_task_error = task_error[0]
                elif task.status == TASK_STATUS_RUNNING:
                    task.status = TASK_STATUS_COMPLETED
                    try:
                        self.root.history_manager.add_entry(
                            task_id=task.id,
                            process_method=getattr(task, "process_method", "Unknown"),
                            model_name=getattr(task.model_data, "model_name", "Unknown")
                            if hasattr(task, "model_data") and task.model_data
                            else "Unknown",
                            input_files=list(getattr(task, "input_paths", [])),
                            export_path=getattr(task, "export_path", ""),
                            duration_seconds=0.0,
                            status="Completed",
                        )
                    except Exception:
                        pass

                self.root.active_queue_task = None
            self.update_queue_ui_display()

        self.root.is_queue_worker_running = False
        self.root.active_processing_thread = None
        self.root.after(0, lambda: self.root.process_end(error=last_task_error))

    def remove_selected_task(self) -> None:
        """Removes or cancels the selected task in the queue Treeview."""
        if not hasattr(self.root, "queue_treeview") or not self.root.queue_treeview:
            return
        selected = self.root.queue_treeview.selection()
        if not selected:
            return

        item = self.root.queue_treeview.item(selected[0])
        task_id = item["values"][0]

        task_to_remove = None
        with self.root.queue_lock:
            for task in self.root.processing_queue:
                if task.id == task_id:
                    task_to_remove = task
                    break

        if not task_to_remove:
            return

        if task_to_remove.status == TASK_STATUS_RUNNING:
            confirm = messagebox.askyesno(
                parent=self.root,
                title="Cancel Task",
                message="Are you sure you want to cancel the currently processing task?",
            )
            if confirm:
                if self.root.thread_check(self.root.active_processing_thread):
                    try:
                        self.root.active_processing_thread.terminate()
                    finally:
                        self.root.is_process_stopped = True
                        self.root.command_Text.write(PROCESS_STOPPED_BY_USER)
                        with self.root.queue_lock:
                            if task_to_remove in self.root.processing_queue:
                                self.root.processing_queue.remove(task_to_remove)
                        self.update_queue_ui_display()
        else:
            with self.root.queue_lock:
                if task_to_remove in self.root.processing_queue:
                    self.root.processing_queue.remove(task_to_remove)
            self.update_queue_ui_display()

    def clear_task_queue(self) -> None:
        """Clears all pending tasks from the queue upon confirmation."""
        confirm = messagebox.askyesno(
            parent=self.root,
            title=CLEAR_PENDING_TEXT,
            message="Are you sure you want to clear all pending tasks from the queue?",
        )
        if confirm:
            with self.root.queue_lock:
                self.root.processing_queue = [
                    t
                    for t in self.root.processing_queue
                    if t.status in [TASK_STATUS_RUNNING, TASK_STATUS_COMPLETED, TASK_STATUS_FAILED]
                ]
            self.update_queue_ui_display()

    def update_queue_ui_display(self) -> None:
        """Refreshes the Treeview widget to display current queued tasks and statuses."""
        with self.root.queue_lock:
            tasks_snapshot = list(self.root.processing_queue)

        def _update() -> None:
            if (
                hasattr(self.root, "queue_treeview")
                and self.root.queue_treeview
                and self.root.queue_treeview.winfo_exists()
            ):
                for item in self.root.queue_treeview.get_children():
                    self.root.queue_treeview.delete(item)
                for task in reversed(tasks_snapshot):
                    if task.process_method == AUDIO_TOOLS:
                        method_str = task.chosen_audio_tool
                    else:
                        if task.process_method == ENSEMBLE_MODE:
                            if (
                                hasattr(task, "chosen_ensemble")
                                and task.chosen_ensemble
                                and task.chosen_ensemble != CHOOSE_ENSEMBLE_OPTION
                            ):
                                method_str = f"Ensemble - {task.chosen_ensemble}"
                            else:
                                method_str = "Ensemble"
                        else:
                            if isinstance(task.model_data, list) and task.model_data:
                                method_str = ", ".join(m.model_name for m in task.model_data)
                            elif task.model_data:
                                method_str = task.model_data.model_name
                            else:
                                method_str = task.process_method

                    status_str = task.status
                    if task.is_paused and task.status == TASK_STATUS_PENDING:
                        status_str = TASK_STATUS_PAUSED

                    if not task.input_paths:
                        self.root.queue_treeview.insert(
                            "", tk.END, values=(task.id, "No Inputs", method_str, status_str)
                        )
                    else:
                        parent = self.root.queue_treeview.insert(
                            "",
                            tk.END,
                            values=(
                                task.id,
                                os.path.basename(task.input_paths[0]),
                                method_str,
                                status_str,
                            ),
                            open=True,
                        )
                        for p in task.input_paths[1:]:
                            self.root.queue_treeview.insert(
                                parent, tk.END, values=(task.id, os.path.basename(p), "", "")
                            )

        self.root.after(0, _update)

    def pause_resume_selected_task(self) -> None:
        """Toggles pause/resume state for the selected task."""
        if not hasattr(self.root, "queue_treeview") or not self.root.queue_treeview:
            return
        selected = self.root.queue_treeview.selection()
        if not selected:
            return
        item = self.root.queue_treeview.item(selected[0])
        task_id = item["values"][0]

        for task in self.root.processing_queue:
            if task.id == task_id:
                if task.status == TASK_STATUS_FAILED:
                    task.status = TASK_STATUS_PENDING
                    task.is_paused = False
                    self.update_queue_ui_display()
                    self.queue_selection_changed()
                    self.start_worker()
                elif task.status == TASK_STATUS_RUNNING:
                    self.root.is_process_paused = not getattr(self.root, "is_process_paused", False)
                    task.is_paused = self.root.is_process_paused
                    if self.root.is_process_paused:
                        self.root.progress_text_var.set("Process Paused...")
                    self.update_queue_ui_display()
                    self.queue_selection_changed()
                elif task.status == TASK_STATUS_PENDING:
                    task.is_paused = not task.is_paused
                    self.update_queue_ui_display()
                    self.queue_selection_changed()

                    if not task.is_paused:
                        self.start_worker()
                break

    def move_task_up(self) -> None:
        """Moves the selected pending task up one position in queue."""
        self.move_task_direction(1)

    def move_task_down(self) -> None:
        """Moves the selected pending task down one position in queue."""
        self.move_task_direction(-1)

    def move_task_direction(self, direction: int) -> None:
        """Moves the selected pending task up or down by the specified direction index."""
        if not hasattr(self.root, "queue_treeview") or not self.root.queue_treeview:
            return
        selected = self.root.queue_treeview.selection()
        if not selected:
            return
        item = self.root.queue_treeview.item(selected[0])
        task_id = item["values"][0]

        with self.root.queue_lock:
            idx = -1
            for i, task in enumerate(self.root.processing_queue):
                if task.id == task_id:
                    idx = i
                    break

            if idx == -1:
                return

            task = self.root.processing_queue[idx]

            if task.status == TASK_STATUS_RUNNING:
                return

            new_idx = idx + direction

            if new_idx < 0 or new_idx >= len(self.root.processing_queue):
                return

            if self.root.processing_queue[new_idx].status == TASK_STATUS_RUNNING:
                return

            self.root.processing_queue[idx], self.root.processing_queue[new_idx] = (
                self.root.processing_queue[new_idx],
                self.root.processing_queue[idx],
            )

        self.update_queue_ui_display()

        for child in self.root.queue_treeview.get_children():
            if self.root.queue_treeview.item(child)["values"][0] == task_id:
                self.root.queue_treeview.selection_set(child)
                self.root.queue_treeview.focus(child)
                break

    def queue_selection_changed(self, event: Any = None) -> None:
        """Handles selection state change in the queue Treeview, updating button states."""
        if not hasattr(self.root, "queue_treeview") or not self.root.queue_treeview:
            return
        selected = self.root.queue_treeview.selection()
        if not selected:
            if hasattr(self.root, "pause_resume_task_button"):
                self.root.pause_resume_task_button.config(state=tk.DISABLED)
                self.root.move_up_task_button.config(state=tk.DISABLED)
                self.root.move_down_task_button.config(state=tk.DISABLED)
            return

        item = self.root.queue_treeview.item(selected[0])
        task_id = item["values"][0]

        task_status = None
        task_obj = None
        for task in self.root.processing_queue:
            if task.id == task_id:
                task_status = task.status
                task_obj = task
                break

        if task_status == TASK_STATUS_FAILED:
            self.root.pause_resume_task_button.config(state=tk.NORMAL, image=self.root.play_img)
            self.root.move_up_task_button.config(state=tk.DISABLED)
            self.root.move_down_task_button.config(state=tk.DISABLED)
        elif task_status == TASK_STATUS_RUNNING:
            self.root.pause_resume_task_button.config(state=tk.NORMAL)
            if getattr(self.root, "is_process_paused", False):
                self.root.pause_resume_task_button.config(image=self.root.play_img)
            else:
                self.root.pause_resume_task_button.config(image=self.root.pause_img)
            self.root.move_up_task_button.config(state=tk.DISABLED)
            self.root.move_down_task_button.config(state=tk.DISABLED)
        elif task_status == TASK_STATUS_COMPLETED:
            self.root.pause_resume_task_button.config(state=tk.DISABLED)
            self.root.move_up_task_button.config(state=tk.DISABLED)
            self.root.move_down_task_button.config(state=tk.DISABLED)
        else:
            self.root.pause_resume_task_button.config(state=tk.NORMAL)
            if task_obj and task_obj.is_paused:
                self.root.pause_resume_task_button.config(image=self.root.play_img)
            else:
                self.root.pause_resume_task_button.config(image=self.root.pause_img)
            self.root.move_up_task_button.config(state=tk.NORMAL)
            self.root.move_down_task_button.config(state=tk.NORMAL)

    def toggle_chime(self) -> None:
        """Toggles the chime completion sound on or off."""
        self.root.is_task_complete_var.set(not self.root.is_task_complete_var.get())

    def update_chime_button_text(self, *args: Any) -> None:
        """Updates chime button text based on task completion chime setting."""
        if hasattr(self.root, "chime_toggle_button"):
            self.root.chime_toggle_button.config(
                text=CHIME_ON_TEXT if self.root.is_task_complete_var.get() else CHIME_OFF_TEXT
            )
