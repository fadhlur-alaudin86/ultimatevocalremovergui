"""Model chaining and secondary model processing pipelines."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from gui_data.constants import *
from lib_v5 import spec_utils

if TYPE_CHECKING:
    from uvr.core.model_data import ModelData

def get_model_separator(secondary_model, process_data, **kwargs):
    from uvr.models.demucs import SeparateDemucs
    from uvr.models.mdx import SeparateMDX
    from uvr.models.mdxc import SeparateMDXC
    from uvr.models.vr import SeparateVR
    method = secondary_model.process_method
    if method == VR_ARCH_TYPE:
        return SeparateVR(secondary_model, process_data, **kwargs)
    elif method == MDX_ARCH_TYPE:
        if secondary_model.is_mdx_c:
            return SeparateMDXC(secondary_model, process_data, **kwargs)
        else:
            return SeparateMDX(secondary_model, process_data, **kwargs)
    elif method == DEMUCS_ARCH_TYPE:
        return SeparateDemucs(secondary_model, process_data, **kwargs)
    raise ValueError(f'Unknown process method: {method}')

def process_secondary_model(secondary_model: ModelData,
                            process_data,
                            main_model_primary_stem_4_stem=None,
                            is_source_load=False,
                            main_process_method=None,
                            is_pre_proc_model=False,
                            is_return_dual=True,
                            main_model_primary=None):

    if not is_pre_proc_model:
        process_iteration = process_data['process_iteration']
        process_iteration()

    if secondary_model.process_method == VR_ARCH_TYPE:
        seperator = SeperateVR(secondary_model, process_data, main_model_primary_stem_4_stem=main_model_primary_stem_4_stem, main_process_method=main_process_method, main_model_primary=main_model_primary)
    if secondary_model.process_method == MDX_ARCH_TYPE:
        if secondary_model.is_mdx_c:
            seperator = SeperateMDXC(secondary_model, process_data, main_model_primary_stem_4_stem=main_model_primary_stem_4_stem, main_process_method=main_process_method, is_return_dual=is_return_dual, main_model_primary=main_model_primary)
        else:
            seperator = SeperateMDX(secondary_model, process_data, main_model_primary_stem_4_stem=main_model_primary_stem_4_stem, main_process_method=main_process_method, main_model_primary=main_model_primary)
    if secondary_model.process_method == DEMUCS_ARCH_TYPE:
        seperator = SeperateDemucs(secondary_model, process_data, main_model_primary_stem_4_stem=main_model_primary_stem_4_stem, main_process_method=main_process_method, is_return_dual=is_return_dual, main_model_primary=main_model_primary)

    secondary_sources = seperator.seperate()

    if type(secondary_sources) is dict and not is_source_load and not is_pre_proc_model:
        return gather_sources(secondary_model.primary_model_primary_stem, secondary_stem(secondary_model.primary_model_primary_stem), secondary_sources)
    else:
        return secondary_sources

def process_chain_model(secondary_model: ModelData,
                        process_data,
                        vocal_stem_path,
                        master_vocal_source,
                        master_inst_source=None):

    process_iteration = process_data['process_iteration']
    process_iteration()

    if secondary_model.bv_model_rebalance:
        vocal_source = spec_utils.reduce_mix_bv(master_inst_source, master_vocal_source, reduction_rate=secondary_model.bv_model_rebalance)
    else:
        vocal_source = master_vocal_source

    vocal_stem_path = [vocal_source, os.path.splitext(os.path.basename(vocal_stem_path))[0]]

    if secondary_model.process_method == VR_ARCH_TYPE:
        seperator = SeperateVR(secondary_model, process_data, vocal_stem_path=vocal_stem_path, master_inst_source=master_inst_source, master_vocal_source=master_vocal_source)
    if secondary_model.process_method == MDX_ARCH_TYPE:
        if secondary_model.is_mdx_c:
            seperator = SeperateMDXC(secondary_model, process_data, vocal_stem_path=vocal_stem_path, master_inst_source=master_inst_source, master_vocal_source=master_vocal_source)
        else:
            seperator = SeperateMDX(secondary_model, process_data, vocal_stem_path=vocal_stem_path, master_inst_source=master_inst_source, master_vocal_source=master_vocal_source)
    if secondary_model.process_method == DEMUCS_ARCH_TYPE:
        seperator = SeperateDemucs(secondary_model, process_data, vocal_stem_path=vocal_stem_path, master_inst_source=master_inst_source, master_vocal_source=master_vocal_source)

    secondary_sources = seperator.seperate()

    if type(secondary_sources) is dict:
        return secondary_sources
    else:
        return None

def gather_sources(primary_stem_name, secondary_stem_name, secondary_sources: dict):

    source_primary = False
    source_secondary = False

    for key, value in secondary_sources.items():
        if key in primary_stem_name:
            source_primary = value
        if key in secondary_stem_name:
            source_secondary = value

    return source_primary, source_secondary

