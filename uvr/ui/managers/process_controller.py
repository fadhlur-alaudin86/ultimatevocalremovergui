"""Process controller orchestrating model separation, tool processing, and queue lifecycle."""

from __future__ import annotations

import glob
import logging
import os
import shutil
import threading
import time
from pathlib import Path
from tkinter import messagebox
from typing import Any

from kthread import KThread

from gui_data.constants import (
    ALIGN_INPUTS,
    ANY_EXT,
    AUDIO_TOOLS,
    BASS_STEM,
    CHANGE_PITCH,
    CHOOSE_MODEL,
    COMBINE_INPUTS,
    CONFIRM_WARNING,
    DEMUCS_ARCH_TYPE,
    DONE,
    DRUM_STEM,
    ENSEMBLE_MODE,
    ENSEMBLING_OUTPUTS,
    ERROR_OCCURED,
    FFMPEG_EXT,
    FOUR_STEM_ENSEMBLE,
    INST_STEM,
    INST_STEM_ONLY,
    INVALID_ENSEMBLE,
    INVALID_EXPORT,
    INVALID_INPUT,
    INVALID_MODEL,
    IS_SAVE_INST_ONLY,
    IS_SAVE_VOC_ONLY,
    LOADING_MODEL_TEXT,
    MANUAL_ENSEMBLE,
    MATCH_INPUTS,
    MDX_ARCH_TYPE,
    MISSING_MESS_TEXT,
    MODEL_MISSING_CHECK,
    MULTI_STEM_ENSEMBLE,
    NEW_LINE,
    NEW_LINES,
    NO_BASS_STEM,
    NO_DRUM_STEM,
    NO_LINE,
    NO_MODEL,
    NO_OTHER_STEM,
    NOT_ENOUGH_ERROR_TEXT,
    OTHER_STEM,
    PRIMARY_STEM,
    PROCESS_COMPLETE,
    PROCESS_COMPLETE_2,
    PROCESS_FAILED,
    PROCESS_STARTING_TEXT,
    PROCESS_STOPPED_BY_USER,
    SECONDARY_STEM,
    SIMILAR_TEXT,
    START_PROCESSING,
    STOP_PROCESS_CONFIRM,
    STORAGE_ERROR,
    STORAGE_WARNING,
    TASK_STATUS_FAILED,
    TASK_STATUS_PENDING,
    TIME_STRETCH,
    VOCAL_STEM,
    VOCAL_STEM_ONLY,
    VR_ARCH_PM,
    VR_ARCH_TYPE,
    WAIT_PROCESSING,
    WAV,
)
from gui_data.error_handling import error_dialouge, error_text
from uvr.constants import COMPLETE_CHIME, FAIL_CHIME
from uvr.core.audio_tools import AudioTools
from uvr.core.ensembler import Ensembler
from uvr.core.model_data import ModelData
from uvr.core.queue_manager import QueueTask
from uvr.models import SeperateDemucs, SeperateMDX, SeperateMDXC, SeperateVR, clear_gpu_cache
from uvr.utils.audio import play_chime
from uvr.utils.file_utils import extract_stems
from uvr.utils.notifications import send_notification

logger = logging.getLogger(__name__)


