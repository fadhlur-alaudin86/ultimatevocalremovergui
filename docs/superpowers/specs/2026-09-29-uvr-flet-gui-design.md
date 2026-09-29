# UVR Flet GUI Reconstruction — Design Spec

Date: 2026-09-29
Status: Approved (chat sections 1-4)
Approach: A — Service layer + cooperative JobQueue (Flet, DeepFilterNet pattern)

## 1. Intent

Reconstruct the UVR GUI from scratch on a modern framework without losing
core separation functionality, fixing five reported GUI defects:

1. Drag and drop with multi-select and folder drop (all supported files
   inside become inputs).
2. Better, clearer UI/UX.
3. Config shown strictly per selected method (no cross-method dead options).
4. No clipped UI or overlapping buttons.
5. No redundant configs, buttons, or functions.

Plus a backend audit (excluding the legacy GUI) covering play/stop/pause
semantics and the custom Half-Precision (AMP) path.

Decisions already taken in chat: framework = Flet; architecture = service
layer + JobQueue; folder scan = recursive + supported-format filter; all
separation methods required on day one (VR, MDX/MDX-C incl. Roformer/SCNet/
Mamba2/Bandit, Demucs, Ensemble, Audio Tools); settings = clean v2 schema
with migration from legacy JSON where salvageable.

## 2. Audit findings (backend, non-GUI)

### 2.1 Half-Precision (custom AMP) — fundamentally correct, 3 hardenings

Autocast usage in `uvr/models/vr.py:153`, `uvr/models/mdx.py:195`,
`uvr/models/demucs.py:220`, `uvr/models/mdxc.py:337` follows the correct
pattern: `torch.autocast(device_type, float16, enabled=is_half and
device=='cuda')` around the model call only, weights kept in fp32, no
legacy `.half()`, no GradScaler (inference-only — correct).

Required hardenings (backend-first sprint):

1. `DeviceManager.resolve`: normalize non-CUDA `device_type` to `cpu`
   before entering autocast. String device `'mps'` with `enabled=False`
   is version-fragile.
2. Compute-capability gate per selected device, not only `cuda:0`.
   `uvr/ui/panels/options_coordinator.py:491-506` checks the default
   device; a multi-GPU `device_set` selection can bypass it.
3. `QueueTask` snapshot gap (`uvr/core/queue_manager.py:20-86`): the
   snapshot omits `is_half_precision`, `is_gpu_conversion`, `device_set`
   (and other inference-affecting flags). `process_controller.py:860-863`
   falls back to live root vars, so editing settings mid-queue mutates
   pending tasks. The new `JobSpec` must snapshot everything at enqueue.

Verified environment: GTX 1650 Max-Q, CC 7.5 (passes the >=7.0 gate),
torch 2.12+cu130, venv Python 3.11. Numeric AMP tests are runnable.

### 2.2 Stop/pause — kill-based, no mid-file control, no cleanup

`uvr/ui/managers/queue_ui.py:178-257` runs tasks in `KThread` and cancels
via `terminate()` (`queue_ui.py:287-289`, `process_controller.py:270+`).
Consequences: unsafe mid-kernel kill, leftover files in `ensemble_temps/`,
partial wavs, unreleased VRAM. Pause (`pause_resume_selected_task`) only
holds the next pending task; mid-file inference cannot pause although every
model already loops over batches/chunks/segments (VR `_execute`, MDXC batch
loop, Demucs `apply_model` segments, MDX chunks) — the natural insertion
points for cooperative checks.

Required semantics (user-confirmed): play/pause applies to selected queue
items (multi-select) and mid-file inference; pausing yields to the next
queued file while the active inference keeps priority on resume. Stop-selected
cancels + removes task(s) + deletes temps/partials. Stop-all cancels
everything + empties the worker + cleanup.

### 2.3 Redundancy and clipping — structural causes

- Flat settings (~100+ keys, `gui_data/saved_settings/*.json`) and ensemble
  files mix per-method and shared keys; Demucs duplicates the generic stem-only
  checkbox pair (`is_primary_stem_only_Demucs`).
