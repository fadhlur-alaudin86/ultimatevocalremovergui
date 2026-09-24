from unittest.mock import MagicMock

import pytest

from uvr.ui.managers.right_click_handler import RightClickMenuHandler


@pytest.fixture
def mock_root():
    root = MagicMock()
    root.current_text_box = MagicMock()
    root.last_found_settings = ("setting_a", "setting_b")
    root.chosen_process_method_var = MagicMock()
    root.chosen_process_method_var.get.return_value = "MDX-Net"
    root.help_hints_var = MagicMock()
    root.help_hints_var.get.return_value = True
    root.error_log_var = MagicMock()
    root.error_log_var.get.return_value = False
    root.is_menu_settings_open = False
    return root


def test_right_click_handler_init(mock_root):
    handler = RightClickMenuHandler(mock_root)
    assert handler.root is mock_root


def test_right_click_menu_copy(mock_root):
    mock_root.current_text_box.selection_get.return_value = "Selected text"
    handler = RightClickMenuHandler(mock_root)

    handler.right_click_menu_copy()

    mock_root.current_text_box.selection_get.assert_called_once()
    mock_root.clipboard_clear.assert_called_once()
    mock_root.clipboard_append.assert_called_once_with("Selected text")


def test_right_click_menu_paste_entry(mock_root):
    mock_root.clipboard_get.return_value = "Pasted text"
    mock_root.current_text_box.index.return_value = 0
    handler = RightClickMenuHandler(mock_root)

    handler.right_click_menu_paste(text_box=False)

    mock_root.current_text_box.delete.assert_called_once_with(0, "end")
    mock_root.current_text_box.insert.assert_called_once_with(0, "Pasted text")


def test_right_click_menu_delete_entry(mock_root):
    handler = RightClickMenuHandler(mock_root)

    handler.right_click_menu_delete(text_box=False)

    mock_root.current_text_box.delete.assert_called_once_with(0, "end")