class ProcessController:
    """Manages audio separation processes, preliminary validation, progress updates, and task execution."""

    def __init__(self, root: Any) -> None:
        self.root = root

    def process_input_selections(self) -> None:
        """Grabbing all audio files from selected directories."""
        input_list = []
        ext = FFMPEG_EXT if not self.root.is_accept_any_input_var.get() else ANY_EXT

        for i in self.root.inputPaths:
            if os.path.isfile(i) and i.endswith(ext):
                input_list.append(i)
            for root_dir, _dirs, files in os.walk(i):
                for file in files:
                    if file.endswith(ext):
                        file_path = os.path.join(root_dir, file)
                        if os.path.isfile(file_path):
                            input_list.append(file_path)

        self.root.inputPaths = tuple(input_list)

    def process_check_wav_type(self) -> None:
        """Determines and sets the WAV sample type setting."""
        wav_type = self.root.wav_type_set_var.get()
        if wav_type == "32-bit Float":
            self.root.wav_type_set = "FLOAT"
        elif wav_type == "64-bit Float":
            self.root.wav_type_set = "FLOAT" if self.root.save_format_var.get() != WAV else "DOUBLE"
        else:
            self.root.wav_type_set = wav_type

    def process_preliminary_checks(self) -> bool:
        """Verifies a valid model is chosen."""
        self.process_check_wav_type()

        method = self.root.chosen_process_method_var.get()
        if method == ENSEMBLE_MODE:
            return len(self.root.ensemble_listbox_get_all_selected_models()) > 1
        if method == VR_ARCH_PM:
            return self.root.vr_model_var.get() != CHOOSE_MODEL
        if method == MDX_ARCH_TYPE:
            return self.root.mdx_net_model_var.get() != CHOOSE_MODEL
        if method == DEMUCS_ARCH_TYPE:
            return self.root.demucs_model_var.get() != CHOOSE_MODEL

        return True

    def process_storage_check(self) -> bool:
        """Verifies storage requirements."""
        total, used, free = shutil.disk_usage("/")

        space_details = (
            f"Detected Total Space: {int(total / 1.074e+9)} GB's\n"
            f"Detected Used Space: {int(used / 1.074e+9)} GB's\n"
            f"Detected Free Space: {int(free / 1.074e+9)} GB's\n"
        )

        appropriate_storage = True

        if int(free / 1.074e+9) <= 2:
            self.root.error_dialoge([STORAGE_ERROR[0], f"{STORAGE_ERROR[1]}{space_details}"])
            appropriate_storage = False

        if int(free / 1.074e+9) in [3, 4, 5, 6, 7, 8]:
            appropriate_storage = self.root.message_box(
                [STORAGE_WARNING[0], f"{STORAGE_WARNING[1]}{space_details}{CONFIRM_WARNING}"]
            )

        return appropriate_storage

    def process_initialize(self) -> None:
        """Verifies the input/output directories are valid and prepares to thread the main process."""
        chosen_method = self.root.chosen_process_method_var.get()
        chosen_tool = self.root.chosen_audio_tool_var.get()

        is_audio_tool_dual = (
            chosen_method == AUDIO_TOOLS
            and chosen_tool in [ALIGN_INPUTS, MATCH_INPUTS]
            and bool(self.root.fileOneEntry_var.get())
            and bool(self.root.fileTwoEntry_var.get())
        )
        has_valid_inputs = bool(self.root.inputPaths and os.path.isfile(self.root.inputPaths[0]))

        if not is_audio_tool_dual and not has_valid_inputs:
            self.root.error_dialoge(INVALID_INPUT)
            return

        if not os.path.isdir(self.root.export_path_var.get()):
            self.root.error_dialoge(INVALID_EXPORT)
            return

        if not self.process_storage_check():
            return

        if chosen_method != AUDIO_TOOLS and not self.process_preliminary_checks():
            error_msg = (
                INVALID_ENSEMBLE
                if chosen_method == ENSEMBLE_MODE
                else INVALID_MODEL
            )
            self.root.error_dialoge(error_msg)
            return

        with self.root.queue_lock:
            if chosen_method == AUDIO_TOOLS and chosen_tool in [ALIGN_INPUTS, MATCH_INPUTS]:
                self.root.queue_task_counter += 1
                task = QueueTask(self.root.queue_task_counter, self.root)
                self.root.processing_queue.append(task)
                self.root.command_Text.write(f"Task #{task.id} added to the processing queue.\n")
            else:
                for input_path in self.root.inputPaths:
                    self.root.queue_task_counter += 1
                    task = QueueTask(self.root.queue_task_counter, self.root)
                    task.input_paths = (input_path,)
                    self.root.processing_queue.append(task)
                    self.root.command_Text.write(f"Task #{task.id} added to the processing queue.\n")

        # Update Treeview
        self.root.update_queue_ui_display()

        # Start queue worker if not running
        if not self.root.is_queue_worker_running:
            self.root.queue_worker_thread = KThread(target=self.root.queue_worker_loop)
            self.root.queue_worker_thread.start()

    def process_button_init(self) -> None:
        """Initializes button states when a process begins."""
        self.root.auto_save()
        self.root.conversion_Button_Text_var.set(WAIT_PROCESSING)
        self.root.conversion_Button.configure(state="disabled")
        self.root.progress_text_var.set("No Active Processing")
        self.root.command_Text.clear()

    def process_button_queue_mode(self) -> None:
        """Keep button enabled so user can keep adding tasks to the queue."""
        self.root.auto_save()
        self.root.command_Text.clear()
        self.root.conversion_Button_Text_var.set(START_PROCESSING)
        self.root.progress_text_var.set("No Active Processing")
        self.root.conversion_Button.configure(state="normal")

    def process_get_baseText(self, total_files: int, file_num: int, is_dual: bool = False) -> str:
        """Create the base text for the command widget."""
        init_text = "Files" if is_dual else "File"
        return f"{init_text} {file_num}/{total_files} "

    def process_update_progress(self, total_files: int, step: float = 1.0) -> None:
        """Calculate the progress for the progress widget in the GUI."""
        while getattr(self.root, "is_process_paused", False):
            time.sleep(0.1)

        total_count = self.root.true_model_count * total_files
        base = 100 / total_count if total_count > 0 else 100
        progress = base * self.root.iteration - base
        progress += base * step

        def _update() -> None:
            self.root.progress_bar_main_var.set(progress)
            self.root.progress_text_var.set(f"Process Progress: {int(progress)}%")

        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)

    def show_stop_menu(self) -> None:
        """Displays the popup stop queue menu."""
        x = self.root.stop_expand_Button.winfo_rootx()
        y = self.root.stop_expand_Button.winfo_rooty() + self.root.stop_expand_Button.winfo_height()
        try:
            self.root.stop_menu.tk_popup(x, y)
        finally:
            self.root.stop_menu.grab_release()

    def confirm_stop_process(self, stop_all: bool = False) -> None:
        """Asks for confirmation before halting active process."""
        self.root.auto_save()

        if self.root.active_processing_thread and self.root.active_processing_thread.is_alive():
            confirm = messagebox.askyesno(
                parent=self.root,
                title=STOP_PROCESS_CONFIRM[0],
                message=STOP_PROCESS_CONFIRM[1],
            )

            if confirm:
                if stop_all:
                    for task in self.root.processing_queue:
                        if task.status == TASK_STATUS_PENDING:
                            task.status = TASK_STATUS_FAILED
                    self.root.update_queue_ui_display()
                try:
                    self.root.active_processing_thread.terminate()
                finally:
                    self.root.is_process_stopped = True
                    self.root.command_Text.write(PROCESS_STOPPED_BY_USER)
        else:
            if stop_all:
                for task in self.root.processing_queue:
                    if task.status == TASK_STATUS_PENDING:
                        task.status = TASK_STATUS_FAILED
                self.root.update_queue_ui_display()
            self.root.clear_cache_torch = True

    def process_end(self, error: Any = None) -> None:
        """End of process actions."""
        self.root.auto_save()
        self.root.cached_sources_clear()
        self.root.clear_cache_torch = True
        self.root.conversion_Button_Text_var.set(START_PROCESSING)
        self.root.conversion_Button.configure(state="normal")
        self.root.progress_bar_main_var.set(0)

        if not error and not getattr(self.root, "is_process_stopped", False):
            try:
                send_notification("Ultimate Vocal Remover", "Audio processing completed successfully!")
            except Exception:
                pass

        if error:
            error_message_box_text = f"{error_dialouge(error)}{ERROR_OCCURED[1]}"

            def show_error() -> None:
                confirm = messagebox.askyesno(
                    parent=self.root,
                    title=ERROR_OCCURED[0],
                    message=error_message_box_text,
                )
                if confirm:
                    self.root.is_confirm_error_var.set(True)
                    self.root.clear_cache_torch = True

            self.root.after(0, show_error)
            self.root.clear_cache_torch = True

            if MODEL_MISSING_CHECK in error_message_box_text:
                self.root.update_checkbox_text()

    def process_determine_secondary_model(
        self,
        process_method: str,
        main_model_primary_stem: str,
        is_primary_stem_only: bool = False,
        is_secondary_stem_only: bool = False,
    ) -> tuple[Any, float | None]:
        """Obtains the correct secondary model data for conversion."""
        secondary_model_scale = None
        secondary_model = None

        if process_method == VR_ARCH_TYPE:
            secondary_model_vars = self.root.vr_secondary_model_vars
        elif process_method == MDX_ARCH_TYPE:
            secondary_model_vars = self.root.mdx_secondary_model_vars
        elif process_method == DEMUCS_ARCH_TYPE:
            secondary_model_vars = self.root.demucs_secondary_model_vars
        else:
            secondary_model_vars = {}

        if main_model_primary_stem in [VOCAL_STEM, INST_STEM]:
            secondary_model = secondary_model_vars.get("voc_inst_secondary_model")
            scale_var = secondary_model_vars.get("voc_inst_secondary_model_scale")
            secondary_model_scale = scale_var.get() if scale_var else None
        if main_model_primary_stem in [OTHER_STEM, NO_OTHER_STEM]:
            secondary_model = secondary_model_vars.get("other_secondary_model")
            scale_var = secondary_model_vars.get("other_secondary_model_scale")
            secondary_model_scale = scale_var.get() if scale_var else None
        if main_model_primary_stem in [DRUM_STEM, NO_DRUM_STEM]:
            secondary_model = secondary_model_vars.get("drums_secondary_model")
            scale_var = secondary_model_vars.get("drums_secondary_model_scale")
            secondary_model_scale = scale_var.get() if scale_var else None
        if main_model_primary_stem in [BASS_STEM, NO_BASS_STEM]:
            secondary_model = secondary_model_vars.get("bass_secondary_model")
            scale_var = secondary_model_vars.get("bass_secondary_model_scale")
            secondary_model_scale = scale_var.get() if scale_var else None

        if secondary_model_scale:
            secondary_model_scale = float(secondary_model_scale)

        if secondary_model and secondary_model.get() != NO_MODEL:
            res_model = ModelData(
                secondary_model.get(),
                is_secondary_model=True,
                primary_model_primary_stem=main_model_primary_stem,
                is_primary_model_primary_stem_only=is_primary_stem_only,
                is_primary_model_secondary_stem_only=is_secondary_stem_only,
                root=self.root,
            )
            if not res_model.model_status:
                res_model = None
        else:
            res_model = None

        return res_model, secondary_model_scale

    def process_determine_demucs_pre_proc_model(self, primary_stem: str | None = None) -> Any:
        """Obtains the correct pre-process secondary model data for conversion."""
        if (
            self.root.demucs_pre_proc_model_var.get() != NO_MODEL
            and self.root.is_demucs_pre_proc_model_activate_var.get()
        ):
            pre_proc_model = ModelData(
                self.root.demucs_pre_proc_model_var.get(),
                primary_model_primary_stem=primary_stem,
                is_pre_proc_model=True,
                root=self.root,
            )
            if pre_proc_model.model_status:
                return pre_proc_model
        return None

    def process_determine_vocal_split_model(self) -> Any:
        """Obtains the correct vocal splitter secondary model data for conversion."""
        if (
            self.root.set_vocal_splitter_var.get() != NO_MODEL
            and self.root.is_set_vocal_splitter_var.get()
        ):
            vocal_splitter_model = ModelData(
                self.root.set_vocal_splitter_var.get(),
                is_vocal_split_model=True,
                root=self.root,
            )
            if vocal_splitter_model.model_status:
                return vocal_splitter_model
        return None

    def check_only_selection_stem(self, checktype: str) -> bool:
        """Checks if only a specific stem should be processed/saved."""
        chosen_method = self.root.chosen_process_method_var.get()
        is_demucs = chosen_method == DEMUCS_ARCH_TYPE

        stem_primary_label = (
            self.root.is_primary_stem_only_Demucs_Text_var.get()
            if is_demucs
            else self.root.is_primary_stem_only_Text_var.get()
        )
        stem_primary_bool = (
            self.root.is_primary_stem_only_Demucs_var.get()
            if is_demucs
            else self.root.is_primary_stem_only_var.get()
        )
        stem_secondary_label = (
            self.root.is_secondary_stem_only_Demucs_Text_var.get()
            if is_demucs
            else self.root.is_secondary_stem_only_Text_var.get()
        )
        stem_secondary_bool = (
            self.root.is_secondary_stem_only_Demucs_var.get()
            if is_demucs
            else self.root.is_secondary_stem_only_var.get()
        )

        if checktype == VOCAL_STEM_ONLY:
            return not (
                (VOCAL_STEM_ONLY != stem_primary_label and stem_primary_bool)
                or (VOCAL_STEM_ONLY not in stem_secondary_label and stem_secondary_bool)
            )
        elif checktype == INST_STEM_ONLY:
            return (
                (
                    INST_STEM_ONLY == stem_primary_label
                    and stem_primary_bool
                    and self.root.is_save_inst_set_vocal_splitter_var.get()
                    and self.root.set_vocal_splitter_var.get() != NO_MODEL
                )
                or (
                    INST_STEM_ONLY == stem_secondary_label
                    and stem_secondary_bool
                    and self.root.is_save_inst_set_vocal_splitter_var.get()
                    and self.root.set_vocal_splitter_var.get() != NO_MODEL
                )
            )
        elif checktype == IS_SAVE_VOC_ONLY:
            return (
                (VOCAL_STEM_ONLY == stem_primary_label and stem_primary_bool)
                or (VOCAL_STEM_ONLY == stem_secondary_label and stem_secondary_bool)
            )
        elif checktype == IS_SAVE_INST_ONLY:
            return (
                (INST_STEM_ONLY == stem_primary_label and stem_primary_bool)
                or (INST_STEM_ONLY == stem_secondary_label and stem_secondary_bool)
            )
        return False

    def determine_voc_split(self, models: list[Any]) -> int:
        """Determines if vocal split preprocessing is needed."""
        is_vocal_active = self.check_only_selection_stem(
            VOCAL_STEM_ONLY
        ) or self.check_only_selection_stem(INST_STEM_ONLY)

        if (
            self.root.set_vocal_splitter_var.get() != NO_MODEL
            and self.root.is_set_vocal_splitter_var.get()
            and is_vocal_active
        ):
            model_stems_list = self.root.model_list(
                VOCAL_STEM, INST_STEM, is_dry_check=True, is_check_vocal_split=True
            )
            if any(model.model_basename in model_stems_list for model in models):
                return 1

        return 0

    def process_tool_start(self, task: Any = None) -> None:
        """Start conversion/processing for Audio Tools utilities."""
        stime = time.perf_counter()

        def time_elapsed() -> str:
            return f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}'

        def get_audio_file_base(audio_file: Any) -> str:
            if audio_tool.audio_tool in [MANUAL_ENSEMBLE, ALIGN_INPUTS, MATCH_INPUTS]:
                target = inputPaths[0] if audio_tool.audio_tool == MANUAL_ENSEMBLE else audio_file[0]
                return f"{os.path.splitext(os.path.basename(target))[0]}"
            return f"{os.path.splitext(os.path.basename(audio_file))[0]}"

        def handle_ensemble(paths: tuple[Any, ...], audio_file_base: str) -> None:
            self.root.progress_bar_main_var.set(50)
            choose_algorithm = task.choose_algorithm if task else self.root.choose_algorithm_var.get()
            if choose_algorithm == COMBINE_INPUTS:
                audio_tool.combine_audio(paths, audio_file_base)
            else:
                audio_tool.ensemble_manual(paths, audio_file_base)
            self.root.progress_bar_main_var.set(100)
            self.root.command_Text.write(DONE)

        def handle_alignment_match(
            audio_file: Any, audio_file_base: str, cmd_text: Any, set_prog_bar: Any
        ) -> None:
            audio_file_2_base = f"{os.path.splitext(os.path.basename(audio_file[1]))[0]}"
            if audio_tool.audio_tool == MATCH_INPUTS:
                audio_tool.match_inputs(audio_file, audio_file_base, cmd_text)
            else:
                cmd_text(f"{PROCESS_STARTING_TEXT}\n")
                audio_tool.align_inputs(
                    audio_file, audio_file_base, audio_file_2_base, cmd_text, set_prog_bar
                )
            self.root.progress_bar_main_var.set(base * file_num)
            self.root.command_Text.write(f"{DONE}\n")

        def handle_pitch_time_shift(audio_file: Any, audio_file_base: str) -> None:
            audio_tool.pitch_or_time_shift(audio_file, audio_file_base)
            self.root.progress_bar_main_var.set(base * file_num)
            self.root.command_Text.write(DONE)

        multiple_files = False
        if not task:
            self.process_button_init()
        inputPaths = task.input_paths if task else self.root.inputPaths
        is_verified_audio = True
        is_dual = False
        is_model_sample_mode = task.model_sample_mode if task else self.root.model_sample_mode_var.get()
        is_task_complete = task.is_task_complete if task else self.root.is_task_complete_var.get()
        self.root.iteration = 0
        self.root.true_model_count = 1
        self.process_check_wav_type()
        process_complete_text = PROCESS_COMPLETE

        chosen_audio_tool = task.chosen_audio_tool if task else self.root.chosen_audio_tool_var.get()
        if chosen_audio_tool in [ALIGN_INPUTS, MATCH_INPUTS]:
            DualBatch_inputPaths = task.DualBatch_inputPaths if task else self.root.DualBatch_inputPaths
            fileOneEntry_Full = task.fileOneEntry_Full if task else self.root.fileOneEntry_Full_var.get()
            fileTwoEntry_Full = task.fileTwoEntry_Full if task else self.root.fileTwoEntry_Full_var.get()
            if DualBatch_inputPaths:
                inputPaths = tuple(DualBatch_inputPaths)
            else:
                if not fileOneEntry_Full or not fileTwoEntry_Full:
                    self.root.command_Text.write(NOT_ENOUGH_ERROR_TEXT)
                    if not task:
                        self.process_end()
                    else:
                        raise RuntimeError("Not enough files selected.")
                    return
                inputPaths = [(fileOneEntry_Full, fileTwoEntry_Full)]

        try:
            total_files = len(inputPaths)
            if task:
                audio_tool = task.audio_tool
                if chosen_audio_tool in [TIME_STRETCH, CHANGE_PITCH, ALIGN_INPUTS, MATCH_INPUTS]:
                    self.root.progress_bar_main_var.set(2)
                    if chosen_audio_tool in [ALIGN_INPUTS, MATCH_INPUTS]:
                        is_dual = True
                elif chosen_audio_tool == MANUAL_ENSEMBLE:
                    multiple_files = True
                    if total_files <= 1:
                        self.root.command_Text.write(NOT_ENOUGH_ERROR_TEXT)
                        raise RuntimeError("Not enough files selected.")
            else:
                if self.root.chosen_audio_tool_var.get() == TIME_STRETCH:
                    audio_tool = AudioTools(TIME_STRETCH, root=self.root)
                    self.root.progress_bar_main_var.set(2)
                elif self.root.chosen_audio_tool_var.get() == CHANGE_PITCH:
                    audio_tool = AudioTools(CHANGE_PITCH, root=self.root)
                    self.root.progress_bar_main_var.set(2)
                elif self.root.chosen_audio_tool_var.get() == MANUAL_ENSEMBLE:
                    audio_tool = Ensembler(is_manual_ensemble=True, root=self.root)
                    multiple_files = True
                    if total_files <= 1:
                        self.root.command_Text.write(NOT_ENOUGH_ERROR_TEXT)
                        self.process_end()
                        return
                elif self.root.chosen_audio_tool_var.get() in [ALIGN_INPUTS, MATCH_INPUTS]:
                    audio_tool = AudioTools(self.root.chosen_audio_tool_var.get(), root=self.root)
                    self.root.progress_bar_main_var.set(2)
                    is_dual = True

            error_text_console = ""
            for file_num, audio_file in enumerate(inputPaths, start=1):
                self.root.iteration += 1
                base = 100 / total_files
                audio_file_base = get_audio_file_base(audio_file)
                self.root.base_text = self.process_get_baseText(
                    total_files=total_files,
                    file_num=total_files if multiple_files else file_num,
                    is_dual=is_dual,
                )
                command_Text = lambda text: self.root.command_Text.write(self.root.base_text + text)
                set_progress_bar = (
                    lambda step, inference_iterations=0: self.process_update_progress(
                        total_files=total_files, step=(step + inference_iterations)
                    )
                )

                if not self.root.verify_audio(audio_file):
                    error_text_console = (
                        f'{self.root.base_text}"{os.path.basename(audio_file)}" {MISSING_MESS_TEXT}\n'
                    )
                    if total_files >= 2:
                        self.root.command_Text.write(f"\n{error_text_console}")
                    is_verified_audio = False
                    continue

                audio_tool_action = audio_tool.audio_tool
                if audio_tool_action not in [MANUAL_ENSEMBLE, ALIGN_INPUTS, MATCH_INPUTS]:
                    audio_file = (
                        self.root.create_sample(audio_file)
                        if is_model_sample_mode
                        else audio_file
                    )
                    self.root.command_Text.write(
                        f'{NEW_LINE if file_num != 1 else NO_LINE}{self.root.base_text}"{os.path.basename(audio_file)}".{NEW_LINES}'
                    )
                elif audio_tool_action in [ALIGN_INPUTS, MATCH_INPUTS]:
                    text_write = (
                        ("File 1", "File 2")
                        if audio_tool_action == ALIGN_INPUTS
                        else ("Target", "Reference")
                    )
                    if audio_file[0] != audio_file[1]:
                        self.root.command_Text.write(
                            f'{self.root.base_text}{text_write[0]}:  "{os.path.basename(audio_file[0])}"{NEW_LINE}'
                        )
                        self.root.command_Text.write(
                            f'{self.root.base_text}{text_write[1]}:  "{os.path.basename(audio_file[1])}"{NEW_LINES}'
                        )
                    else:
                        self.root.command_Text.write(
                            f"{self.root.base_text}{text_write[0]} & {text_write[1]} {SIMILAR_TEXT}{NEW_LINES}"
                        )
                        continue
                elif audio_tool_action == MANUAL_ENSEMBLE:
                    for n, i in enumerate(inputPaths):
                        self.root.command_Text.write(f'File {n + 1} "{os.path.basename(i)}"{NEW_LINE}')
                    self.root.command_Text.write(NEW_LINE)

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
                self.root.command_Text.write(f"{error_text_console}\n{PROCESS_FAILED}")
                self.root.command_Text.write(time_elapsed())
                if is_task_complete:
                    play_chime(FAIL_CHIME)
                if task:
                    raise RuntimeError("Verification failed.")
            else:
                self.root.command_Text.write(f"{process_complete_text}{time_elapsed()}")
                if is_task_complete:
                    play_chime(COMPLETE_CHIME)

            if not task:
                self.process_end()

        except Exception as e:
            self.root.error_log_var.set(error_text(chosen_audio_tool, e))
            self.root.command_Text.write(f"\n\n{PROCESS_FAILED}")
            self.root.command_Text.write(time_elapsed())
            if is_task_complete:
                play_chime(FAIL_CHIME)
            if not task:
                self.process_end(error=e)
            else:
                task.status = TASK_STATUS_FAILED
                raise e

    def process_start(self, task: Any = None) -> None:
        """Start the audio separation process for model inference."""
        stime = time.perf_counter()
        time_elapsed = lambda: f'Time Elapsed: {time.strftime("%H:%M:%S", time.gmtime(int(time.perf_counter() - stime)))}'
        export_path = task.export_path if task else self.root.export_path_var.get()
        is_ensemble = task.is_ensemble if task else False
        self.root.true_model_count = 0
        self.root.iteration = 0
        is_verified_audio = True
        if not task:
            self.process_button_init()
        inputPaths = task.input_paths if task else self.root.inputPaths
        inputPath_total_len = len(inputPaths)
        is_model_sample_mode = (
            task.is_model_sample_mode
            if task
            else self.root.model_sample_mode_var.get()
        )

        try:
            if task:
                model = task.model_data
                ensemble = task.ensemble
            else:
                method = self.root.chosen_process_method_var.get()
                if method == ENSEMBLE_MODE:
                    model, ensemble = self.root.assemble_model_data(), Ensembler(root=self.root)
                    export_path, is_ensemble = ensemble.ensemble_folder_name, True
                elif method == VR_ARCH_PM:
                    model = self.root.assemble_model_data(self.root.vr_model_var.get(), VR_ARCH_TYPE)
                elif method == MDX_ARCH_TYPE:
                    model = self.root.assemble_model_data(self.root.mdx_net_model_var.get(), MDX_ARCH_TYPE)
                elif method == DEMUCS_ARCH_TYPE:
                    model = self.root.assemble_model_data(self.root.demucs_model_var.get(), DEMUCS_ARCH_TYPE)
                else:
                    model = []

            self.root.cached_source_model_list_check(model)

            true_model_4_stem_count = sum(
                m.demucs_4_stem_added_count if m.process_method == DEMUCS_ARCH_TYPE else 0
                for m in model
            )
            true_model_pre_proc_model_count = sum(2 if m.pre_proc_model_activated else 0 for m in model)
            self.root.true_model_count = (
                sum(2 if m.is_secondary_model_activated else 1 for m in model)
                + true_model_4_stem_count
                + true_model_pre_proc_model_count
                + self.determine_voc_split(model)
            )

            error_text_console = ""
            for file_num, audio_file in enumerate(inputPaths, start=1):
                self.root.cached_sources_clear()
                base_text = self.process_get_baseText(total_files=inputPath_total_len, file_num=file_num)
                self.root.file_progress_var.set(
                    f"File {file_num}/{inputPath_total_len}: {os.path.basename(audio_file)}"
                )

                if self.root.verify_audio(audio_file):
                    original_audio_file = audio_file
                    audio_file = (
                        self.root.create_sample(audio_file)
                        if is_model_sample_mode
                        else audio_file
                    )
                    self.root.command_Text.write(
                        f'{NEW_LINE if file_num != 1 else NO_LINE}{base_text}"{os.path.basename(audio_file)}".{NEW_LINES}'
                    )
                    is_verified_audio = True
                else:
                    error_text_console = (
                        f'{base_text}"{os.path.basename(audio_file)}" {MISSING_MESS_TEXT}\n'
                    )
                    if inputPath_total_len >= 2:
                        self.root.command_Text.write(f"\n{error_text_console}")
                    self.root.iteration += self.root.true_model_count
                    is_verified_audio = False
                    continue

                for current_model_num, current_model in enumerate(model, start=1):
                    self.root.iteration += 1

                    if is_ensemble:
                        self.root.command_Text.write(
                            f"Ensemble Mode - {current_model.model_basename} - Model {current_model_num}/{len(model)}{NEW_LINES}"
                        )

                    model_name_text = f"({current_model.model_basename})" if not is_ensemble else ""
                    config_details = ""
                    if current_model.process_method == MDX_ARCH_TYPE:
                        overlap_val = (
                            current_model.overlap_mdx
                            if not current_model.is_mdx_c
                            else current_model.overlap_mdx23
                        )
                        config_details = f" [Seg: {current_model.mdx_segment_size} | Over: {overlap_val} | TTA: {'Y' if current_model.is_tta else 'N'}]"
                    elif current_model.process_method == VR_ARCH_TYPE:
                        config_details = f" [Win: {current_model.window_size} | Agg: {current_model.aggression_setting} | TTA: {'Y' if current_model.is_tta else 'N'}]"
                    elif current_model.process_method == DEMUCS_ARCH_TYPE:
                        config_details = f" [Seg: {current_model.segment} | Shift: {current_model.shifts}]"

                    self.root.command_Text.write(
                        base_text + f"{LOADING_MODEL_TEXT} {model_name_text}{config_details}..."
                    )

                    set_progress_bar = (
                        lambda step, inference_iterations=0: self.process_update_progress(
                            total_files=inputPath_total_len, step=(step + inference_iterations)
                        )
                    )
                    write_to_console = lambda progress_text, b_text=base_text: self.root.command_Text.write(
                        b_text + progress_text
                    )

                    current_export_path = export_path
                    if (task.is_create_model_folder if task else self.root.is_create_model_folder_var.get()) and not is_ensemble:
                        current_export_path = os.path.join(
                            Path(task.export_path if task else self.root.export_path_var.get()),
                            current_model.model_basename,
                            os.path.splitext(os.path.basename(audio_file))[0],
                        )
                        if not os.path.isdir(current_export_path):
                            os.makedirs(current_export_path)

                    base_name_original = os.path.splitext(os.path.basename(audio_file))[0]
                    audio_file_base = base_name_original
                    counter = 1

                    while True:
                        temp_base = audio_file_base
                        if (task.is_testing_audio if task else self.root.is_testing_audio_var.get()) and not is_ensemble:
                            temp_base = f"{round(time.time())}_{temp_base}"
                        if is_ensemble:
                            temp_base = f"{temp_base}_{current_model.model_basename}"
                        elif task.is_add_model_name if task else self.root.is_add_model_name_var.get():
                            temp_base = f"{temp_base}_{current_model.model_basename}"

                        existing = glob.glob(os.path.join(current_export_path, f"{temp_base}*"))
                        if not existing:
                            audio_file_base = temp_base
                            break

                        audio_file_base = f"{base_name_original}_{counter}"
                        counter += 1

                    process_data = {
                        "model_data": current_model,
                        "export_path": current_export_path,
                        "audio_file_base": audio_file_base,
                        "audio_file": audio_file,
                        "set_progress_bar": set_progress_bar,
                        "write_to_console": write_to_console,
                        "process_iteration": self.root.process_iteration,
                        "cached_source_callback": self.root.cached_source_callback,
                        "cached_model_source_holder": self.root.cached_model_source_holder,
                        "list_all_models": self.root.all_models,
                        "is_ensemble_master": is_ensemble,
                        "is_half_precision": (
                            getattr(task, "is_half_precision", self.root.is_half_precision_var.get())
                            if task
                            else self.root.is_half_precision_var.get()
                        ),
                        "is_4_stem_ensemble": (
                            (task.ensemble_main_stem if task else self.root.ensemble_main_stem_var.get())
                            in [FOUR_STEM_ENSEMBLE, MULTI_STEM_ENSEMBLE]
                            and is_ensemble
                        ),
                        "original_audio_file": original_audio_file,
                    }

                    if current_model.process_method == VR_ARCH_TYPE:
                        seperator = SeperateVR(current_model, process_data)
                    elif current_model.process_method == MDX_ARCH_TYPE:
                        seperator = (
                            SeperateMDXC(current_model, process_data)
                            if current_model.is_mdx_c
                            else SeperateMDX(current_model, process_data)
                        )
                    elif current_model.process_method == DEMUCS_ARCH_TYPE:
                        seperator = SeperateDemucs(current_model, process_data)
                    else:
                        seperator = None

                    if seperator:
                        seperator.seperate()

                    if is_ensemble:
                        self.root.command_Text.write("\n")

                if is_ensemble:
                    audio_file_base = audio_file_base.replace(f"_{current_model.model_basename}", "")
                    self.root.command_Text.write(base_text + ENSEMBLING_OUTPUTS)

                    ensemble_stem = (
                        task.ensemble_main_stem
                        if task
                        else self.root.ensemble_main_stem_var.get()
                    )
                    if ensemble_stem in [FOUR_STEM_ENSEMBLE, MULTI_STEM_ENSEMBLE]:
                        stem_list = extract_stems(audio_file_base, export_path)
                        for output_stem in stem_list:
                            ensemble.ensemble_outputs(
                                audio_file_base, export_path, output_stem, is_4_stem=True
                            )
                    else:
                        if not (
                            task.is_secondary_stem_only
                            if task
                            else self.root.is_secondary_stem_only_var.get()
                        ):
                            ensemble.ensemble_outputs(audio_file_base, export_path, PRIMARY_STEM)
                        if not (
                            task.is_primary_stem_only
                            if task
                            else self.root.is_primary_stem_only_var.get()
                        ):
                            ensemble.ensemble_outputs(audio_file_base, export_path, SECONDARY_STEM)
                            ensemble.ensemble_outputs(
                                audio_file_base, export_path, SECONDARY_STEM, is_inst_mix=True
                            )

                    self.root.command_Text.write(DONE)

                if is_model_sample_mode and os.path.isfile(audio_file):
                    os.remove(audio_file)

                clear_gpu_cache()

            if is_ensemble and os.path.isdir(export_path) and len(os.listdir(export_path)) == 0:
                shutil.rmtree(export_path)

            task_complete_check = (
                task.is_task_complete if task else self.root.is_task_complete_var.get()
            )
            if inputPath_total_len == 1 and not is_verified_audio:
                self.root.command_Text.write(f"{error_text_console}\n{PROCESS_FAILED}")
                self.root.command_Text.write(time_elapsed())
                if task_complete_check:
                    play_chime(FAIL_CHIME)
            else:
                set_progress_bar(1.0)
                self.root.command_Text.write(PROCESS_COMPLETE)
                self.root.command_Text.write(time_elapsed())
                if task_complete_check:
                    play_chime(COMPLETE_CHIME)

            if not task:
                self.process_end()

        except Exception as e:
            current_method = task.process_method if task else self.root.chosen_process_method_var.get()
            self.root.error_log_var.set(f"{error_text(current_method, e)}{self.root.get_settings_list()}")
            self.root.command_Text.write(f"\n\n{PROCESS_FAILED}")
            self.root.command_Text.write(time_elapsed())
            if task.is_task_complete if task else self.root.is_task_complete_var.get():
                play_chime(FAIL_CHIME)
            if not task:
                self.process_end(error=e)
            else:
                task.status = TASK_STATUS_FAILED
                raise e
