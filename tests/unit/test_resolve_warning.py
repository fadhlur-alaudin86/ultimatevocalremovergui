"""Tests for the empty-resolve warning message."""

from flet_gui.pages.separate import describe_resolve


def test_empty_resolve_warns():
    msg = describe_resolve([], [], "my_folder")
    assert msg is not None and "my_folder" in msg


def test_nonempty_resolve_is_quiet():
    assert describe_resolve(["/tmp/a.wav"], [], "my_folder") is None
    assert describe_resolve([], ["note.txt"], "my_folder") is None
