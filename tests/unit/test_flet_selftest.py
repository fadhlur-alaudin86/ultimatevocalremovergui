"""Tests for the Flet scaffold headless selftest."""

from flet_gui.app import build_all
from flet_gui.pages.separate import build_job_specs, fields_for_method, half_gate
from gui_data.constants import DEMUCS_ARCH_TYPE, VR_ARCH_PM


def test_selftest_builds_all_views():
    views = build_all(headless=True)
    assert set(views) == {"separate", "queue", "log", "settings"}


def test_form_fields_match_capabilities():
    fields = fields_for_method(DEMUCS_ARCH_TYPE)
    assert "shifts" in fields and "aggression_setting" not in fields
    assert "aggression_setting" in fields_for_method(VR_ARCH_PM)


def test_submit_emits_frozen_jobspec():
    specs = build_job_specs(
        method=DEMUCS_ARCH_TYPE,
        model_id="htdemucs",
        input_paths=["/tmp/a.wav", "/tmp/b.wav"],
        export_path="/tmp/out",
        options={"is_half_precision": True, "device_set": "Default"},
    )
    assert len(specs) == 1
    spec = specs[0]
    assert spec.input_paths == ("/tmp/a.wav", "/tmp/b.wav")
    assert spec.process_method == DEMUCS_ARCH_TYPE
    assert spec.is_half_precision is True


def test_half_gate_disables_on_cpu_with_reason():
    allowed, reason = half_gate(want_gpu=False, device_set="Default")
    assert allowed is False and reason
    allowed, _ = half_gate(want_gpu=True, device_set="Default")
    assert isinstance(allowed, bool)
