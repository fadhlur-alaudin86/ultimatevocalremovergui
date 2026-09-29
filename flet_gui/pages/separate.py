"""Separate view: dynamic per-method form, browse controls, drop zone.

Forms render from ``CAPABILITIES`` so each method shows exactly the options
it owns; shared device/half/sample/format controls gate half-precision via
``DeviceManager``. All input paths (picker, folder, paste) funnel through
``InputResolver`` per the Task 9 spike verdict.
"""

from __future__ import annotations

import flet as ft

from gui_data.constants import (
    AUDIO_TOOLS,
    DEMUCS_ARCH_TYPE,
    ENSEMBLE_MODE,
    MDX_ARCH_TYPE,
    VR_ARCH_PM,
)
from uvr.core.capability_registry import (
    CAPABILITIES,
    OUTPUT_OPTIONS,
    SHARED_OPTIONS,
    is_known_option,
)
from uvr.core.device_manager import DeviceManager
from uvr.core.input_resolver import InputResolver
from uvr.core.jobs import JobSpec

METHOD_ORDER = [VR_ARCH_PM, MDX_ARCH_TYPE, DEMUCS_ARCH_TYPE, ENSEMBLE_MODE, AUDIO_TOOLS]


def _page_of(control):
    """Return the control's page, or None when unmounted (headless/selftest)."""
    try:
        return control.page
    except RuntimeError:
        return None


def fields_for_method(method: str) -> list[str]:
    """Option keys rendered for ``method`` (capability subset)."""
    return list(CAPABILITIES.get(method, []))


def half_gate(want_gpu: bool, device_set: str | int) -> tuple[bool, str]:
    """Return ``(allowed, reason)`` for the half-precision checkbox."""
    try:
        device = DeviceManager.resolve(device_set, want_gpu=want_gpu)
    except ValueError as exc:
        return False, str(exc)
    if DeviceManager.half_allowed(device):
        return True, ""
    if not want_gpu or DeviceManager.autocast_device(device) != "cuda":
        return False, "Half-precision needs a CUDA GPU (CPU/MPS run full precision)."
    return False, "Half-precision disabled: GPU compute capability < 7.0."


def collect_submit_options(store_data: dict, form_state: dict) -> dict:
    """Merge persisted store values with live form state for submit.

    Store holds per-method/output edits; form state holds shared toggles.
    Unknown keys are dropped; form state wins on conflict.
    """
    options = {k: v for k, v in store_data.items() if is_known_option(k)}
    options.update({k: v for k, v in form_state.items() if k in SHARED_OPTIONS})
    return options


def describe_resolve(accepted: list[str], rejected: list[str], source: str) -> str | None:
    """Warning message when a drop/pick yields nothing usable, else None."""
    if not accepted and not rejected:
        return f"No supported audio files found in: {source}"
    return None


def build_job_specs(
    *,
    method: str,
    model_id: str | None,
    input_paths: list[str],
    export_path: str,
    options: dict,
    job_id: int = 0,
) -> list[JobSpec]:
    """Build one frozen ``JobSpec`` snapshot per submit.

    ``spec.job_id`` is informational (0 = unassigned); the service counter
    is the canonical id returned by ``submit``.
    """
    get = options.get
    return [
        JobSpec(
            job_id=job_id,
            process_method=method,
            model_id=model_id,
            input_paths=tuple(input_paths),
            export_path=export_path,
            is_half_precision=bool(get("is_half_precision", False)),
            is_gpu_conversion=bool(get("is_gpu_conversion", False)),
            device_set=get("device_set", "Default"),
            save_format=get("save_format", "WAV"),
            wav_type_set=get("wav_type_set", "PCM_16"),
            mp3_bit_set=get("mp3_bit_set", "320k"),
            is_model_sample_mode=bool(get("is_model_sample_mode", False)),
            extra={k: v for k, v in options.items()},
        )
    ]


def create_pickers():
    """File/folder/output pickers (host must add them to ``page.overlay``)."""
    file_picker = ft.FilePicker()
    folder_picker = ft.FilePicker()
    output_picker = ft.FilePicker()
    return file_picker, folder_picker, output_picker