- `options_coordinator.py:339-459` hides irrelevant widgets with
  `place(x=-1000)` on an absolute-position layout (`gui_data/app_size_values.py`).
  This is the structural root of cross-method dead configs and overlap/clipping.
  Fix: capability-driven dynamic forms on a responsive layout, never hidden
  absolute widgets.

## 3. Architecture (Section 1, approved)

New `uvr/core/service.py` is the sole backend entry: `InferenceService.submit
(JobSpec)` where `JobSpec` is a full snapshot (method, model id, all inference
flags incl. half/device/sample-mode, input list, export dir, output format).

- `JobQueue` (cooperative): each job carries `pause_event`/`cancel_event`
  checked at batch/chunk/segment boundaries in all four models plus
  `pipeline.py`. Replaces `KThread.terminate`.
- `DeviceManager`: central device selection, per-device CC gate, autocast
  normalization.
- `CapabilityRegistry`: single source of truth `method -> allowed options`.
- Flet GUI (DeepFilterNet pattern): `NavigationRail`
  (Separate / Queue / Log / Settings) + `EventBus`. Views never call models
  directly. Merged single stem-only checkbox pair.

## 4. Data flow and queue semantics (Section 2, approved)

`InputResolver`: drop of files / multi-select / folders; folders scanned
recursively; only extensions listed in the existing `ANY_EXT` constant
(`gui_data/constants.py`, covering wav/mp3/flac/ogg/m4a and alikes) become
inputs; rejected paths are logged in the Log view.

Snapshot at enqueue: later setting edits never affect pending tasks. Worker
runs one active inference at a time (single GPU); pause yields to the next
file; resume re-queues at front. Cancel paths delete `ensemble_temps/`
entries and partial wavs and release GPU cache. Progress reuses the existing
`set_progress_bar` callbacks forwarded over the `EventBus`; waveform uses
downsampled peaks as in `uvr/ui/components/waveform_viewer.py`.

## 5. Per-method config and settings (Section 3, approved)

Registry matrix:

- VR: aggression, window size, batch size, TTA, post-process + threshold,
  high-end process.
- MDX / MDX-C / Roformer / SCNet / Mamba2 / Bandit: segment size, overlap
  (`overlap_mdx`, `overlap_mdx23`), batch size, dims, TTA, denoise option.
- Demucs: model version (v1-v4), segment, shifts, overlap, split mode,
  chunk/combine options.
- Ensemble: ensemble type, main stem, model list + per-model scale, save-all
  outputs, append-name, wav-ensemble.
- Audio Tools: per-tool forms (time stretch, pitch change, align, match,
  combine, manual ensemble).

Shared options (`device`, `half`, `sample mode`, output format) always render
but `half` disables with a reason when CPU/MPS/CC<7 on the selected device.
Flet forms render dynamically from the registry on responsive `Column`/`Row`
layouts. New versioned settings schema `v2` (`{version, method, params}`);
migrator reads legacy `saved_settings/*.json` and `saved_ensembles/*.json`,
ignoring + logging unknown keys.

## 6. Error handling and testing (Section 4, approved)

Backend returns structured `JobError(code, message, hint)` (missing model,
CUDA OOM, corrupt MP3 with `rerun_mp3` fallback, missing ffmpeg); views show
actionable messages; full tracebacks go to the Log tab and `uvr.log`.

Verification:

- `DeviceManager.resolve` unit tests (mps/cpu/string devices).
- Numeric GPU tests on the available GTX 1650: each arch runs half on/off;
  assert no NaN/crash and report SNR/peak deltas.
- Snapshot test: mid-queue setting edits leave pending tasks unchanged.
- Cancel/pause tests: temp cleanup, correct terminal statuses.
- GUI `--selftest` headless view build (DeepFilterNet pattern), `ruff check`,
  `ruff format`, `pytest` green before completion claims.

## 7. Execution order

Backend-first short sprint (AMP hardening + `JobSpec` snapshot + cooperative
cancel/pause hooks + `DeviceManager` + `CapabilityRegistry` + migrator),
then Flet GUI build on the stable service contract. No parallel GUI-before-
contract work; the GUI depends on the service interface defined here.

## 8. Out of scope

Legacy Tkinter UI (`UVR.py`, `uvr/ui/*` Tk code) is frozen, not refactored.
Out-of-process/IPC backend. macOS packaging. New separation models.
