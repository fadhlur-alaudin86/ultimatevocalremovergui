import json

from uvr.core.settings import load_settings, save_settings


def test_load_settings_loads_valid_json(tmp_path):
    json_file = tmp_path / "data.json"
    dummy_data = {"test_key": "test_val", "version": 5}
    json_file.write_text(json.dumps(dummy_data))

    loaded = load_settings(file_path=str(json_file))
    assert loaded["test_key"] == "test_val"
    assert loaded["version"] == 5


def test_save_settings_writes_formatted_json(tmp_path):
    json_file = tmp_path / "data.json"
    test_dict = {"export_path": "/tmp/exports", "is_gpu": True}

    save_settings(test_dict, file_path=str(json_file))

    assert json_file.exists()
    content = json.loads(json_file.read_text())
    assert content["export_path"] == "/tmp/exports"
    assert content["is_gpu"] is True


def test_load_settings_fallback_to_defaults(tmp_path):
    missing_json = tmp_path / "non_existent.json"

    loaded = load_settings(file_path=str(missing_json))
    assert isinstance(loaded, dict)
    assert len(loaded) > 0
    assert "export_path" in loaded