def build_separate_view(service, store, bus) -> ft.View:
    form_state: dict = {
        "method": METHOD_ORDER[0],
        "model_id": "",
        "inputs": [],
        "export_path": "",
        "is_gpu_conversion": False,
        "is_half_precision": False,
        "device_set": "Default",
        "is_model_sample_mode": False,
        "save_format": "WAV",
    }
    fields_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    input_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    status_text = ft.Text("Idle")
    half_checkbox = ft.Checkbox(label="Half-precision (AMP)", value=False)
    half_reason = ft.Text("", size=12)
    output_field = ft.TextField(label="Output folder", value="", expand=True)
    paste_field = ft.TextField(label="Paste file or folder path", expand=True)
    file_picker, folder_picker, output_picker = create_pickers()

    def refresh_inputs() -> None:
        input_list.controls = [ft.Text(path) for path in form_state["inputs"]]

    def add_paths(paths: list[str]) -> None:
        accepted, rejected = InputResolver.resolve(paths)
        for path in accepted:
            if path not in form_state["inputs"]:
                form_state["inputs"].append(path)
        refresh_inputs()
        for path in rejected:
            bus.publish("log", f"Skipped unsupported input: {path}")
        warning = describe_resolve(accepted, rejected, ", ".join(paths) or "(empty)")
        if warning is not None:
            bus.publish("log", warning)
        status_text.value = f"{len(form_state['inputs'])} input(s)"
        for control in (input_list, status_text):
            if _page_of(control) is not None:
                control.update()

    def refresh_half_gate() -> None:
        allowed, reason = half_gate(form_state["is_gpu_conversion"], form_state["device_set"])
        half_checkbox.disabled = not allowed
        if not allowed:
            half_checkbox.value = False
            form_state["is_half_precision"] = False
        half_reason.value = reason
        for control in (half_checkbox, half_reason):
            if _page_of(control) is not None:
                control.update()

    def render_fields() -> None:
        method = form_state["method"]
        controls: list[ft.Control] = [ft.Text(f"{method} options", weight=ft.FontWeight.BOLD)]
        for key in fields_for_method(method) + OUTPUT_OPTIONS:
            field = ft.TextField(label=key, value=str(store.get(key, "")))
            field.data = key

            def on_field_change(event: ft.ControlEvent, _key=key) -> None:
                store.set(_key, event.control.value)

            field.on_change = on_field_change
            controls.append(field)
        fields_column.controls = controls
        if _page_of(fields_column) is not None:
            fields_column.update()

    def on_method_change(event: ft.ControlEvent) -> None:
        form_state["method"] = event.control.value
        store.set("last_method", event.control.value)
        render_fields()

    def on_gpu_change(event: ft.ControlEvent) -> None:
        form_state["is_gpu_conversion"] = bool(event.control.value)
        refresh_half_gate()

    def on_half_change(event: ft.ControlEvent) -> None:
        form_state["is_half_precision"] = bool(event.control.value)

    def on_model_change(event: ft.ControlEvent) -> None:
        form_state["model_id"] = event.control.value

    def on_format_select(event: ft.ControlEvent) -> None:
        form_state["save_format"] = event.control.value

    def on_start_click(_event: ft.ControlEvent) -> None:
        specs = build_job_specs(
            method=form_state["method"],
            model_id=form_state["model_id"] or None,
            input_paths=list(form_state["inputs"]),
            export_path=output_field.value or form_state["export_path"],
            options=collect_submit_options(store.as_dict(), form_state),
        )
        try:
            job_id = service.submit(specs[0])
        except Exception as exc:
            status_text.value = f"Submit failed: {exc}"
            bus.publish("log", f"Submit failed: {exc}")
        else:
            status_text.value = f"Submitted job {job_id}"
            bus.publish("queue-changed", job_id)
        if _page_of(status_text) is not None:
            status_text.update()

    def on_output_picked(event: ft.ControlEvent) -> None:
        output_field.value = event.path or ""
        form_state["export_path"] = event.path or ""
        if _page_of(output_field) is not None:
            output_field.update()

    file_picker.on_result = lambda event: add_paths([f.path for f in (event.files or []) if f.path])
    folder_picker.on_result = lambda event: add_paths([event.path] if event.path else [])
    output_picker.on_result = on_output_picked

    method_dropdown = ft.Dropdown(
        label="Method",
        options=[ft.dropdown.Option(key) for key in METHOD_ORDER],
        value=form_state["method"],
        on_select=on_method_change,
    )
    gpu_checkbox = ft.Checkbox(label="GPU", value=False, on_change=on_gpu_change)
    half_checkbox.on_change = on_half_change
    model_field = ft.TextField(label="Model", value="", on_change=on_model_change)
    format_dropdown = ft.Dropdown(
        label="Format",
        options=[ft.dropdown.Option(fmt) for fmt in ("WAV", "FLAC", "MP3")],
        value=form_state["save_format"],
        on_select=on_format_select,
    )

    render_fields()
    refresh_inputs()

    view = ft.View(
        route="/separate",
        controls=[
            ft.Row([method_dropdown, model_field, format_dropdown, gpu_checkbox, half_checkbox], wrap=True),
            half_reason,
            ft.Row(
                [
                    ft.Button("Add files…", on_click=lambda _: file_picker.pick_files(allow_multiple=True)),
                    ft.Button("Add folder…", on_click=lambda _: folder_picker.get_directory_path()),
                    paste_field,
                    ft.Button("Add", on_click=lambda _: add_paths([paste_field.value])),
                ],
                wrap=True,
            ),
            ft.Row([output_field, ft.Button("Browse…", on_click=lambda _: output_picker.get_directory_path())]),
            ft.Row([fields_column, input_list], expand=True),
            ft.Row([ft.Button("Start", on_click=on_start_click), status_text]),
        ],
    )
    view.data = {"pickers": [file_picker, folder_picker, output_picker]}
    return view
