from uvr.ui.dialogs.base_dialog import BaseDialog, CTkBaseDialog


def test_base_dialog_classes():
    assert issubclass(BaseDialog, CTkBaseDialog)
