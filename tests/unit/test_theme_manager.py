from uvr.ui.theme_manager import ThemeManager


def test_theme_manager_modes():
    ThemeManager.set_mode("dark")
    assert ThemeManager.get_mode() == "dark"
    assert ThemeManager.is_dark() is True

    ThemeManager.set_mode("light")
    assert ThemeManager.get_mode() == "light"
    assert ThemeManager.is_dark() is False

    # Test toggle
    new_mode = ThemeManager.toggle_mode()
    assert new_mode == "dark"
    assert ThemeManager.is_dark() is True

    new_mode = ThemeManager.toggle_mode()
    assert new_mode == "light"
    assert ThemeManager.is_dark() is False


def test_theme_manager_invalid_mode_defaults_to_dark():
    ThemeManager.set_mode("invalid_mode")
    assert ThemeManager.get_mode() == "dark"
    assert ThemeManager.is_dark() is True
