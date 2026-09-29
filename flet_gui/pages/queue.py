"""Queue view: multi-select job list with play/pause/stop controls."""

from __future__ import annotations

import flet as ft


def on_stop_selected(service, ids: list[int]) -> None:
    """Cancel the selected jobs (helper kept testable without Flet)."""
    service.cancel(ids)


def build_queue_view(service, bus) -> ft.View:
    _ = (service, bus)
    return ft.View(
        route="/queue",
        controls=[
            ft.Text("Queue", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Job list and controls go here."),
        ],
    )
