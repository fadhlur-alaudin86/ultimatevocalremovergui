from uvr.utils.file_utils import (
    ensure_dir,
    get_file_extension,
    is_supported_audio,
    sanitize_filename,
)


def test_sanitize_filename():
    unsafe = 'my<song>:name"cool?.wav'
    sanitized = sanitize_filename(unsafe)
    assert '<' not in sanitized
    assert '>' not in sanitized
    assert ':' not in sanitized
    assert '"' not in sanitized
    assert '?' not in sanitized


def test_ensure_dir(tmp_path):
    target = tmp_path / "deep" / "nested" / "dir"
    ensure_dir(str(target))
    assert target.is_dir()


def test_get_file_extension():
    assert get_file_extension("audio.wav") == ".wav"
    assert get_file_extension("track.FLAC") == ".flac"
    assert get_file_extension("/path/to/song.mp3") == ".mp3"


def test_is_supported_audio():
    assert is_supported_audio("song.wav") is True
    assert is_supported_audio("song.mp3") is True
    assert is_supported_audio("song.flac") is True
    assert is_supported_audio("song.m4a") is True
    assert is_supported_audio("song.txt") is False
    assert is_supported_audio("song.json") is False
