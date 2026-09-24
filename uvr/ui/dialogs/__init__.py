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
from uvr.ui.dialogs.model_params import (
    pop_up_change_model_defaults,
    pop_up_mdx_c_param,
    pop_up_mdx_model,
    pop_up_mdx_model_sub_json_dump,
    pop_up_set_vocal_splitter,
    pop_up_vr_param,
    pop_up_vr_param_sub_json_dump,
)

__all__ = [
    "BaseDialog",
    "CTkBaseDialog",
    "open_ensemble_model_settings",
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
