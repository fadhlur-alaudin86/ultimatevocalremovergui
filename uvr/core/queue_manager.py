"""Thread-safe queue manager and task representation for batch audio processing.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from gui_data.constants import *
from uvr.core.audio_tools import AudioTools
from uvr.core.ensembler import Ensembler

logger = logging.getLogger(__name__)


class QueueTask:
    """Represents a discrete audio processing task in the batch queue."""

    def __init__(self, task_id: int, root: Any):
        self.id = task_id
        self.status = TASK_STATUS_PENDING
        self.is_paused = False

        # Snapshot UI configuration at enqueue time
        self.process_method = root.chosen_process_method_var.get()
        self.export_path = root.export_path_var.get()
        self.input_paths: tuple[str, ...] = tuple(root.inputPaths)
        self.save_format = root.save_format_var.get()
        self.mp3_bit_set = root.mp3_bit_set_var.get()
        self.wav_type_set = root.wav_type_set_var.get()
        self.is_model_sample_mode = root.model_sample_mode_var.get()
        self.is_testing_audio = root.is_testing_audio_var.get()
        self.is_add_model_name = root.is_add_model_name_var.get()
        self.is_create_model_folder = root.is_create_model_folder_var.get()
        self.ensemble_main_stem = root.ensemble_main_stem_var.get()
        self.is_secondary_stem_only = root.is_secondary_stem_only_var.get()
        self.is_primary_stem_only = root.is_primary_stem_only_var.get()
        self.is_task_complete = root.is_task_complete_var.get()
        self.chosen_ensemble = root.chosen_ensemble_var.get()

        # Audio Tools snapshot variables
        self.chosen_audio_tool = root.chosen_audio_tool_var.get()
        self.choose_algorithm = root.choose_algorithm_var.get()
        self.DualBatch_inputPaths = list(root.DualBatch_inputPaths)
        self.fileOneEntry_Full = root.fileOneEntry_Full_var.get()
        self.fileTwoEntry_Full = root.fileTwoEntry_Full_var.get()

        # Model snapshot or Audio Tool snapshot
        if self.process_method == AUDIO_TOOLS:
            self.model_data = None
            self.ensemble = None
            self.is_ensemble = False

            if self.chosen_audio_tool == TIME_STRETCH:
                self.audio_tool = AudioTools(TIME_STRETCH, root=root)
            elif self.chosen_audio_tool == CHANGE_PITCH:
                self.audio_tool = AudioTools(CHANGE_PITCH, root=root)
            elif self.chosen_audio_tool == MANUAL_ENSEMBLE:
                self.audio_tool = Ensembler(is_manual_ensemble=True, root=root)
            else:
                self.audio_tool = AudioTools(self.chosen_audio_tool, root=root)
        else:
            self.audio_tool = None
            if self.process_method == ENSEMBLE_MODE:
                self.model_data = root.assemble_model_data()
                self.ensemble = Ensembler(root=root)
                self.export_path = self.ensemble.ensemble_folder_name
                self.is_ensemble = True
            elif self.process_method == VR_ARCH_PM:
                self.model_data = root.assemble_model_data(root.vr_model_var.get(), VR_ARCH_TYPE)
                self.ensemble = None
                self.is_ensemble = False
            elif self.process_method == MDX_ARCH_TYPE:
                self.model_data = root.assemble_model_data(root.mdx_net_model_var.get(), MDX_ARCH_TYPE)
                self.ensemble = None
                self.is_ensemble = False
            elif self.process_method == DEMUCS_ARCH_TYPE:
                self.model_data = root.assemble_model_data(root.demucs_model_var.get(), DEMUCS_ARCH_TYPE)
                self.ensemble = None
                self.is_ensemble = False
            else:
                self.model_data = None
                self.ensemble = None
                self.is_ensemble = False


class QueueManager:
    """Thread-safe queue manager that synchronizes task access between the GUI

    event loop and background worker threads.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tasks: list[QueueTask] = []
        self._task_counter: int = 0

    def add_task(self, root: Any, input_paths: tuple[str, ...] | None = None) -> QueueTask:
        """Create and append a new task to the queue under thread lock."""
        with self._lock:
            self._task_counter += 1
            task = QueueTask(self._task_counter, root)
            if input_paths is not None:
                task.input_paths = input_paths
            self._tasks.append(task)
            return task

    def get_next_pending_task(self) -> QueueTask | None:
        """Retrieve the next pending, unpaused task for execution."""
        with self._lock:
            for task in self._tasks:
                if task.status == TASK_STATUS_PENDING and not task.is_paused:
                    return task
            return None

    def get_all_tasks(self) -> list[QueueTask]:
        """Return a shallow copy of all tasks in the queue."""
        with self._lock:
            return list(self._tasks)

    def remove_task(self, task_id: int) -> bool:
        """Remove a task by id if it is not currently running."""
        with self._lock:
            target = next((t for t in self._tasks if t.id == task_id), None)
            if target and target.status != TASK_STATUS_RUNNING:
                self._tasks.remove(target)
                return True
            return False

    def clear_finished_tasks(self) -> None:
        """Remove all completed and failed tasks."""
        with self._lock:
            self._tasks = [
                t
                for t in self._tasks
                if t.status in (TASK_STATUS_PENDING, TASK_STATUS_RUNNING)
            ]

    def move_task(self, current_idx: int, target_idx: int) -> bool:
        """Move a task position within the queue under lock."""
        with self._lock:
            if 0 <= current_idx < len(self._tasks) and 0 <= target_idx < len(self._tasks):
                if self._tasks[target_idx].status != TASK_STATUS_RUNNING:
                    self._tasks[current_idx], self._tasks[target_idx] = (
                        self._tasks[target_idx],
                        self._tasks[current_idx],
                    )
                    return True
            return False

    def clear_all(self) -> None:
        """Empty all non-running tasks from the queue."""
        with self._lock:
            self._tasks = [t for t in self._tasks if t.status == TASK_STATUS_RUNNING]

    def __len__(self) -> int:
        with self._lock:
            return len(self._tasks)
