# UVR Flet GUI Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the headless backend (AMP, snapshot, cooperative queue control) then build the Flet GUI on a stable service contract.

**Architecture:** Phase A adds `uvr/core/` service pieces (`DeviceManager`, `JobSpec`/`JobError`, `InputResolver`, `CapabilityRegistry`, `InferenceService`) with cooperative pause/cancel events checked in the four model batch loops; Phase B builds a `flet_gui/` package (Separate/Queue/Log/Settings views) that talks only to `InferenceService`.

**Tech Stack:** Python 3.11, PyTorch (existing), Flet `flet>=1.0,<2.0`, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-09-29-uvr-flet-gui-design.md`

## Global Constraints

- Python floor 3.11; torch API as in `.venv` (torch 2.12+cu130).
- `ruff check` and `ruff format --check` clean on every touched file (`ruff.toml`: target py311, line-length 120).
- Legacy Tkinter UI (`UVR.py`, `uvr/ui/*`) is frozen: read-only reference, never modified.
- Views never import `uvr/models/*` directly; only `uvr/core/service.py` public API.
- Flet dependency pinned as `flet>=1.0,<2.0` (same floor as DeepFilterNet `requirements-gui.txt`).
- GPU numeric tests run in `.venv` (CUDA available, GTX 1650 Max-Q CC 7.5); skip cleanly when `torch.cuda.is_available()` is False.
- Test runner: `.venv/bin/python -m pytest`; linter: `ruff`.

## Review Focus

- Corrupt/empty MP3 input must fall back to `rerun_mp3` or raise `JobError(code="BAD_INPUT")`, never hang the worker. Pinned in Task 7.
- Folder drop containing zero supported files must produce an empty job with a Log warning, not a crash. Pinned in Task 5.
- `device_set` pointing at a missing GPU index must raise `JobError(code="BAD_DEVICE")` before any model load. Pinned in Task 1.
- Half-precision requested on CPU/MPS must silently run fp32 with a Log note, never enter `autocast("mps")`. Pinned in Tasks 1-2.
- Cancel arriving mid-write must delete the partial wav and temp dir entries, never leave half files as final outputs. Pinned in Task 7.

---

### Task 1: DeviceManager (device resolution + AMP gate)

**Files:**
- Create: `uvr/core/device_manager.py`
- Test: `tests/unit/test_device_manager.py`

**Interfaces:**
- Consumes: `torch`, `gui_data/constants.py` (`DEFAULT`, `CUDA_DEVICE`).
- Produces: `DeviceManager.resolve(device_set: str | int, want_gpu: bool) -> torch.device | str`; `DeviceManager.autocast_device(device) -> str` (returns `"cuda"` or `"cpu"`, never `"mps"`); `DeviceManager.half_allowed(device) -> bool` (False unless CUDA with capability >= (7, 0) on the selected device). Used by Tasks 2 and 7.

- [ ] **Step 1: Write the failing test**

```python
def test_autocast_device_never_returns_mps():
    assert DeviceManager.autocast_device("mps") == "cpu"

def test_half_allowed_requires_cuda_cc7():
    assert DeviceManager.half_allowed(torch.device("cpu")) is False

def test_resolve_bad_index_raises():
    with pytest.raises(ValueError):
        DeviceManager.resolve(99, want_gpu=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_device_manager.py -v`
Expected: FAIL with "DeviceManager not defined" (or collection error).

- [ ] **Step 3: Implement `DeviceManager` in `uvr/core/device_manager.py`**

Pure functions/classmethods only; CC check via `torch.cuda.get_device_capability(idx)` on the selected index; any CUDA exception means `half_allowed` False.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_device_manager.py -v`
Expected: PASS.

- [ ] **Step 5: Run `ruff check uvr/core/device_manager.py tests/unit/test_device_manager.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/core/device_manager.py tests/unit/test_device_manager.py
git commit -m "feat(core): add DeviceManager with per-device AMP gate"
```

### Task 2: Route all four models through DeviceManager autocast

**Files:**
- Modify: `uvr/models/vr.py:152-153`, `uvr/models/mdx.py:194-195`, `uvr/models/demucs.py:219-220`, `uvr/models/mdxc.py:336-337`, `uvr/models/base.py:1-30` (shared import only)
- Test: `tests/unit/test_half_precision.py`

**Interfaces:**
- Consumes: `DeviceManager.autocast_device` from Task 1.
- Produces: identical numerics with flag off; no other signature changes. Used by Task 7.

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.gpu
def test_autocast_context_never_uses_mps_device_type():
    ctx_device = DeviceManager.autocast_device("mps")
    with torch.autocast(device_type=ctx_device, dtype=torch.float16, enabled=False):
        pass

@pytest.mark.gpu
def test_half_on_off_no_nans_cpu_smoke():
    assert DeviceManager.half_allowed(torch.device("cpu")) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_half_precision.py -v`
Expected: FAIL (import error, DeviceManager missing or models not routed).

- [ ] **Step 3: Replace each inline `device_type_str` derivation with `DeviceManager.autocast_device(self.device)`** in the four `torch.autocast(...)` call sites; keep `enabled=self.is_half_precision and autocast_device == "cuda"`.

- [ ] **Step 4: Run GPU numeric check (manual, GTX 1650): run one VR inference with flag on/off; assert no NaN/crash; record peak delta in the commit message.**

Run: `.venv/bin/python -m pytest tests/unit/test_half_precision.py -v`
Expected: PASS (gpu-marked tests run; on CPU-only machines they must skip, not fail).

- [ ] **Step 5: Run `ruff check uvr/models/vr.py uvr/models/mdx.py uvr/models/demucs.py uvr/models/mdxc.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/models tests/unit/test_half_precision.py
git commit -m "fix(models): route autocast through DeviceManager"
```

### Task 3: JobSpec full snapshot + JobError

**Files:**
- Create: `uvr/core/jobs.py`
- Test: `tests/unit/test_job_spec.py`

**Interfaces:**
- Consumes: nothing new (stdlib dataclasses).
- Produces: `@dataclass JobSpec` with fields `job_id: int`, `process_method: str`, `model_id: str | None`, `input_paths: tuple[str, ...]`, `export_path: str`, `is_half_precision: bool`, `is_gpu_conversion: bool`, `device_set: str | int`, `save_format: str`, `wav_type_set: str`, `mp3_bit_set: str`, `is_model_sample_mode: bool`, `extra: dict`; `@dataclass JobError(code: str, message: str, hint: str)`. Used by Tasks 6-7 and Phase B views.

- [ ] **Step 1: Write the failing test**

```python
def test_snapshot_is_immutable_after_source_mutation():
    spec = JobSpec(job_id=1, process_method="VR", model_id="m", input_paths=("a.wav",), export_path="/tmp/x", is_half_precision=True, is_gpu_conversion=True, device_set=0, save_format="WAV", wav_type_set="PCM_16", mp3_bit_set="320k", is_model_sample_mode=False, extra={})
    assert spec.input_paths == ("a.wav",)
    with pytest.raises(Exception):
        spec.job_id = 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_job_spec.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement frozen `JobSpec` and `JobError` in `uvr/core/jobs.py`**

Frozen dataclass; `input_paths` coerced to tuple in `__post_init__`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_job_spec.py -v`
Expected: PASS.

- [ ] **Step 5: Run `ruff check uvr/core/jobs.py tests/unit/test_job_spec.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/core/jobs.py tests/unit/test_job_spec.py
git commit -m "feat(core): add frozen JobSpec snapshot and JobError"
```

### Task 4: Cooperative pause/cancel in model loops

**Files:**
- Modify: `uvr/models/base.py` (`SeparateAttributes.__init__`, store `pause_event`/`cancel_event` from `process_data`), `uvr/models/vr.py:144-159`, `uvr/models/mdx.py:96-198` (chunk loop), `uvr/models/demucs.py:205-255`, `uvr/models/mdxc.py:332-348`, `uvr/models/pipeline.py:30-91` (pass-through only)
- Test: `tests/unit/test_cooperative_control.py`

**Interfaces:**
- Consumes: `process_data["pause_event"]`, `process_data["cancel_event"]` (`threading.Event`, optional, default None = legacy behavior).
- Produces: `uvr.models.base.ControlCancelled(Exception)`; loops raise it promptly on `cancel_event.is_set()` and block on `pause_event.wait()` per batch. Used by Task 7.

- [ ] **Step 1: Write the failing test**

```python
def test_cancel_event_aborts_vr_batch_loop():
    ev = threading.Event(); ev.set()
    with pytest.raises(ControlCancelled):
        check_cancel(ev)

def test_pause_event_blocks_and_resumes():
    ev = threading.Event()
    assert ev.wait(timeout=0.01) is True
```

(Helper-level first; integration asserts each of the four loops calls the helper per iteration.)

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_cooperative_control.py -v`
Expected: FAIL.

- [ ] **Step 3: Add `check_control(pause_event, cancel_event)` helper in `uvr/models/base.py`**; call it once per batch/chunk/segment iteration in all four loops; `pipeline.py` forwards `process_data` unchanged (no new keys invented there).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_cooperative_control.py -v`
Expected: PASS.

- [ ] **Step 5: Run `ruff check uvr/models/ tests/unit/test_cooperative_control.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/models tests/unit/test_cooperative_control.py
git commit -m "feat(models): cooperative pause/cancel checks in batch loops"
```

### Task 5: InputResolver (drag-drop + folder recursion + filter)

**Files:**
- Create: `uvr/core/input_resolver.py`
- Modify: `uvr/utils/file_utils.py:99-102` (extend set with `.opus`, `.aiff`, `.alac` to match `uvr/utils/native_file_dialog.py:19`)
- Test: `tests/unit/test_input_resolver.py`

**Interfaces:**
- Consumes: `uvr/utils/file_utils.py:is_supported_audio`.
- Produces: `InputResolver.resolve(paths: list[str]) -> tuple[list[str], list[str]]` (`(accepted, rejected)`); directories scanned recursively; files filtered by `is_supported_audio`; output sorted, deduplicated. Used by Task 10 (Flet drop zone + pickers).

- [ ] **Step 1: Write the failing test**

```python
def test_resolve_folder_recursive_filters(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.wav").touch(); (tmp_path / "sub" / "b.mp3").touch()
    (tmp_path / "note.txt").touch()
    accepted, rejected = InputResolver.resolve([str(tmp_path)])
    assert accepted == sorted(accepted) and len(accepted) == 2
    assert any("note.txt" in r for r in rejected)

def test_resolve_empty_folder_returns_empty_with_warning(tmp_path):
    assert InputResolver.resolve([str(tmp_path)]) == ([], [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_input_resolver.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `InputResolver.resolve`** with `os.walk`, `is_supported_audio` filter, dedupe + sort.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_input_resolver.py -v`
Expected: PASS.

- [ ] **Step 5: Run `ruff check uvr/core/input_resolver.py uvr/utils/file_utils.py tests/unit/test_input_resolver.py` and existing `pytest tests/unit/test_file_utils.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/core/input_resolver.py uvr/utils/file_utils.py tests/unit/test_input_resolver.py
git commit -m "feat(core): add InputResolver with recursive audio filter"
```

### Task 6: CapabilityRegistry + settings v2 + legacy migrator

**Files:**
- Create: `uvr/core/capability_registry.py`
- Test: `tests/unit/test_capability_registry.py`

**Interfaces:**
- Consumes: `gui_data/constants.py` method keys (`VR_ARCH_PM`, `MDX_ARCH_TYPE`, `DEMUCS_ARCH_TYPE`, `ENSEMBLE_MODE`, `AUDIO_TOOLS`).
- Produces: `CAPABILITIES: dict[str, list[str]]` (method -> allowed option keys); `SETTINGS_VERSION = 2`; `migrate_legacy(data: dict) -> dict` (keeps known keys, drops + returns unknown-key list for logging). Used by Task 10 (dynamic forms) and Task 12 (Settings view).

- [ ] **Step 1: Write the failing test**

```python
def test_vr_has_no_demucs_options():
    assert "shifts" not in CAPABILITIES["VR"]

def test_migrate_drops_unknown_and_reports():
    out, unknown = migrate_legacy({"vr_model": "x", "bogus_key": 1})
    assert out == {"vr_model": "x"} and unknown == ["bogus_key"]
```

(Method keys use the exact constants from `gui_data/constants.py`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_capability_registry.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `CAPABILITIES` covering VR, MDX/MDX-C, Demucs, Ensemble, Audio Tools per-method keys from the spec matrix**, plus `migrate_legacy`. Unify the duplicate Demucs stem-only pair (`is_primary_stem_only_Demucs` / `is_secondary_stem_only_Demucs`) into the single shared `is_primary_stem_only` / `is_secondary_stem_only` pair: registry exposes one `stem_only` option used by all methods.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_capability_registry.py -v`
Expected: PASS.

- [ ] **Step 5: Run `ruff check uvr/core/capability_registry.py tests/unit/test_capability_registry.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/core/capability_registry.py tests/unit/test_capability_registry.py
git commit -m "feat(core): add CapabilityRegistry and settings v2 migrator"
```

### Task 7: InferenceService (submit/pause/resume/cancel + cleanup)

**Files:**
- Create: `uvr/core/service.py`
- Test: `tests/unit/test_inference_service.py`

**Interfaces:**
- Consumes: `JobSpec`/`JobError` (Task 3), control events (Task 4), `DeviceManager` (Task 1), `uvr/utils/file_utils.py:remove_temps`.
- Produces: `InferenceService.submit(spec: JobSpec, run_fn) -> int`; `pause(ids: list[int])`, `resume(ids: list[int])`, `cancel(ids: list[int])`, `cancel_all()`; `statuses() -> dict[int, str]`; cancel deletes partial wavs + calls `remove_temps` on the job temp dir; corrupt input maps to `JobError(code="BAD_INPUT")`. `run_fn` injection keeps tests torch-free. Used by all Phase B views.

- [ ] **Step 1: Write the failing test**

```python
def test_pause_resume_and_cancel_selected():
    svc = InferenceService(run_fn=lambda spec, ctrl: None)
    jid = svc.submit(make_spec(), run_fn=None)
    svc.pause([jid]); assert svc.statuses()[jid] == "paused"
    svc.resume([jid]); assert svc.statuses()[jid] in ("pending", "running")
    svc.cancel([jid]); assert svc.statuses()[jid] == "cancelled"

def test_cancel_removes_partial(tmp_path):
    partial = tmp_path / "out_(Vocals).wav"; partial.touch()
    svc = InferenceService(run_fn=lambda spec, ctrl: None)
    svc._cleanup_partials(str(tmp_path), "out")
    assert not partial.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_inference_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `InferenceService`** on a single background worker thread (one active inference; `threading.Event` per job); pause yields to next job, resume re-queues at front; cancel sets event, joins, cleans temps/partials, marks cancelled.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_inference_service.py -v`
Expected: PASS.

- [ ] **Step 5: Run `ruff check uvr/core/service.py tests/unit/test_inference_service.py`**
- [ ] **Step 6: Commit**

```bash
git add uvr/core/service.py tests/unit/test_inference_service.py
git commit -m "feat(core): add InferenceService with cooperative control"
```

### Task 8: Flet scaffold + dependency + headless selftest

**Files:**
- Modify: `requirements.txt` (append `flet>=1.0,<2.0`)
- Create: `flet_gui/__init__.py`, `flet_gui/app.py` (`main(page)`, `--selftest` builds all views without `ft.run`), `flet_gui/state.py` (`EventBus`, `ConfigStore` holders)
- Test: `tests/unit/test_flet_selftest.py` (runs `app.build_all(headless=True)` or `--selftest`, asserts four views construct)

**Interfaces:**
- Consumes: `InferenceService` (Task 7) instance passed into views; nothing else.
- Produces: `python -m flet_gui.app --selftest` exit 0; `build_all()` returning dict of four views. Used by Tasks 10-12.

- [ ] **Step 1: Write the failing test**

```python
def test_selftest_builds_all_views():
    views = build_all(headless=True)
    assert set(views) == {"separate", "queue", "log", "settings"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_flet_selftest.py -v`
Expected: FAIL (package missing; flet not installed in `.venv` yet — install with `.venv/bin/pip install "flet>=1.0,<2.0"` first and re-run to confirm code-level failure).

- [ ] **Step 3: Scaffold `flet_gui/` with `NavigationRail` (Separate/Queue/Log/Settings) + status bar**, following `~/.clone/Github/DeepFilterNet/gui/app.py` structure.

- [ ] **Step 4: Run test + selftest to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_flet_selftest.py -v && .venv/bin/python -m flet_gui.app --selftest`
Expected: PASS / exit 0.

- [ ] **Step 5: Run `ruff check flet_gui/ tests/unit/test_flet_selftest.py`**
- [ ] **Step 6: Commit**

```bash
git add requirements.txt flet_gui tests/unit/test_flet_selftest.py
git commit -m "feat(gui): scaffold Flet app with headless selftest"
```

### Task 9: Spike — OS file-drop support in pinned Flet (time-boxed)

**Files:**
- Create: `docs/superpowers/specs/2026-09-29-flet-drop-spike.md` (2-3 sentence verdict + chosen path)
- Test: none (spike output is a decision, throwaway probe only)

- [ ] **Step 1: Probe whether the pinned Flet version delivers OS file/folder drops onto the window** (drop event with paths) on Linux.
- [ ] **Step 2: Record verdict**: native drop supported (use it) or not (fallback: prominent DropZone button opening `FilePicker` multi-select + folder pick + path paste; keep `InputResolver` as the single funnel so a later Flet upgrade enables native drop without backend changes).
- [ ] **Step 3: Commit the spike note**

```bash
git add docs/superpowers/specs/2026-09-29-flet-drop-spike.md
git commit -m "docs(spike): Flet OS file-drop verdict"
```

### Task 10: Separate view (dynamic per-method form + browse + drop)

**Files:**
- Create: `flet_gui/pages/separate.py`
- Test: extend `tests/unit/test_flet_selftest.py` (form renders only `CAPABILITIES[method]` keys per method; switching method swaps fields)

**Interfaces:**
- Consumes: `CAPABILITIES` (Task 6), `InputResolver.resolve` (Task 5), `InferenceService.submit` (Task 7), Flet `FilePicker` (`pick_files(allow_multiple=True)`, folder pick) for browse-input alternative and `get_directory_path` for browse-output.
- Produces: `build_separate_view(service, store) -> ft.View`; emits frozen `JobSpec` per file on submit.

- [ ] **Step 1: Write the failing test**

```python
def test_form_fields_match_capabilities():
    fields = fields_for_method("DEMUCS")
    assert "shifts" in fields and "aggression_setting" not in fields
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_flet_selftest.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement dynamic form from `CAPABILITIES` on responsive `Column`/`Row`**; shared device/half/sample/format row with half disabled + reason when `DeviceManager.half_allowed` False; browse-input buttons + drop zone (per Task 9 verdict) both funnel into `InputResolver.resolve`; output path via directory picker.

- [ ] **Step 4: Run test + selftest to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_flet_selftest.py -v && .venv/bin/python -m flet_gui.app --selftest`
Expected: PASS / exit 0.

- [ ] **Step 5: Run `ruff check flet_gui/pages/separate.py`**
- [ ] **Step 6: Commit**

```bash
git add flet_gui/pages/separate.py tests/unit/test_flet_selftest.py
git commit -m "feat(gui): dynamic per-method Separate view with browse and drop"
```

### Task 11: Queue view (multi-select play/pause/stop)

**Files:**
- Create: `flet_gui/pages/queue.py`
- Test: `tests/unit/test_queue_view.py` (selection maps to `pause`/`resume`/`cancel` calls on a fake service; stop-all calls `cancel_all`)

**Interfaces:**
- Consumes: `InferenceService.pause/resume/cancel/cancel_all/statuses` (Task 7).
- Produces: `build_queue_view(service) -> ft.View` with multi-select list and Play/Pause/Stop-selected/Stop-all buttons.

- [ ] **Step 1: Write the failing test**

```python
def test_stop_selected_calls_cancel_with_ids():
    fake = FakeService()
    on_stop_selected(fake, [2, 3])
    assert fake.cancelled == [2, 3]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_queue_view.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement the queue view** wiring buttons to service methods; statuses poll via `EventBus`.

- [ ] **Step 4: Run test + selftest to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_queue_view.py -v && .venv/bin/python -m flet_gui.app --selftest`
Expected: PASS / exit 0.

- [ ] **Step 5: Run `ruff check flet_gui/pages/queue.py tests/unit/test_queue_view.py`**
- [ ] **Step 6: Commit**

```bash
git add flet_gui/pages/queue.py tests/unit/test_queue_view.py
git commit -m "feat(gui): queue view with multi-select control"
```

### Task 12: Log + Settings views (v2 + legacy import)

**Files:**
- Create: `flet_gui/pages/log_view.py`, `flet_gui/pages/settings.py`
- Test: `tests/unit/test_settings_view.py` (save writes `{version: 2, ...}`; legacy `gui_data/saved_settings/*.json` migrates with unknown keys logged)

**Interfaces:**
- Consumes: `migrate_legacy` (Task 6), `EventBus` log stream (Task 8).
- Produces: `build_log_view(bus)`, `build_settings_view(store)` with Save + Import-legacy buttons.

- [ ] **Step 1: Write the failing test**

```python
def test_save_writes_v2_schema(tmp_path):
    path = save_settings(tmp_path, {"vr_model": "x"})
    assert json.loads(path.read_text())["version"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_settings_view.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement both views**; import-legacy runs `migrate_legacy` over the chosen file and surfaces dropped keys in the Log view.

- [ ] **Step 4: Run test + selftest to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_settings_view.py -v && .venv/bin/python -m flet_gui.app --selftest`
Expected: PASS / exit 0.

- [ ] **Step 5: Run `ruff check flet_gui/pages/log_view.py flet_gui/pages/settings.py tests/unit/test_settings_view.py`**
- [ ] **Step 6: Commit**

```bash
git add flet_gui/pages/log_view.py flet_gui/pages/settings.py tests/unit/test_settings_view.py
git commit -m "feat(gui): log and v2 settings views with legacy import"
```

### Task 13: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: PASS (gpu-marked tests run on CUDA hosts, skip elsewhere).

- [ ] **Step 2: Run lint and format check**

Run: `ruff check . && ruff format --check uvr/core flet_gui tests/unit/test_device_manager.py tests/unit/test_half_precision.py tests/unit/test_job_spec.py tests/unit/test_cooperative_control.py tests/unit/test_input_resolver.py tests/unit/test_capability_registry.py tests/unit/test_inference_service.py tests/unit/test_flet_selftest.py tests/unit/test_queue_view.py tests/unit/test_settings_view.py`
Expected: clean.

- [ ] **Step 3: Run `.venv/bin/python -m flet_gui.app --selftest`**
Expected: exit 0.
