from uvr.core.presets import PresetManager


def test_preset_manager_lifecycle(tmp_path):
    preset_dir = tmp_path / "presets"
    manager = PresetManager(str(preset_dir))

    # Built-in presets should be initialized
    presets = manager.list_presets()
    assert len(presets) >= 3
    assert "Default Vocal Extraction" in presets

    # Test saving custom preset
    custom_cfg = {"model": "UVR-MDX-Net", "format": "WAV"}
    assert manager.save_preset("My Custom Preset", custom_cfg) is True
    assert "My Custom Preset" in manager.list_presets()

    # Test loading custom preset
    loaded = manager.load_preset("My Custom Preset")
    assert loaded["model"] == "UVR-MDX-Net"
    assert loaded["format"] == "WAV"

    # Test deletion
    assert manager.delete_preset("My Custom Preset") is True
    assert "My Custom Preset" not in manager.list_presets()
