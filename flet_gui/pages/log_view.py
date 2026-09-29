"""Log view: service events and backend messages."""

from __future__ import annotations

import flet as ft


def build_log_view(bus) -> ft.View:
    _ = bus
    return ft.View(
        route="/log",
        controls=[
            ft.Text("Log", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Log output goes here."),
        ],
    )
