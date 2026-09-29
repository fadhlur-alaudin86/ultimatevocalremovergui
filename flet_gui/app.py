"""Flet GUI entry point: navigation rail, swappable views, status bar."""

from __future__ import annotations

import argparse
import sys

import flet as ft

from flet_gui.pages.log_view import build_log_view
from flet_gui.pages.queue import build_queue_view
from flet_gui.pages.separate import build_separate_view
from flet_gui.pages.settings import build_settings_view
from flet_gui.state import ConfigStore, EventBus
from uvr.core.service import InferenceService

VIEW_KEYS = ("separate", "queue", "log", "settings")


def _noop_runner(spec, pause_event, cancel_event) -> None:
    """Placeholder runner until real model wiring lands (integration)."""


def build_all(headless: bool = False) -> dict:
    """Construct every view without starting a window (selftest path)."""
    _ = headless
    service = InferenceService(run_fn=_noop_runner, autostart=False)
    store = ConfigStore()
    bus = EventBus()
    return {
        "separate": build_separate_view(service, store, bus),
        "queue": build_queue_view(service, bus),
        "log": build_log_view(bus),
        "settings": build_settings_view(store, bus),
    }


def main(page: ft.Page) -> None:
    page.title = "UVR Flet GUI"
    service = InferenceService(run_fn=_noop_runner)
    store = ConfigStore()
    bus = EventBus()
    views = {
        "separate": build_separate_view(service, store, bus),
        "queue": build_queue_view(service, bus),
        "log": build_log_view(bus),
        "settings": build_settings_view(store, bus),
    }
    status = ft.Text("Idle")

    def on_rail_change(event: ft.ControlEvent) -> None:
        page.views.clear()
        page.views.append(views[VIEW_KEYS[event.control.selected_index]])
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        destinations=[ft.NavigationRailDestination(label=key.title()) for key in VIEW_KEYS],
        on_change=on_rail_change,
    )
    for key in ("separate", "settings"):
        for picker in views[key].data.get("pickers", []):
            page.overlay.append(picker)
    page.add(ft.Row([rail, ft.VerticalDivider(width=1), views["separate"]], expand=True), status)


def _selftest() -> int:
    views = build_all(headless=True)
    assert set(views) == set(VIEW_KEYS), set(views)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        sys.exit(_selftest())
    ft.run(main)
