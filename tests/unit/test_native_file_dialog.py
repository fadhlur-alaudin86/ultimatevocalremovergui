from uvr.utils.native_file_dialog import (
    get_native_dialog_backend,
    is_kde,
)


def test_dialog_backend_detection():
    backend = get_native_dialog_backend()
    assert backend in {"kdialog", "zenity", "tk"}


def test_kde_detection():
    kde_status = is_kde()
    assert isinstance(kde_status, bool)
