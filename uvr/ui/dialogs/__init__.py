"""Modal and secondary dialog windows for UVR.
"""

from __future__ import annotations

from uvr.ui.dialogs.base_dialog import BaseDialog, CTkBaseDialog
from uvr.ui.dialogs.ensemble_dialogs import (
    open_ensemble_model_settings,
    pop_up_ensemble_model_settings,
    pop_up_input_stem_name,
    pop_up_save_ensemble,
    pop_up_save_ensemble_sub_json_dump,
)
from uvr.ui.dialogs.help_dialog import (
    build_preproc_model_tab,
    build_secondary_model_tab,
    open_error_log,
    open_help_menu,
    open_manual_downloads,
)
from uvr.ui.dialogs.input_dialogs import (
    check_dual_paths,
    open_batch_dual,
    open_view_inputs,
)
from uvr.ui.dialogs.model_params import (
    pop_up_change_model_defaults,
    pop_up_mdx_c_param,
    pop_up_mdx_model,
    pop_up_mdx_model_sub_json_dump,
    pop_up_set_vocal_splitter,
    pop_up_vr_param,
    pop_up_vr_param_sub_json_dump,
)
from uvr.ui.dialogs.settings_dialog import (
    open_advanced_align_options,
    open_advanced_demucs_options,
    open_advanced_ensemble_options,
    open_advanced_mdx_options,
    open_advanced_vr_options,
    open_settings_menu,
)

__all__ = [
    "BaseDialog",
    "CTkBaseDialog",
    "build_preproc_model_tab",
    "build_secondary_model_tab",
    "check_dual_paths",
    "open_advanced_align_options",
    "open_advanced_demucs_options",
    "open_advanced_ensemble_options",
    "open_advanced_mdx_options",
    "open_advanced_vr_options",
    "open_batch_dual",
    "open_ensemble_model_settings",
    "open_error_log",
    "open_help_menu",
    "open_manual_downloads",
    "open_settings_menu",
    "open_view_inputs",
    "pop_up_change_model_defaults",
    "pop_up_ensemble_model_settings",
    "pop_up_input_stem_name",
    "pop_up_mdx_c_param",
    "pop_up_mdx_model",
    "pop_up_mdx_model_sub_json_dump",
    "pop_up_save_ensemble",
    "pop_up_save_ensemble_sub_json_dump",
    "pop_up_set_vocal_splitter",
    "pop_up_vr_param",
    "pop_up_vr_param_sub_json_dump",
]

