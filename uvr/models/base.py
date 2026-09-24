"""Base attributes, device management, and audio utility functions for models."""
from __future__ import annotations

import gc
import os
import warnings
from typing import TYPE_CHECKING

import audioread
import librosa
import numpy as np
import soundfile as sf
import torch
from scipy import signal

from gui_data.constants import *
from gui_data.error_handling import *
from lib_v5 import spec_utils
from lib_v5.vr_network import nets_new
from lib_v5.vr_network.model_param_init import ModelParameters

if TYPE_CHECKING:
    from uvr.core.model_data import ModelData

mps_available = torch.backends.mps.is_available() if is_macos else False
cuda_available = torch.cuda.is_available()
warnings.filterwarnings('ignore')
cpu = torch.device('cpu')

def clear_gpu_cache():
    gc.collect()
    if is_macos:
        torch.mps.empty_cache()
    else:
        torch.cuda.empty_cache()

class SeparateAttributes:
    def __init__(self, model_data: ModelData,
                 process_data: dict,
                 main_model_primary_stem_4_stem=None,
                 main_process_method=None,
                 is_return_dual=True,
                 main_model_primary=None,
                 vocal_stem_path=None,
                 master_inst_source=None,
                 master_vocal_source=None):

        self.list_all_models: list
        self.process_data = process_data
        self.progress_value = 0
        self.set_progress_bar = process_data['set_progress_bar']
        self.write_to_console = process_data['write_to_console']
        if vocal_stem_path:
            self.audio_file, self.audio_file_base = vocal_stem_path
            self.audio_file_base_voc_split = lambda stem, split:os.path.join(self.export_path, f'{self.audio_file_base.replace("_(Vocals)", "")}_({stem}_{split}).wav')
        else:
            self.audio_file = process_data['audio_file']
            self.audio_file_base = process_data['audio_file_base']
            self.audio_file_base_voc_split = None
        # original_audio_file is the unmodified input (before sample mode crop)
        # fall back to audio_file when not present (vocal_stem_path mode)
        self.original_audio_file = process_data.get('original_audio_file', self.audio_file)
        self.export_path = process_data['export_path']
        self.cached_source_callback = process_data['cached_source_callback']
        self.cached_model_source_holder = process_data['cached_model_source_holder']
        self.is_4_stem_ensemble = process_data['is_4_stem_ensemble']
        self.list_all_models = process_data['list_all_models']
        self.process_iteration = process_data['process_iteration']
        self.is_half_precision = process_data.get('is_half_precision', False)
        self.is_return_dual = is_return_dual
        self.is_pitch_change = model_data.is_pitch_change
        self.semitone_shift = model_data.semitone_shift
        self.is_match_frequency_pitch = model_data.is_match_frequency_pitch
        self.overlap = model_data.overlap
        self.overlap_mdx = model_data.overlap_mdx
        self.overlap_mdx23 = model_data.overlap_mdx23
        self.is_mdx_combine_stems = model_data.is_mdx_combine_stems
        self.is_mdx_c = model_data.is_mdx_c
        self.mdx_c_configs = model_data.mdx_c_configs
        self.is_roformer = getattr(model_data, 'is_roformer', False)
        self.is_scnet = getattr(model_data, 'is_scnet', False)
        self.is_mamba2 = getattr(model_data, 'is_mamba2', False)
        self.is_bandit = getattr(model_data, 'is_bandit', False)
        self.mdxnet_stem_select = model_data.mdxnet_stem_select
        self.mixer_path = model_data.mixer_path
        self.model_samplerate = model_data.model_samplerate
        self.model_capacity = model_data.model_capacity
        self.is_vr_51_model = model_data.is_vr_51_model
        self.is_pre_proc_model = model_data.is_pre_proc_model
        self.is_secondary_model_activated = model_data.is_secondary_model_activated if not self.is_pre_proc_model else False
        self.is_secondary_model = model_data.is_secondary_model if not self.is_pre_proc_model else True
        self.process_method = model_data.process_method
        self.model_path = model_data.model_path
        self.model_name = model_data.model_name
        self.model_basename = model_data.model_basename
        self.wav_type_set = model_data.wav_type_set
        self.mp3_bit_set = model_data.mp3_bit_set
        self.save_format = model_data.save_format
        self.is_gpu_conversion = model_data.is_gpu_conversion
        self.is_normalization = model_data.is_normalization
        self.is_replaygain = getattr(model_data, 'is_replaygain', False)
        self.is_primary_stem_only = model_data.is_primary_stem_only if not self.is_secondary_model else model_data.is_primary_model_primary_stem_only
        self.is_secondary_stem_only = model_data.is_secondary_stem_only if not self.is_secondary_model else model_data.is_primary_model_secondary_stem_only
        self.is_ensemble_mode = model_data.is_ensemble_mode
        self.secondary_model = model_data.secondary_model
        self.primary_model_primary_stem = model_data.primary_model_primary_stem
        self.primary_stem_native = model_data.primary_stem_native
        self.primary_stem = model_data.primary_stem
        self.secondary_stem = model_data.secondary_stem
        self.is_invert_spec = model_data.is_invert_spec
        self.is_deverb_vocals = model_data.is_deverb_vocals
        self.is_mixer_mode = model_data.is_mixer_mode
        self.secondary_model_scale = model_data.secondary_model_scale
        self.is_demucs_pre_proc_model_inst_mix = model_data.is_demucs_pre_proc_model_inst_mix
        self.primary_source_map = {}
        self.secondary_source_map = {}
        self.primary_source = None
        self.secondary_source = None
        self.secondary_source_primary = None
        self.secondary_source_secondary = None
        self.main_model_primary_stem_4_stem = main_model_primary_stem_4_stem
        self.main_model_primary = main_model_primary
        self.ensemble_primary_stem = model_data.ensemble_primary_stem
        self.is_multi_stem_ensemble = model_data.is_multi_stem_ensemble
        self.is_other_gpu = False
        self.is_deverb = True
        self.DENOISER_MODEL = model_data.DENOISER_MODEL
        self.deverber_model = model_data.deverber_model
        self.is_source_swap = False
        self.vocal_split_model = model_data.vocal_split_model
        self.is_vocal_split_model = model_data.is_vocal_split_model
        self.master_vocal_path = None
        self.set_master_inst_source = None
        self.master_inst_source = master_inst_source
        self.master_vocal_source = master_vocal_source
        self.is_save_inst_vocal_splitter = isinstance(master_inst_source, np.ndarray) and model_data.is_save_inst_vocal_splitter
        self.is_inst_only_voc_splitter = model_data.is_inst_only_voc_splitter
        self.is_karaoke = model_data.is_karaoke
        self.is_bv_model = model_data.is_bv_model
        self.is_bv_model_rebalenced = model_data.bv_model_rebalance and self.is_vocal_split_model
        self.is_bv_model_rebalanced = self.is_bv_model_rebalenced
        self.is_sec_bv_rebalance = model_data.is_sec_bv_rebalance
        self.stem_path_init = os.path.join(self.export_path, f'{self.audio_file_base}_({self.secondary_stem}).wav')
        self.deverb_vocal_opt = model_data.deverb_vocal_opt
        self.is_save_vocal_only = model_data.is_save_vocal_only
        self.device = cpu
        self.run_type = ['CPUExecutionProvider']
        self.is_opencl = False
        self.device_set = model_data.device_set
        self.is_use_opencl = model_data.is_use_opencl

        if self.is_inst_only_voc_splitter or self.is_sec_bv_rebalance:
            self.is_primary_stem_only = False
            self.is_secondary_stem_only = False

        if main_model_primary and self.is_multi_stem_ensemble:
            self.primary_stem, self.secondary_stem = main_model_primary, secondary_stem(main_model_primary)

        if self.is_gpu_conversion >= 0:
            if mps_available:
                self.device, self.is_other_gpu = 'mps', True
            else:
                device_prefix = None
                if self.device_set != DEFAULT:
                    device_prefix = CUDA_DEVICE

                if cuda_available:
                    self.device = CUDA_DEVICE if not device_prefix else f'{device_prefix}:{self.device_set}'
                    self.run_type = ['CUDAExecutionProvider']

        if model_data.process_method == MDX_ARCH_TYPE:
            self.is_mdx_ckpt = model_data.is_mdx_ckpt
            self.primary_model_name, self.primary_sources = self.cached_source_callback(MDX_ARCH_TYPE, model_name=self.model_basename)
            self.is_denoise = model_data.is_denoise
            self.is_denoise_model = model_data.is_denoise_model
            self.is_mdx_c_seg_def = model_data.is_mdx_c_seg_def
            self.mdx_batch_size = model_data.mdx_batch_size
            self.compensate = model_data.compensate
            self.mdx_segment_size = model_data.mdx_segment_size

            if self.is_mdx_c:
                if not self.is_4_stem_ensemble:
                    self.primary_stem = model_data.ensemble_primary_stem if process_data['is_ensemble_master'] else model_data.primary_stem
                    self.secondary_stem = model_data.ensemble_secondary_stem if process_data['is_ensemble_master'] else model_data.secondary_stem
            else:
                self.dim_f, self.dim_t = model_data.mdx_dim_f_set, 2**model_data.mdx_dim_t_set

            self.check_label_secondary_stem_runs()
            self.n_fft = model_data.mdx_n_fft_scale_set
            self.chunks = model_data.chunks
            self.margin = model_data.margin
            self.adjust = 1
            self.dim_c = 4
            self.hop = 1024

        if model_data.process_method == DEMUCS_ARCH_TYPE:
            self.demucs_stems = model_data.demucs_stems if main_process_method not in [MDX_ARCH_TYPE, VR_ARCH_TYPE] else None
            self.secondary_model_4_stem = model_data.secondary_model_4_stem
            self.secondary_model_4_stem_scale = model_data.secondary_model_4_stem_scale
            self.is_chunk_demucs = model_data.is_chunk_demucs
            self.segment = model_data.segment
            self.demucs_version = model_data.demucs_version
            self.demucs_source_list = model_data.demucs_source_list
            self.demucs_source_map = model_data.demucs_source_map
            self.is_demucs_combine_stems = model_data.is_demucs_combine_stems
            self.demucs_stem_count = model_data.demucs_stem_count
            self.pre_proc_model = model_data.pre_proc_model
            self.device = cpu if self.is_other_gpu and self.demucs_version not in [DEMUCS_V3, DEMUCS_V4] else self.device

            self.primary_stem = model_data.ensemble_primary_stem if process_data['is_ensemble_master'] else model_data.primary_stem
            self.secondary_stem = model_data.ensemble_secondary_stem if process_data['is_ensemble_master'] else model_data.secondary_stem

            if (self.is_multi_stem_ensemble or self.is_4_stem_ensemble) and not self.is_secondary_model:
                self.is_return_dual = False

            if self.is_multi_stem_ensemble and main_model_primary:
                self.is_4_stem_ensemble = False
                if main_model_primary in self.demucs_source_map.keys():
                    self.primary_stem = main_model_primary
                    self.secondary_stem = secondary_stem(main_model_primary)
                elif secondary_stem(main_model_primary) in self.demucs_source_map.keys():
                    self.primary_stem = secondary_stem(main_model_primary)
                    self.secondary_stem = main_model_primary

            if self.is_secondary_model and not process_data['is_ensemble_master']:
                if not self.demucs_stem_count == 2 and model_data.primary_model_primary_stem == INST_STEM:
                    self.primary_stem = VOCAL_STEM
                    self.secondary_stem = INST_STEM
                else:
                    self.primary_stem = model_data.primary_model_primary_stem
                    self.secondary_stem = secondary_stem(self.primary_stem)

            self.shifts = model_data.shifts
            self.is_split_mode = model_data.is_split_mode if not self.demucs_version == DEMUCS_V4 else True
            self.primary_model_name, self.primary_sources = self.cached_source_callback(DEMUCS_ARCH_TYPE, model_name=self.model_basename)

        if model_data.process_method == VR_ARCH_TYPE:
            self.check_label_secondary_stem_runs()
            self.primary_model_name, self.primary_sources = self.cached_source_callback(VR_ARCH_TYPE, model_name=self.model_basename)
            self.mp = model_data.vr_model_param
            self.high_end_process = model_data.is_high_end_process
            self.is_tta = model_data.is_tta
            self.is_post_process = model_data.is_post_process
            self.is_gpu_conversion = model_data.is_gpu_conversion
            self.batch_size = model_data.batch_size
            self.window_size = model_data.window_size
            self.input_high_end_h = None
            self.input_high_end = None
            self.post_process_threshold = model_data.post_process_threshold
            self.aggressiveness = {'value': model_data.aggression_setting,
                                   'split_bin': self.mp.param['band'][1]['crop_stop'],
                                   'aggr_correction': self.mp.param.get('aggr_correction')}

    def check_label_secondary_stem_runs(self):

        # For ensemble master that's not a 4-stem ensemble, and not mdx_c
        if self.process_data['is_ensemble_master'] and not self.is_4_stem_ensemble and not self.is_mdx_c:
            if self.ensemble_primary_stem != self.primary_stem:
                self.is_primary_stem_only, self.is_secondary_stem_only = self.is_secondary_stem_only, self.is_primary_stem_only

        # For secondary models
        if self.is_pre_proc_model or self.is_secondary_model:
            self.is_primary_stem_only = False
            self.is_secondary_stem_only = False

    def start_inference_console_write(self):
        if self.is_secondary_model and not self.is_pre_proc_model and not self.is_vocal_split_model:
            self.write_to_console(INFERENCE_STEP_2_SEC(self.process_method, self.model_basename))

        if self.is_pre_proc_model:
            self.write_to_console(INFERENCE_STEP_2_PRE(self.process_method, self.model_basename))

        if self.is_vocal_split_model:
            self.write_to_console(INFERENCE_STEP_2_VOC_S(self.process_method, self.model_basename))

    def running_inference_console_write(self, is_no_write=False):
        self.write_to_console(DONE, base_text='') if not is_no_write else None
        self.set_progress_bar(0.05) if not is_no_write else None

        if self.is_secondary_model and not self.is_pre_proc_model and not self.is_vocal_split_model:
            self.write_to_console(INFERENCE_STEP_1_SEC)
        elif self.is_pre_proc_model:
            self.write_to_console(INFERENCE_STEP_1_PRE)
        elif self.is_vocal_split_model:
            self.write_to_console(INFERENCE_STEP_1_VOC_S)
        else:
            self.write_to_console(INFERENCE_STEP_1)

    def running_inference_progress_bar(self, length, is_match_mix=False):
        if not is_match_mix:
            self.progress_value += 1

            if (0.8/length*self.progress_value) >= 0.8:
                length = self.progress_value + 1

            self.set_progress_bar(0.1, (0.8/length*self.progress_value))

    def load_cached_sources(self):

        if self.is_secondary_model and not self.is_pre_proc_model:
            self.write_to_console(INFERENCE_STEP_2_SEC_CACHED_MODOEL(self.process_method, self.model_basename))
        elif self.is_pre_proc_model:
            self.write_to_console(INFERENCE_STEP_2_PRE_CACHED_MODOEL(self.process_method, self.model_basename))
        else:
            self.write_to_console(INFERENCE_STEP_2_PRIMARY_CACHED, "")

    def cache_source(self, secondary_sources):

        model_occurrences = self.list_all_models.count(self.model_basename)

        if not model_occurrences <= 1:
            if self.process_method == MDX_ARCH_TYPE:
                self.cached_model_source_holder(MDX_ARCH_TYPE, secondary_sources, self.model_basename)

            if self.process_method == VR_ARCH_TYPE:
                self.cached_model_source_holder(VR_ARCH_TYPE, secondary_sources, self.model_basename)

            if self.process_method == DEMUCS_ARCH_TYPE:
                self.cached_model_source_holder(DEMUCS_ARCH_TYPE, secondary_sources, self.model_basename)

    def process_vocal_split_chain(self, sources: dict):

        def is_valid_vocal_split_condition(master_vocal_source):
            """Checks if conditions for vocal split processing are met."""
            conditions = [
                isinstance(master_vocal_source, np.ndarray),
                self.vocal_split_model,
                not self.is_ensemble_mode,
                not self.is_karaoke,
                not self.is_bv_model
            ]
            return all(conditions)

        # Retrieve sources from the dictionary with default fallbacks
        master_inst_source = sources.get(INST_STEM, None)
        master_vocal_source = sources.get(VOCAL_STEM, None)

        # Process the vocal split chain if conditions are met
        if is_valid_vocal_split_condition(master_vocal_source):
            process_chain_model(
                self.vocal_split_model,
                self.process_data,
                vocal_stem_path=self.master_vocal_path,
                master_vocal_source=master_vocal_source,
                master_inst_source=master_inst_source
            )

    def process_secondary_stem(self, stem_source, secondary_model_source=None, model_scale=None):
        if not self.is_secondary_model:
            if self.is_secondary_model_activated and isinstance(secondary_model_source, np.ndarray):
                secondary_model_scale = model_scale if model_scale else self.secondary_model_scale
                stem_source = spec_utils.average_dual_sources(stem_source, secondary_model_source, secondary_model_scale)

        return stem_source

    def final_process(self, stem_path, source, secondary_source, stem_name, samplerate):
        source = self.process_secondary_stem(source, secondary_source)
        self.write_audio(stem_path, source, samplerate, stem_name=stem_name)

        return {stem_name: source}

    def write_audio(self, stem_path: str, stem_source, samplerate, stem_name=None):

        def save_audio_file(path, source):
            source = spec_utils.normalize(source, self.is_normalization)
            sf.write(path, source, samplerate, subtype=self.wav_type_set)

            if is_not_ensemble:
                save_format(path, self.save_format, self.mp3_bit_set, self.is_replaygain, input_file_path=self.original_audio_file)

        def save_voc_split_instrumental(stem_name, stem_source, is_inst_invert=False):
            # Same karaoke stem remapping as save_voc_split_vocal
            if self.is_karaoke and self.is_vocal_split_model:
                if stem_name == VOCAL_STEM:
                    stem_name = LEAD_VOCAL_STEM
                elif stem_name == INST_STEM:
                    stem_name = BV_VOCAL_STEM
            inst_stem_name = "Instrumental (With Lead Vocals)" if stem_name == LEAD_VOCAL_STEM else "Instrumental (With Backing Vocals)"
            inst_stem_path_name = LEAD_VOCAL_STEM_I if stem_name == LEAD_VOCAL_STEM else BV_VOCAL_STEM_I
            inst_stem_path = self.audio_file_base_voc_split(INST_STEM, inst_stem_path_name)
            stem_source = -stem_source if is_inst_invert else stem_source
            inst_stem_source = spec_utils.combine_arrarys([self.master_inst_source, stem_source], is_swap=True)
            save_with_message(inst_stem_path, inst_stem_name, inst_stem_source)

        def save_voc_split_vocal(stem_name, stem_source):
            # When a karaoke model is used as vocal splitter, its output stems are named
            # 'Vocals' (lead) and 'Instrumental' (backing). Remap to the correct split
            # identifiers so filename paths use (Vocals_Lead) / (Vocals_Backing).
            if self.is_karaoke and self.is_vocal_split_model:
                if stem_name == VOCAL_STEM:
                    stem_name = LEAD_VOCAL_STEM
                elif stem_name == INST_STEM:
                    stem_name = BV_VOCAL_STEM
            voc_split_stem_name = LEAD_VOCAL_STEM_LABEL if stem_name == LEAD_VOCAL_STEM else BV_VOCAL_STEM_LABEL
            voc_split_stem_path = self.audio_file_base_voc_split(VOCAL_STEM, stem_name)
            save_with_message(voc_split_stem_path, voc_split_stem_name, stem_source)

        def save_with_message(stem_path, stem_name, stem_source):
            is_deverb = self.is_deverb_vocals and (
                self.deverb_vocal_opt == stem_name or
                (self.deverb_vocal_opt == 'ALL' and
                (stem_name == VOCAL_STEM or stem_name == LEAD_VOCAL_STEM_LABEL or stem_name == BV_VOCAL_STEM_LABEL)))

            self.write_to_console(f'{SAVING_STEM[0]}{stem_name}{SAVING_STEM[1]}')

            if is_deverb and is_not_ensemble:
                deverb_vocals(stem_path, stem_source)

            save_audio_file(stem_path, stem_source)
            self.write_to_console(DONE, base_text='')

        def deverb_vocals(stem_path:str, stem_source):
            self.write_to_console(INFERENCE_STEP_DEVERBING, base_text='')
            if self.deverber_model.process_method == VR_ARCH_TYPE:
                stem_source_deverbed, stem_source_2 = vr_denoiser(stem_source, self.device, is_deverber=True, model_path=self.deverber_model.model_path)
            elif self.deverber_model.process_method == MDX_ARCH_TYPE:
                deverber = SeperateMDXC(self.deverber_model, self.process_data) if self.deverber_model.is_mdx_c else SeperateMDX(self.deverber_model, self.process_data)
                # stem_source shape: (samples, channels) — demix expects (channels, samples)
                mix_input = stem_source.T
                raw_result = deverber.demix(mix_input)

                if isinstance(raw_result, dict):
                    # Multi-stem dict: look for the "clean" stem (first key, e.g. "No Reverb")
                    keys = list(raw_result.keys())
                    # Prefer a key that indicates a non-reverb / clean stem
                    clean_key = next((k for k in keys if 'no reverb' in k.lower() or 'clean' in k.lower() or 'deverb' in k.lower()), keys[0])
                    reverb_key = next((k for k in keys if 'reverb' in k.lower() and k != clean_key), keys[-1] if len(keys) > 1 else None)
                    stem_source_deverbed = raw_result[clean_key].T  # back to (samples, channels)
                    if reverb_key and reverb_key != clean_key:
                        stem_source_2 = raw_result[reverb_key].T
                    else:
                        stem_source_2 = stem_source - stem_source_deverbed
                else:
                    # Single numpy array
                    stem_source_deverbed = raw_result.T  # back to (samples, channels)
                    stem_source_2 = stem_source - stem_source_deverbed

                if stem_source.shape != stem_source_deverbed.shape:
                    stem_source_deverbed = spec_utils.match_array_shapes(stem_source_deverbed, stem_source)
                if stem_source.shape != stem_source_2.shape:
                    stem_source_2 = spec_utils.match_array_shapes(stem_source_2, stem_source)

            save_audio_file(stem_path.replace(".wav", "_deverbed.wav"), stem_source_deverbed)
            save_audio_file(stem_path.replace(".wav", "_reverb_only.wav"), stem_source_2)

        # For karaoke vocal splitter, remap stem_name so bv_model checks work correctly
        _eff_stem_name = stem_name
        if self.is_karaoke and self.is_vocal_split_model:
            if _eff_stem_name == VOCAL_STEM:
                _eff_stem_name = LEAD_VOCAL_STEM
            elif _eff_stem_name == INST_STEM:
                _eff_stem_name = BV_VOCAL_STEM

        is_bv_model_lead = (self.is_bv_model_rebalenced and self.is_vocal_split_model and _eff_stem_name == LEAD_VOCAL_STEM)
        is_bv_rebalance_lead = (self.is_bv_model_rebalenced and self.is_vocal_split_model and _eff_stem_name == BV_VOCAL_STEM)
        is_no_vocal_save = (self.is_inst_only_voc_splitter and (stem_name == VOCAL_STEM or stem_name == BV_VOCAL_STEM or stem_name == LEAD_VOCAL_STEM)) or is_bv_model_lead
        is_not_ensemble = (not self.is_ensemble_mode or self.is_vocal_split_model)
        is_do_not_save_inst = (self.is_save_vocal_only and self.is_sec_bv_rebalance and stem_name == INST_STEM)

        if is_bv_rebalance_lead:
            master_voc_source = spec_utils.match_array_shapes(self.master_vocal_source, stem_source, is_swap=True)
            bv_rebalance_lead_source = stem_source-master_voc_source

        if not is_bv_model_lead and not is_do_not_save_inst:
            if self.is_vocal_split_model or not self.is_secondary_model:
                if self.is_vocal_split_model and not self.is_inst_only_voc_splitter:
                    save_voc_split_vocal(stem_name, stem_source)
                    if is_bv_rebalance_lead:
                        save_voc_split_vocal(LEAD_VOCAL_STEM, bv_rebalance_lead_source)
                else:
                    if not is_no_vocal_save:
                        save_with_message(stem_path, stem_name, stem_source)

                if self.is_save_inst_vocal_splitter and not self.is_save_vocal_only:
                    save_voc_split_instrumental(stem_name, stem_source)
                    if is_bv_rebalance_lead:
                        save_voc_split_instrumental(LEAD_VOCAL_STEM, bv_rebalance_lead_source, is_inst_invert=True)

                self.set_progress_bar(0.95)

        if stem_name == VOCAL_STEM:
            self.master_vocal_path = stem_path

    def pitch_fix(self, source, sr_pitched, org_mix):
        semitone_shift = self.semitone_shift
        source = spec_utils.change_pitch_semitones(source, sr_pitched, semitone_shift=semitone_shift)[0]
        source = spec_utils.match_array_shapes(source, org_mix)
        return source

    def match_frequency_pitch(self, mix):
        source = mix
        if self.is_match_frequency_pitch and self.is_pitch_change:
            source, sr_pitched = spec_utils.change_pitch_semitones(mix, 44100, semitone_shift=-self.semitone_shift)
            source = self.pitch_fix(source, sr_pitched, mix)

        return source


