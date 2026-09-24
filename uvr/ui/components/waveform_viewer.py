"""Lightweight audio waveform visualization and preview component.
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
from typing import Any

import customtkinter as ctk
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class WaveformViewer(ctk.CTkFrame):
    """Interactive waveform display widget that downsamples and plots audio signals."""

    def __init__(
        self,
        master: Any,
        width: int = 400,
        height: int = 90,
        waveform_color: str = "#3A86FF",
        background_color: str = "#1E1E1E",
        **kwargs: Any,
    ) -> None:
        super().__init__(master, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self.waveform_color = waveform_color
        self.bg_color = background_color
        self.audio_path: str | None = None
        self.samples: np.ndarray | None = None
        self.sample_rate: int = 44100

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=background_color,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas.bind("<Configure>", self._on_resize)

        # Status text overlay
        self._status_text_id = self.canvas.create_text(
            width // 2,
            height // 2,
            text="No Audio Loaded",
            fill="#777777",
            font=("Arial", 10),
        )

    def load_audio(self, audio_path: str, max_points: int = 800) -> bool:
        """Load and downsample audio data for visualization."""
        if not os.path.isfile(audio_path):
            logger.warning("Audio file does not exist: %s", audio_path)
            return False

        try:
            data, sr = sf.read(audio_path, always_2d=True)
            self.audio_path = audio_path
            self.sample_rate = sr

            # Convert stereo to mono average
            mono = np.mean(data, axis=1)

            # Downsample to max_points
            total_samples = len(mono)
            if total_samples > max_points:
                step = total_samples // max_points
                # Calculate max amplitude per chunk
                mono = mono[: step * max_points]
                chunks = mono.reshape((max_points, step))
                peaks = np.max(np.abs(chunks), axis=1)
                self.samples = peaks
            else:
                self.samples = np.abs(mono)

            self.redraw()
            return True
        except Exception as exc:
            logger.warning("Could not read audio file %s: %s", audio_path, exc)
            return False

    def clear(self) -> None:
        """Reset waveform display."""
        self.audio_path = None
        self.samples = None
        self.canvas.delete("waveform_line")
        self.canvas.itemconfig(self._status_text_id, text="No Audio Loaded", state=tk.NORMAL)

    def redraw(self) -> None:
        """Render the waveform on the canvas."""
        self.canvas.delete("waveform_line")

        if self.samples is None or len(self.samples) == 0:
            self.canvas.itemconfig(self._status_text_id, state=tk.NORMAL)
            return

        self.canvas.itemconfig(self._status_text_id, state=tk.HIDDEN)

        w = self.canvas.winfo_width() or self.width
        h = self.canvas.winfo_height() or self.height
        mid_y = h / 2
        num_points = len(self.samples)

        # Normalize peaks to max height
        max_val = np.max(self.samples) if np.max(self.samples) > 0 else 1.0
        normalized = (self.samples / max_val) * (mid_y * 0.85)

        dx = w / max(num_points, 1)

        for i, val in enumerate(normalized):
            x = i * dx
            self.canvas.create_line(
                x,
                mid_y - val,
                x,
                mid_y + val,
                fill=self.waveform_color,
                width=max(1, int(dx)),
                tags="waveform_line",
            )

    def _on_resize(self, event: tk.Event) -> None:
        """Handle canvas resize dynamically."""
        self.width = event.width
        self.height = event.height
        self.canvas.coords(self._status_text_id, event.width // 2, event.height // 2)
        if self.samples is not None:
            self.redraw()
