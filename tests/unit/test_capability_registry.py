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


def test_real_legacy_keys_survive_migration():
    from uvr.core.capability_registry import OUTPUT_OPTIONS

    legacy = {
        "vr_voc_inst_secondary_model_scale": "0.9",
        "mdx_other_secondary_model_scale": "0.7",
        "demucs_bass_secondary_model_scale": "0.5",
        "demucs_stems": "Vocals",
        "mdx_stems": "Vocals",
        "is_normalization": True,
        "is_replaygain": False,
        "semitone_shift": "0",
        "is_deverb_vocals": False,
        "deverb_vocal_opt": "Main Vocals Only",
        "is_mixer_mode": False,
        "set_vocal_splitter": "No Model Selected",
        "is_save_inst_set_vocal_splitter": False,
        "voc_split_save_opt": "Lead Only",
        "is_add_model_name": True,
        "is_testing_audio": False,
    }
    kept, unknown = migrate_legacy(legacy)
    assert unknown == []
    assert set(kept) == set(legacy)
    assert "is_normalization" in OUTPUT_OPTIONS