SeperateAttributes = SeparateAttributes

def prepare_mix(mix):

    audio_path = mix

    if not isinstance(mix, np.ndarray):
        mix, _ = librosa.load(mix, mono=False, sr=44100)
    else:
        mix = mix.T

    if isinstance(audio_path, str):
        if not np.any(mix) and audio_path.endswith('.mp3'):
            mix = rerun_mp3(audio_path)

    if mix.ndim == 1:
        mix = np.asfortranarray([mix,mix])

    return mix

def rerun_mp3(audio_file, sample_rate=44100):

    with audioread.audio_open(audio_file) as f:
        track_length = int(f.duration)

    return librosa.load(audio_file, duration=track_length, mono=False, sr=sample_rate)[0]

def apply_replaygain(file_path):
    try:
        import math
        import os

        import mutagen
        import pydub
        from mutagen.flac import FLAC
        from mutagen.id3 import ID3, TXXX

        print(f"Applying native ReplayGain to: {file_path}")

        # Load audio to calculate loudness
        audio = pydub.AudioSegment.from_file(file_path)

        # Calculate track gain and peak
        target_dbfs = -14.0
        dbfs = audio.dBFS

        # Handle pure silence
        if math.isinf(dbfs):
            track_gain = 0.0
        else:
            track_gain = target_dbfs - dbfs

        track_peak = audio.max / audio.max_possible_amplitude

        gain_str = f"{track_gain:+.2f} dB"
        peak_str = f"{track_peak:.6f}"

        # Apply tags based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mp3':
            try:
                tags = ID3(file_path)
            except mutagen.id3.ID3NoHeaderError:
                tags = mutagen.id3.ID3()

            tags.add(TXXX(encoding=3, desc='REPLAYGAIN_TRACK_GAIN', text=gain_str))
            tags.add(TXXX(encoding=3, desc='REPLAYGAIN_TRACK_PEAK', text=peak_str))
            tags.save(file_path, v2_version=3)
        elif ext == '.flac':
            tags = FLAC(file_path)
            tags['REPLAYGAIN_TRACK_GAIN'] = gain_str
            tags['REPLAYGAIN_TRACK_PEAK'] = peak_str
            tags.save()

    except Exception as e:
        print(f"Failed to apply native ReplayGain: {e}")

