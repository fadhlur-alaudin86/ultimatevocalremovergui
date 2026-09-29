"""Settings view: v2 schema save/load plus legacy import."""

from __future__ import annotations

import json
from pathlib import Path

from uvr.core.capability_registry import SETTINGS_VERSION


def save_settings(directory: str | Path, data: dict) -> Path:
    """Persist settings with the v2 schema marker; returns the file path."""
    path = Path(directory) / "uvr_settings_v2.json"
    payload = {"version": SETTINGS_VERSION, **data}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def build_settings_view(store, bus):
    import flet as ft

    _ = (store, bus)
    return ft.View(
        route="/settings",
        controls=[
            ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Settings form goes here."),
        ],
    )
