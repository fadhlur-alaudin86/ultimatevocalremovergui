"""Tests for CapabilityRegistry and the settings v2 migrator."""

from gui_data.constants import (
    AUDIO_TOOLS,
    DEMUCS_ARCH_TYPE,
    ENSEMBLE_MODE,
    MDX_ARCH_TYPE,
    VR_ARCH_PM,
)
from uvr.core.capability_registry import (
    CAPABILITIES,
    SETTINGS_VERSION,
    SHARED_OPTIONS,
    migrate_legacy,
)


def test_all_methods_present():
    assert set(CAPABILITIES) == {VR_ARCH_PM, MDX_ARCH_TYPE, DEMUCS_ARCH_TYPE, ENSEMBLE_MODE, AUDIO_TOOLS}


def test_vr_has_no_demucs_options():
    assert "shifts" not in CAPABILITIES[VR_ARCH_PM]
    assert "aggression_setting" in CAPABILITIES[VR_ARCH_PM]


def test_single_stem_only_option_for_all_methods():
    for method, options in CAPABILITIES.items():
        assert "is_primary_stem_only_Demucs" not in options, method
        assert "is_secondary_stem_only_Demucs" not in options, method


def test_migrate_drops_unknown_and_reports():
    out, unknown = migrate_legacy({"vr_model": "x", "bogus_key": 1})
    assert out == {"vr_model": "x"} and unknown == ["bogus_key"]


def test_migrate_folds_demucs_stem_pair_into_shared():
    out, _ = migrate_legacy({"is_primary_stem_only_Demucs": True})
    assert out.get("is_primary_stem_only") is True
    assert "is_primary_stem_only_Demucs" not in out


def test_settings_version_is_2():
    assert SETTINGS_VERSION == 2
    assert "is_half_precision" in SHARED_OPTIONS
