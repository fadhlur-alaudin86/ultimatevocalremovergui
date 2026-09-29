"""Settings view: v2 schema save/load plus legacy import."""

from __future__ import annotations

import json
from pathlib import Path

import flet as ft

from uvr.core.capability_registry import SETTINGS_VERSION, migrate_legacy


def save_settings(directory: str | Path, data: dict) -> Path:
    """Persist settings with the v2 schema marker; returns the file path."""
    path = Path(directory) / "uvr_settings_v2.json"
    payload = {"version": SETTINGS_VERSION, **data}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def import_legacy_file(path: str | Path, store, bus) -> tuple[dict, list[str]]:
    """Import a legacy flat settings JSON into the store.

    Returns ``(kept, unknown)``; dropped keys are reported on the log bus.
    """
    data = json.loads(Path(path).read_text())
    kept, unknown = migrate_legacy(data)
    for key, value in kept.items():
        store.set(key, value)
    if unknown:
        bus.publish("log", f"Legacy import dropped {len(unknown)} unknown key(s): {', '.join(unknown)}")
    else:
        bus.publish("log", "Legacy import: all keys recognized.")
    return kept, unknown


def build_settings_view(store, bus) -> ft.View:
    status_text = ft.Text("")
    picker = ft.FilePicker()

    def on_import_picked(event: ft.ControlEvent) -> None:
        if not event.files:
            return
        try:
            kept, unknown = import_legacy_file(event.files[0].path, store, bus)
        except (OSError, ValueError, KeyError) as exc:
            status_text.value = f"Import failed: {exc}"
        else:
            status_text.value = f"Imported {len(kept)} setting(s), dropped {len(unknown)}."
        try:
            page = status_text.page
        except RuntimeError:
            page = None
        if page is not None:
            status_text.update()

    def on_save_click(_event: ft.ControlEvent) -> None:
        try:
            path = save_settings(".", store.as_dict())
        except OSError as exc:
            status_text.value = f"Save failed: {exc}"
        else:
            status_text.value = f"Saved to {path}"
        try:
            page = status_text.page
        except RuntimeError:
            page = None
        if page is not None:
            status_text.update()

    picker.on_result = on_import_picked
    view = ft.View(
        route="/settings",
        controls=[
            ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.Button("Save settings (v2)", on_click=on_save_click),
                    ft.Button("Import legacy JSON…", on_click=lambda _: picker.pick_files()),
                    status_text,
                ],
                wrap=True,
            ),
        ],
    )
    view.data = {"pickers": [picker]}
    return view
