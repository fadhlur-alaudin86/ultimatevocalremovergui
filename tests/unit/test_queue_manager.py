from unittest.mock import MagicMock

import pytest

from gui_data.constants import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    VR_ARCH_PM,
)
from uvr.core.queue_manager import QueueManager, QueueTask


@pytest.fixture
def mock_root():
    root = MagicMock()
    root.chosen_process_method_var.get.return_value = VR_ARCH_PM
    root.vr_model_var.get.return_value = "VR-Model-1"
    root.export_path_var.get.return_value = "/tmp/export"
    root.inputPaths = ["/tmp/input1.wav", "/tmp/input2.wav"]
    root.save_format_var.get.return_value = "WAV"
    root.mp3_bit_set_var.get.return_value = "320k"
    root.wav_type_set_var.get.return_value = "PCM_16"
    root.model_sample_mode_var.get.return_value = False
    root.is_testing_audio_var.get.return_value = False
    root.is_add_model_name_var.get.return_value = False
    root.is_create_model_folder_var.get.return_value = False
    root.ensemble_main_stem_var.get.return_value = "All Stems"
    root.is_secondary_stem_only_var.get.return_value = False
    root.is_primary_stem_only_var.get.return_value = False
    root.is_task_complete_var.get.return_value = True
    root.chosen_ensemble_var.get.return_value = "Ensemble"
    root.chosen_audio_tool_var.get.return_value = ""
    root.choose_algorithm_var.get.return_value = ""
    root.DualBatch_inputPaths = []
    root.fileOneEntry_Full_var.get.return_value = ""
    root.fileTwoEntry_Full_var.get.return_value = ""
    root.assemble_model_data.return_value = MagicMock(model_name="VR-Model-1")
    return root


def test_queue_task_initialization(mock_root):
    task = QueueTask(task_id=1, root=mock_root)
    assert task.id == 1
    assert task.status == TASK_STATUS_PENDING
    assert task.process_method == VR_ARCH_PM
    assert task.export_path == "/tmp/export"
    assert task.input_paths == ("/tmp/input1.wav", "/tmp/input2.wav")


def test_queue_manager_add_and_retrieve(mock_root):
    qm = QueueManager()
    task1 = qm.add_task(mock_root, input_paths=("/tmp/file1.wav",))
    task2 = qm.add_task(mock_root, input_paths=("/tmp/file2.wav",))

    assert task1.id == 1
    assert task2.id == 2
    assert len(qm.get_all_tasks()) == 2

    next_task = qm.get_next_pending_task()
    assert next_task.id == 1


def test_queue_manager_remove_task(mock_root):
    qm = QueueManager()
    task = qm.add_task(mock_root)
    assert qm.remove_task(task.id) is True
    assert len(qm.get_all_tasks()) == 0


def test_queue_manager_cannot_remove_running_task(mock_root):
    qm = QueueManager()
    task = qm.add_task(mock_root)
    task.status = TASK_STATUS_RUNNING
    assert qm.remove_task(task.id) is False
    assert len(qm.get_all_tasks()) == 1


def test_queue_manager_move_task(mock_root):
    qm = QueueManager()
    task1 = qm.add_task(mock_root)
    task2 = qm.add_task(mock_root)

    tasks = qm.get_all_tasks()
    assert tasks[0].id == task1.id
    assert tasks[1].id == task2.id

    assert qm.move_task(0, 1) is True
    reordered = qm.get_all_tasks()
    assert reordered[0].id == task2.id
    assert reordered[1].id == task1.id


def test_queue_manager_clear_finished(mock_root):
    qm = QueueManager()
    task1 = qm.add_task(mock_root)
    task2 = qm.add_task(mock_root)
    task1.status = TASK_STATUS_COMPLETED
    task2.status = TASK_STATUS_PENDING

    qm.clear_finished_tasks()
    remaining = qm.get_all_tasks()
    assert len(remaining) == 1
    assert remaining[0].id == task2.id
