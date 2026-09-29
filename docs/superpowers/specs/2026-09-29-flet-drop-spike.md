# Spike: OS file-drop support in Flet 1.0.2

Verdict: native OS file/folder drop onto the window is NOT supported. `DragTarget`/`Draggable` handle in-app control drags only (payload is an in-app `src_id`, never OS paths), `Page`/`View` expose no `on_drop` event, and `FilePicker` offers `pick_files` (multi-select), `get_directory_path`, and `save_file` but no folder-contents pick.

Chosen path (fallback): a prominent DropZone control that opens `FilePicker.pick_files(allow_multiple=True)` for files and `get_directory_path` for folders (fed through `InputResolver.resolve` recursion), plus a path-paste text field. `InputResolver` remains the single funnel, so a future Flet version with native OS drop can plug in without backend changes.
