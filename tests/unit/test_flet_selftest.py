"""Tests for the Flet scaffold headless selftest."""

from flet_gui.app import build_all


def test_selftest_builds_all_views():
    views = build_all(headless=True)
    assert set(views) == {"separate", "queue", "log", "settings"}
