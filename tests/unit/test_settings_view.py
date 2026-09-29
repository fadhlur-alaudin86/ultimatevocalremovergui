"""Tests for Log and Settings views (v2 schema + legacy import)."""

import json

from flet_gui.pages.log_view import build_log_view
from flet_gui.pages.settings import import_legacy_file, save_settings
from flet_gui.state import ConfigStore, EventBus


def test_save_writes_v2_schema(tmp_path):
    path = save_settings(tmp_path, {"vr_model": "x"})
    assert json.loads(path.read_text())["version"] == 2


def test_import_legacy_migrates_and_logs(tmp_path):
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps({"vr_model": "x", "bogus_key": 1, "help_hints_var": True}))
    store = ConfigStore()
    bus = EventBus()
    logged = []
    bus.subscribe("log", logged.append)
    kept, unknown = import_legacy_file(str(legacy), store, bus)
    assert kept["vr_model"] == "x"
    assert store.get("vr_model") == "x"
    assert unknown == ["bogus_key", "help_hints_var"]
    assert any("bogus_key" in entry for entry in logged)


def test_log_view_appends_published_entries():
    bus = EventBus()
    view = build_log_view(bus)
    bus.publish("log", "hello backend")
    lines = view.data["lines"].controls
    assert any("hello backend" in line.value for line in lines)
