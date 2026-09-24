"""MDX-C, Roformer, SCNet, BSMamba2, and Bandit separation models."""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import torch

from gui_data.constants import *
from gui_data.error_handling import *
from lib_v5 import spec_utils
from uvr.models.base import (
    SeparateAttributes,
    clear_gpu_cache,
    cpu,
    prepare_mix,
)
from uvr.models.pipeline import process_secondary_model


class SeparateMDXC(SeparateAttributes):

    def seperate(self):
        samplerate = 44100
        sources = None

        if self.primary_model_name == self.model_basename and isinstance(self.primary_sources, tuple):
            mix, sources = self.primary_sources
            self.load_cached_sources()
        else:
            self.start_inference_console_write()
            self.running_inference_console_write()
            mix = prepare_mix(self.audio_file)
            sources = self.demix(mix)
            if not self.is_vocal_split_model:
                self.cache_source((mix, sources))
            self.write_to_console(DONE, base_text='')

        stem_list = [self.mdx_c_configs.training.target_instrument] if self.mdx_c_configs.training.target_instrument else [i for i in self.mdx_c_configs.training.instruments]

        if self.is_secondary_model:
            if self.is_pre_proc_model:
                self.mdxnet_stem_select = stem_list[0]
            else:
                self.mdxnet_stem_select = self.main_model_primary_stem_4_stem if self.main_model_primary_stem_4_stem else self.primary_model_primary_stem
            self.primary_stem = self.mdxnet_stem_select
            self.secondary_stem = secondary_stem(self.mdxnet_stem_select)
            self.is_primary_stem_only, self.is_secondary_stem_only = False, False

        is_all_stems = self.mdxnet_stem_select == ALL_STEMS
        is_not_ensemble_master = not self.process_data['is_ensemble_master']
        is_not_single_stem = not len(stem_list) <= 2
        is_not_secondary_model = not self.is_secondary_model
        is_ensemble_4_stem = self.is_4_stem_ensemble and is_not_single_stem

        if (is_all_stems and is_not_ensemble_master and is_not_single_stem and is_not_secondary_model) or (is_ensemble_4_stem and not self.is_pre_proc_model):
            for stem in stem_list:
                primary_stem_path = os.path.join(self.export_path, f'{self.audio_file_base}_({stem}).wav')
                self.primary_source = sources[stem].T
                self.write_audio(primary_stem_path, self.primary_source, samplerate, stem_name=stem)

                if stem == VOCAL_STEM and not self.is_sec_bv_rebalance:
                    self.process_vocal_split_chain({VOCAL_STEM:stem})
        else:
            if len(stem_list) == 1:
                source_primary = sources[self.primary_stem] if isinstance(sources, dict) else sources
            else:
                source_primary = sources[stem_list[0]] if self.is_multi_stem_ensemble and len(stem_list) == 2 else sources[self.mdxnet_stem_select]
            if self.is_secondary_model_activated and self.secondary_model:
                self.secondary_source_primary, self.secondary_source_secondary = process_secondary_model(self.secondary_model,
                                                                                                         self.process_data,
                                                                                                         main_process_method=self.process_method,
                                                                                                         main_model_primary=self.primary_stem)

            if not self.is_primary_stem_only:
                secondary_stem_path = os.path.join(self.export_path, f'{self.audio_file_base}_({self.secondary_stem}).wav')
                if not isinstance(self.secondary_source, np.ndarray):

                    if self.is_mdx_combine_stems and len(stem_list) >= 2:
                        if len(stem_list) == 2:
                            secondary_source = sources[self.secondary_stem]
                        else:
                            sources.pop(self.primary_stem)
                            next_stem = next(iter(sources))
                            secondary_source = np.zeros_like(sources[next_stem])
                            for v in sources.values():
                                secondary_source += v

                        self.secondary_source = secondary_source.T
                    else:
                        if isinstance(sources, dict) and self.secondary_stem in sources:
                            self.secondary_source = sources[self.secondary_stem].T
                        else:
                            self.secondary_source, raw_mix = source_primary, self.match_frequency_pitch(mix)
                            self.secondary_source = spec_utils.to_shape(self.secondary_source, raw_mix.shape)

                            if self.is_invert_spec:
                                self.secondary_source = spec_utils.invert_stem(raw_mix, self.secondary_source)
                            else:
                                self.secondary_source = (-self.secondary_source.T+raw_mix.T)

                self.secondary_source_map = self.final_process(secondary_stem_path, self.secondary_source, self.secondary_source_secondary, self.secondary_stem, samplerate)

            if not self.is_secondary_stem_only:
                primary_stem_path = os.path.join(self.export_path, f'{self.audio_file_base}_({self.primary_stem}).wav')
                if not isinstance(self.primary_source, np.ndarray):
                    self.primary_source = source_primary.T

                self.primary_source_map = self.final_process(primary_stem_path, self.primary_source, self.secondary_source_primary, self.primary_stem, samplerate)

        clear_gpu_cache()

        secondary_sources = {**self.primary_source_map, **self.secondary_source_map}
        self.process_vocal_split_chain(secondary_sources)

        if self.is_secondary_model or self.is_pre_proc_model:
            return secondary_sources

    def demix(self, mix):
        sr_pitched = 441000
        org_mix = mix
        if self.is_pitch_change:
            mix, sr_pitched = spec_utils.change_pitch_semitones(mix, 44100, semitone_shift=-self.semitone_shift)

        pitch_fix = lambda s:self.pitch_fix(s, sr_pitched, org_mix)

        if getattr(self, 'is_roformer', False) or getattr(self, 'is_scnet', False) or getattr(self, 'is_mamba2', False) or getattr(self, 'is_bandit', False):
            import json
            config_dict = None

            # Default to the bundled Mini-BS-Roformer config
            config_path = os.path.join("lib_v5", "bs_roformer", "config.json")

            # Try to see if there is a specific config next to the model
            model_json = self.model_path.replace('.ckpt', '.json').replace('.safetensors', '.json').replace('.pt', '.json')
            if os.path.isfile(model_json):
                config_path = model_json
            else:
                # Try mdx_c_configs folder
                model_json_c = os.path.join("models", "MDX_Net_Models", "model_data", "mdx_c_configs", os.path.basename(model_json))
                if os.path.isfile(model_json_c):
                    config_path = model_json_c
                elif self.is_mdx_c and self.mdx_c_configs is not None:
                    config_dict = self.mdx_c_configs

            if config_dict is None:
                with open(config_path) as f:
                    if config_path.endswith('.yaml'):
                        import yaml
                        from ml_collections import ConfigDict
                        config_dict = ConfigDict(yaml.load(f, Loader=yaml.FullLoader))
                    else:
                        config_dict = json.load(f)

            if getattr(self, 'is_roformer', False):
                if hasattr(config_dict, 'model') or 'model' in config_dict:
                    # Native format (Music-Source-Separation-Training)
                    model_config = getattr(config_dict, 'model', config_dict.get('model', {}))
                    kwargs = dict(model_config)
                    if 'freqs_per_bands' in kwargs:
                        from lib_v5.roformer_native.bs_roformer import BSRoformer
                        model = BSRoformer(**kwargs)
                    else:
                        from lib_v5.roformer_native.mel_band_roformer import (
                            MelBandRoformer,
                        )
                        model = MelBandRoformer(**kwargs)
                    S = kwargs.get('num_stems', 1)
                    hop_length = kwargs.get('stft_hop_length', 441)
                    audio_config = getattr(config_dict, 'audio', config_dict.get('audio', {}))
                    wave_chunk_size = audio_config.get('chunk_size', 352800) if audio_config else 352800
                else:
                    # HuggingFace format (mini-bs-roformer)
                    from lib_v5.bs_roformer.modeling_bs_roformer import (
                        BSRoformerConfig,
                        BSRoformerForMaskedEstimation,
                    )
                    config = BSRoformerConfig(**config_dict)
                    model = BSRoformerForMaskedEstimation(config)
                    S = config.num_stems
                    hop_length = config.stft_hop_length
                    wave_chunk_size = config.wave_chunk_size
            elif getattr(self, 'is_scnet', False):
                from lib_v5.scnet.scnet import SCNet
                kwargs = dict(config_dict.model)
                model = SCNet(**kwargs)
                S = len(kwargs.get('sources', ['vocals', 'other']))
                hop_length = kwargs.get('hop_size', 1024)
                wave_chunk_size = config_dict.get('audio', {}).get('chunk_size', 485100) if hasattr(config_dict, 'get') else 485100
            elif getattr(self, 'is_mamba2', False):
                try:
                    from lib_v5.bs_mamba2.bs_mamba2 import BSMamba2Model
                except ImportError as e:
                    print(f"Failed to import mamba_ssm for Mamba2 model: {e}")
                    raise RuntimeError("Mamba2 dependencies are missing. Please install mamba_ssm, causal-conv1d, rotary_embedding_torch, and beartype.") from e
                if isinstance(config_dict, dict) and 'model' not in config_dict:
                    kwargs = config_dict
                else:
                    kwargs = dict(config_dict.model)
                model = BSMamba2Model(**kwargs)
                S = kwargs.get('num_stems', 1)
                hop_length = kwargs.get('stft_hop_length', 441)
                wave_chunk_size = config_dict.get('audio', {}).get('chunk_size', 352800) if hasattr(config_dict, 'get') else 352800
            elif getattr(self, 'is_bandit', False):
                if importlib.util.find_spec("torchaudio") is None:
                    raise RuntimeError("Bandit dependencies are missing. Please install torchaudio.")
                from lib_v5.bandit.bandit import Bandit
                kwargs = dict(config_dict.kwargs)
                model = Bandit(**kwargs)
                S = len(kwargs.get('stems', ['vocals', 'other']))
                hop_length = kwargs.get('hop_length', 512)
                wave_chunk_size = config_dict.get('audio', {}).get('chunk_size', 384000) if hasattr(config_dict, 'get') else 384000

            if self.model_path.endswith('.safetensors'):
                from lib_v5.safetensors import load_safetensors
                state_dict = load_safetensors(self.model_path)
            else:
                state_dict = torch.load(self.model_path, map_location=cpu, weights_only=False)
                if 'state_dict' in state_dict:
                    state_dict = state_dict['state_dict']

            model.load_state_dict(state_dict)
            model.to(self.device).eval()

            mix_tensor = torch.tensor(mix, dtype=torch.float32).to(self.device)

            chunk_size = wave_chunk_size if self.mdx_segment_size == 'Default' else min(hop_length * (self.mdx_segment_size - 1), wave_chunk_size)
            if self.overlap_mdx23 == 'Default':
                overlap = getattr(config_dict, 'inference', config_dict.get('inference', {})).get('num_overlap', 8) if isinstance(config_dict, dict) or hasattr(config_dict, 'inference') else 8
            else:
                overlap = self.overlap_mdx23
            overlap_size = chunk_size // overlap
            fade_size = chunk_size // 10

            import torch.nn.functional as F_torch
            window = torch.ones(chunk_size)
            window[:fade_size] = torch.linspace(0, 1, fade_size)
            window[-fade_size:] = torch.linspace(1, 0, fade_size)
            window = window.to(self.device)

            wave_length = mix_tensor.shape[-1]
            import math as math_mod
            n_chunks = math_mod.ceil(max(wave_length - chunk_size, 0) / overlap_size) + 1
            required_length = (n_chunks - 1) * overlap_size + chunk_size
            padded_wave = F_torch.pad(mix_tensor, (0, required_length - wave_length))
            unfolded = padded_wave.unfold(-1, chunk_size, overlap_size).permute(1, 0, 2)

            outputs = []
            with torch.no_grad():
                for i, chunk_batch in enumerate(unfolded.split(self.mdx_batch_size, dim=0)):
                    self.set_progress_bar(0.1 + 0.8 * (i * self.mdx_batch_size / n_chunks))
                    if hasattr(self, 'is_tta') and self.is_tta:
                        out_normal = model(chunk_batch).cpu()
                        out_inv = model(-chunk_batch).cpu()
                        out = (out_normal + (-out_inv)) / 2
                    else:
                        out = model(chunk_batch).cpu()
                    outputs.append(out)
            batch_out = torch.cat(outputs, dim=0)
            del outputs

            window_cpu = window.cpu()
            batch_out = batch_out * window_cpu
            _, num_stems, C, _ = batch_out.shape
            batch_out = batch_out.view(n_chunks, -1, chunk_size).permute(1, 2, 0)
            output_buf = F_torch.fold(batch_out, output_size=(1, required_length), kernel_size=(1, chunk_size), stride=(1, overlap_size))
            output_buf = output_buf.view(num_stems, C, -1)
            win_fold = window_cpu.expand(1, 1, -1).repeat(1, n_chunks, 1)
            weight_sum = F_torch.fold(win_fold.permute(0, 2, 1), output_size=(1, required_length), kernel_size=(1, chunk_size), stride=(1, overlap_size))
            weight_sum = weight_sum.view(1, 1, -1).clamp_min_(1e-8)
            result = (output_buf / weight_sum)[:, :, :wave_length]
            self.set_progress_bar(0.9)

            estimated_sources = result.detach().numpy()
            del model
            clear_gpu_cache()

            if S == 4:
                inst_source = estimated_sources[0] + estimated_sources[1] + estimated_sources[2]
                voc_source = estimated_sources[3]
                sources = {
                    VOCAL_STEM: pitch_fix(voc_source) if self.is_pitch_change else voc_source,
                    INST_STEM: pitch_fix(inst_source) if self.is_pitch_change else inst_source
                }
                # Also add individual stems if defined in config
                if getattr(self, 'mdx_c_configs', None) is not None and hasattr(self.mdx_c_configs, 'training') and hasattr(self.mdx_c_configs.training, 'instruments'):
                    instruments = self.mdx_c_configs.training.instruments
                    for k, v in zip(instruments, estimated_sources, strict=False):
                        sources[k] = pitch_fix(v) if self.is_pitch_change else v
                return sources
            elif S > 1:
                instruments = ["Vocals", "Instrumental"]
                if getattr(self, 'mdx_c_configs', None) is not None and hasattr(self.mdx_c_configs, 'training') and hasattr(self.mdx_c_configs.training, 'instruments'):
                    instruments = self.mdx_c_configs.training.instruments
                sources = {k: pitch_fix(v) if self.is_pitch_change else v for k, v in zip(instruments, estimated_sources, strict=False)}
                return sources
            else:
                est_s = estimated_sources[0]
                return pitch_fix(est_s) if self.is_pitch_change else est_s

        model = TFC_TDF_net(self.mdx_c_configs, device=self.device)
        model.load_state_dict(torch.load(self.model_path, map_location=cpu, weights_only=False))
        model.to(self.device).eval()
        mix = torch.tensor(mix, dtype=torch.float32)

        try:
            S = model.num_target_instruments
        except Exception:
            S = model.module.num_target_instruments

        mdx_segment_size = self.mdx_c_configs.inference.dim_t if self.mdx_segment_size == 'Default' else self.mdx_segment_size

        batch_size = self.mdx_batch_size
        chunk_size = self.mdx_c_configs.audio.hop_length * (mdx_segment_size - 1)
        if self.overlap_mdx23 == 'Default':
            overlap = getattr(self.mdx_c_configs, 'inference', self.mdx_c_configs.get('inference', {})).get('num_overlap', 8) if hasattr(self.mdx_c_configs, 'get') or hasattr(self.mdx_c_configs, 'inference') else 8
        else:
            overlap = self.overlap_mdx23

        hop_size = chunk_size // overlap
        mix_shape = mix.shape[1]
        pad_size = hop_size - (mix_shape - chunk_size) % hop_size
        mix = torch.cat([torch.zeros(2, chunk_size - hop_size), mix, torch.zeros(2, pad_size + chunk_size - hop_size)], 1)

        chunks = mix.unfold(1, chunk_size, hop_size).transpose(0, 1)
        batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]

        X = torch.zeros(S, *mix.shape) if S > 1 else torch.zeros_like(mix)
        X = X.to(self.device)

        with torch.no_grad():
            cnt = 0
            for batch in batches:
                self.running_inference_progress_bar(len(batches))
                device_type_str = self.device.type if not isinstance(self.device, str) else self.device.split(':')[0]
                with torch.autocast(device_type=device_type_str, dtype=torch.float16, enabled=self.is_half_precision and device_type_str == 'cuda'):
                    batch_pin = batch.pin_memory().to(self.device, non_blocking=True)
                    if hasattr(self, 'is_tta') and self.is_tta:
                        x_normal = model(batch_pin)
                        x_inv = model(-batch_pin)
                        x = (x_normal + (-x_inv)) / 2
                    else:
                        x = model(batch_pin)

                for w in x:
                    X[..., cnt * hop_size : cnt * hop_size + chunk_size] += w
                    cnt += 1

        estimated_sources = X[..., chunk_size - hop_size:-(pad_size + chunk_size - hop_size)] / overlap
        del X

        if S > 1:
            sources = {k: pitch_fix(v) if self.is_pitch_change else v for k, v in zip(self.mdx_c_configs.training.instruments, estimated_sources.cpu().detach().numpy(), strict=False)}
            del estimated_sources
            if self.is_denoise_model:
                if VOCAL_STEM in sources.keys() and INST_STEM in sources.keys():
                    sources[VOCAL_STEM] = vr_denoiser(sources[VOCAL_STEM], self.device, model_path=self.DENOISER_MODEL)
                    if sources[VOCAL_STEM].shape[1] != org_mix.shape[1]:
                        sources[VOCAL_STEM] = spec_utils.match_array_shapes(sources[VOCAL_STEM], org_mix)
                    sources[INST_STEM] = org_mix - sources[VOCAL_STEM]

            del model
            clear_gpu_cache()
            return sources
        else:
            est_s = estimated_sources.cpu().detach().numpy()
            del estimated_sources
            source = pitch_fix(est_s) if self.is_pitch_change else est_s

            del model
            clear_gpu_cache()
            return source


    def separate(self):
        return self.seperate()

SeperateMDXC = SeparateMDXC
