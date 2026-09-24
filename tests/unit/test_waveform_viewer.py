import tkinter as tk

import numpy as np
import soundfile as sf

from uvr.ui.components.waveform_viewer import WaveformViewer


def test_waveform_viewer_load_and_clear(tmp_path):
    # Create a synthetic WAV file
    wav_path = str(tmp_path / "test.wav")
    sr = 22050
    t = np.linspace(0, 1.0, sr)
    data = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(wav_path, data, sr)

    root = tk.Tk()
    root.withdraw()
    try:
        viewer = WaveformViewer(root, width=200, height=50)
        assert viewer.load_audio(wav_path, max_points=100) is True
        assert viewer.samples is not None
        assert len(viewer.samples) == 100

        viewer.clear()
        assert viewer.audio_path is None
        assert viewer.samples is None
    finally:
        root.destroy()
