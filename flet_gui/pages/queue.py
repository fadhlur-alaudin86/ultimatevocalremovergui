"""Queue view: multi-select job list with play/pause/stop controls."""

from __future__ import annotations

import flet as ft


def selected_ids(checkboxes) -> list[int]:
    """Return job ids of checked boxes."""
    return [box.data for box in checkboxes if box.value]


def on_play_selected(service, ids: list[int]) -> None:
    """Resume (play) the selected jobs."""
    service.resume(ids)


def on_pause_selected(service, ids: list[int]) -> None:
    """Pause the selected jobs."""
    service.pause(ids)


def on_stop_selected(service, ids: list[int]) -> None:
    """Cancel the selected jobs (helper kept testable without Flet)."""
    service.cancel(ids)


def on_stop_all(service) -> None:
    """Cancel everything and empty the worker."""
    service.cancel_all()


def build_queue_view(service, bus) -> ft.View:
    job_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    status_text = ft.Text("No jobs")
    boxes: list[ft.Checkbox] = []

    def refresh(_payload=None) -> None:
        boxes.clear()
        rows: list[ft.Control] = []
        for job_id, status in sorted(service.statuses().items()):
            box = ft.Checkbox(label=f"Job {job_id} — {status}", value=False)
            box.data = job_id
            boxes.append(box)
            rows.append(box)
        job_column.controls = rows
        count = len(rows)
        status_text.value = f"{count} job(s)" if count else "No jobs"
        for control in (job_column, status_text):
            try:
                page = control.page
            except RuntimeError:
                page = None
            if page is not None:
                control.update()

    bus.subscribe("queue-changed", refresh)
    if hasattr(service, "add_listener"):
        service.add_listener(lambda _job_id, _status: refresh())
    refresh()

    return ft.View(
        route="/queue",
        controls=[
            ft.Text("Queue", size=24, weight=ft.FontWeight.BOLD),
            job_column,
            ft.Row(
                [
                    ft.Button("Play", on_click=lambda _: on_play_selected(service, selected_ids(boxes))),
                    ft.Button("Pause", on_click=lambda _: on_pause_selected(service, selected_ids(boxes))),
                    ft.Button("Stop selected", on_click=lambda _: on_stop_selected(service, selected_ids(boxes))),
                    ft.Button("Stop all", on_click=lambda _: on_stop_all(service)),
                    ft.Button("Refresh", on_click=lambda _: refresh()),
                    status_text,
                ],
                wrap=True,
            ),
        ],
    )
