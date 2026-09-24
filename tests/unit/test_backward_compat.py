

def test_separate_module_reexports():
    import separate
    # Check backward compatible Seperate* aliases
    assert hasattr(separate, "SeperateDemucs")
    assert hasattr(separate, "SeperateMDX")
    assert hasattr(separate, "SeperateMDXC")
    assert hasattr(separate, "SeperateVR")
    assert hasattr(separate, "SeparateDemucs")
    assert hasattr(separate, "SeparateMDX")
    assert hasattr(separate, "SeparateMDXC")
    assert hasattr(separate, "SeparateVR")
    # Check alias equality
    assert separate.SeperateDemucs is separate.SeparateDemucs
    assert separate.SeperateMDX is separate.SeparateMDX
    assert separate.SeperateMDXC is separate.SeparateMDXC
    assert separate.SeperateVR is separate.SeparateVR


def test_error_handling_aliases():
    from gui_data.error_handling import error_dialogue
    try:
        raise ValueError("Test error")
    except ValueError as exc:
        msg = error_dialogue(exc)
        assert "ValueError" in msg


def test_combine_arrays_alias():
    from lib_v5.spec_utils import combine_arrarys, combine_arrays
    assert combine_arrarys is combine_arrays