def save_format(audio_path, save_format, mp3_bit_set, is_replaygain=False, input_file_path=None):

    if not save_format == WAV:

        FFMPEG_PATH = 'ffmpeg'
        if OPERATING_SYSTEM == 'Darwin':
            FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg')
            pydub.AudioSegment.converter = FFMPEG_PATH

        has_input_file = input_file_path and os.path.exists(input_file_path)

        if save_format == FLAC:
            audio_path_flac = audio_path.replace(".wav", ".flac")
            if has_input_file:
                import subprocess
                cmd = [FFMPEG_PATH, '-y', '-i', audio_path, '-i', input_file_path, '-map', '0:a', '-map', '1:v?', '-map_metadata', '1', '-c:v', 'copy', '-c:a', 'flac', audio_path_flac]
                try:
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                except Exception as e:
                    print(f"FFmpeg FLAC export failed: {e}")
                    pydub.AudioSegment.from_wav(audio_path).export(audio_path_flac, format="flac")
            else:
                pydub.AudioSegment.from_wav(audio_path).export(audio_path_flac, format="flac")

            if is_replaygain:
                apply_replaygain(audio_path_flac)

        if save_format == MP3:
            audio_path_mp3 = audio_path.replace(".wav", ".mp3")
            if has_input_file:
                import subprocess
                cmd = [FFMPEG_PATH, '-y', '-i', audio_path, '-i', input_file_path, '-map', '0:a', '-map', '1:v?', '-map_metadata', '1', '-c:v', 'copy', '-c:a', 'libmp3lame', '-b:a', mp3_bit_set, '-id3v2_version', '3', audio_path_mp3]
                try:
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                except Exception as e:
                    print(f"FFmpeg MP3 export failed: {e}")
                    try:
                        pydub.AudioSegment.from_wav(audio_path).export(audio_path_mp3, format="mp3", bitrate=mp3_bit_set, codec="libmp3lame")
                    except Exception:
                        pydub.AudioSegment.from_wav(audio_path).export(audio_path_mp3, format="mp3", bitrate=mp3_bit_set)
            else:
                try:
                    pydub.AudioSegment.from_wav(audio_path).export(audio_path_mp3, format="mp3", bitrate=mp3_bit_set, codec="libmp3lame")
                except Exception:
                    pydub.AudioSegment.from_wav(audio_path).export(audio_path_mp3, format="mp3", bitrate=mp3_bit_set)

            if is_replaygain:
                apply_replaygain(audio_path_mp3)

        try:
            os.remove(audio_path)
        except Exception as e:
            print(e)
    else:
        if is_replaygain:
            apply_replaygain(audio_path)

