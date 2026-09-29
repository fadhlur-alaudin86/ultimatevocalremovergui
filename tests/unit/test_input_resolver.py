"""Tests for InputResolver drag-drop/folder resolution."""

from uvr.core.input_resolver import InputResolver


def test_resolve_folder_recursive_filters(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.wav").touch()
    (tmp_path / "sub" / "b.mp3").touch()
    (tmp_path / "note.txt").touch()
    accepted, rejected = InputResolver.resolve([str(tmp_path)])
    assert accepted == sorted(accepted) and len(accepted) == 2
    assert any("note.txt" in r for r in rejected)


def test_resolve_empty_folder_returns_empty_with_warning(tmp_path):
    assert InputResolver.resolve([str(tmp_path)]) == ([], [])


def test_resolve_dedupes_and_sorts(tmp_path):
    f = tmp_path / "b.flac"
    f.touch()
    accepted, _ = InputResolver.resolve([str(f), str(f), str(tmp_path)])
    assert accepted == [str(f)]


def test_resolve_missing_path_is_rejected():
    accepted, rejected = InputResolver.resolve(["/no/such/file.wav"])
    assert accepted == []
    assert rejected == ["/no/such/file.wav"]
