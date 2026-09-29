"""Separate view: dynamic per-method form, browse controls, drop zone.

Full form content arrives in a later task; this scaffold owns the layout
skeleton and the stable builder signature.
"""

from __future__ import annotations

import flet as ft


def fields_for_method(method: str) -> list[str]:
    """Option keys rendered for ``method`` (capability subset)."""
    from uvr.core.capability_registry import CAPABILITIES

    return list(CAPABILITIES.get(method, []))


def build_separate_view(service, store, bus) -> ft.View:
    _ = (service, store, bus)
    return ft.View(
        route="/separate",
        controls=[
            ft.Text("Separate", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Method form, browse controls, and drop zone go here."),
        ],
    )
