"""Log view: service events and backend messages."""

from __future__ import annotations

import flet as ft


def build_log_view(bus) -> ft.View:
    lines = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def append(entry) -> None:
        lines.controls.append(ft.Text(str(entry)))
        if len(lines.controls) > 500:
            del lines.controls[: len(lines.controls) - 500]
        try:
            page = lines.page
        except RuntimeError:
            page = None
        if page is not None:
            lines.update()

    bus.subscribe("log", append)
    view = ft.View(
        route="/log",
        controls=[
            ft.Text("Log", size=24, weight=ft.FontWeight.BOLD),
            lines,
        ],
    )
    view.data = {"lines": lines}
    return view