def pitch_shift(mix):
    new_sr = 31183

    # Resample audio file
    resampled_audio = signal.resample_poly(mix, new_sr, 44100)

    return resampled_audio

def list_to_dictionary(lst):
    dictionary = {item: index for index, item in enumerate(lst)}
    return dictionary

def vr_denoiser(X, device, hop_length=1024, n_fft=2048, cropsize=256, is_deverber=False, model_path=None):
    batchsize = 4

    if is_deverber:
        nout, nout_lstm = 64, 128
        mp = ModelParameters(os.path.join('lib_v5', 'vr_network', 'modelparams', '4band_v3.json'))
        n_fft = mp.param['bins'] * 2
    else:
        mp = None
        hop_length=1024
        nout, nout_lstm = 16, 128

    model = nets_new.CascadedNet(n_fft, nout=nout, nout_lstm=nout_lstm)
    model.load_state_dict(torch.load(model_path, map_location=cpu, weights_only=False))
    model.to(device)

    if mp is None:
        X_spec = spec_utils.wave_to_spectrogram_old(X, hop_length, n_fft)
    else:
        X_spec = loading_mix(X.T, mp)

    #PreProcess
    X_mag = np.abs(X_spec)
    X_phase = np.angle(X_spec)

    #Sep
    n_frame = X_mag.shape[2]
    pad_l, pad_r, roi_size = spec_utils.make_padding(n_frame, cropsize, model.offset)
    X_mag_pad = np.pad(X_mag, ((0, 0), (0, 0), (pad_l, pad_r)), mode='constant')
    X_mag_pad /= X_mag_pad.max()

    X_dataset = []
    patches = (X_mag_pad.shape[2] - 2 * model.offset) // roi_size
    for i in range(patches):
        start = i * roi_size
        X_mag_crop = X_mag_pad[:, :, start:start + cropsize]
        X_dataset.append(X_mag_crop)

    X_dataset = np.asarray(X_dataset)

    model.eval()

    with torch.no_grad():
        mask = []
        # To reduce the overhead, dataloader is not used.
        for i in range(0, patches, batchsize):
            X_batch = X_dataset[i: i + batchsize]
            X_batch = torch.from_numpy(X_batch).to(device)

            pred = model.predict_mask(X_batch)

            pred = pred.detach().cpu().numpy()
            pred = np.concatenate(pred, axis=2)
            mask.append(pred)

        mask = np.concatenate(mask, axis=2)

    mask = mask[:, :, :n_frame]

    #Post Proc
    if is_deverber:
        v_spec = mask * X_mag * np.exp(1.j * X_phase)
        y_spec = (1 - mask) * X_mag * np.exp(1.j * X_phase)
    else:
        v_spec = (1 - mask) * X_mag * np.exp(1.j * X_phase)

    if mp is None:
        wave = spec_utils.spectrogram_to_wave_old(v_spec, hop_length=1024)
    else:
        wave = spec_utils.cmb_spectrogram_to_wave(v_spec, mp, is_v51_model=True).T

    wave = spec_utils.match_array_shapes(wave, X)

    if is_deverber:
        wave_2 = spec_utils.cmb_spectrogram_to_wave(y_spec, mp, is_v51_model=True).T
        wave_2 = spec_utils.match_array_shapes(wave_2, X)
        return wave, wave_2
    else:
        return wave

