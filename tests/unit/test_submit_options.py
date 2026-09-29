"""Tests for submit option collection (store + form merge)."""

from flet_gui.pages.separate import collect_submit_options


def test_collect_merges_store_and_form_state():
    store_data = {"aggression_setting": "7", "wav_type_set": "FLOAT", "bogus": 1}
    form_state = {"is_gpu_conversion": True, "is_half_precision": False, "device_set": "Default"}
    options = collect_submit_options(store_data, form_state)
    assert options["aggression_setting"] == "7"
    assert options["wav_type_set"] == "FLOAT"
    assert options["is_gpu_conversion"] is True
    assert "bogus" not in options