def loading_mix(X, mp):

    X_wave, X_spec_s = {}, {}

    bands_n = len(mp.param['band'])

    for d in range(bands_n, 0, -1):
        bp = mp.param['band'][d]

        if OPERATING_SYSTEM == 'Darwin':
            wav_resolution = 'polyphase' if SYSTEM_PROC == ARM or ARM in SYSTEM_ARCH else bp['res_type']
        else:
            wav_resolution = 'polyphase'#bp['res_type']

        if d == bands_n: # high-end band
            X_wave[d] = X

        else: # lower bands
            X_wave[d] = librosa.resample(X_wave[d+1], orig_sr=mp.param['band'][d+1]['sr'], target_sr=bp['sr'], res_type=wav_resolution)

        X_spec_s[d] = spec_utils.wave_to_spectrogram(X_wave[d], bp['hl'], bp['n_fft'], mp, band=d, is_v51_model=True)

        # if d == bands_n and is_high_end_process:
        #     input_high_end_h = (bp['n_fft']//2 - bp['crop_stop']) + (mp.param['pre_filter_stop'] - mp.param['pre_filter_start'])
        #     input_high_end = X_spec_s[d][:, bp['n_fft']//2-input_high_end_h:bp['n_fft']//2, :]

    X_spec = spec_utils.combine_spectrograms(X_spec_s, mp)

    del X_wave, X_spec_s

    return X_spec
