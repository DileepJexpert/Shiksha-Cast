"""Amplitude-driven viseme lip-sync for the cutout engine. Precomputes a per-frame
loudness curve for a narration WAV and maps it to a mouth state (closed/half/open).
Designed so a 9-shape Rhubarb timeline can replace `mouth_at` later with no other
changes (same return contract: a mouth-state string).
"""
from __future__ import annotations

import math

import numpy as np
import soundfile as sf


class Lipsync:
    def __init__(self, wav_path: str, fps: int):
        audio, sr = sf.read(wav_path)
        if getattr(audio, "ndim", 1) > 1:
            audio = audio.mean(axis=1)
        audio = np.asarray(audio, dtype="float32")
        self.dur = len(audio) / sr if sr else 0.0
        n = max(1, int(math.ceil(self.dur * fps)))
        win = max(1, int(sr / fps))
        v = np.array([
            float(np.sqrt(np.mean(audio[i * win:(i + 1) * win] ** 2) + 1e-9))
            if i * win < len(audio) else 0.0
            for i in range(n)
        ], dtype="float32")
        if len(v) >= 3:
            v = np.convolve(v, np.array([0.25, 0.5, 0.25], dtype="float32"), mode="same")
        p = float(np.percentile(v, 95)) if v.max() > 0 else 1.0
        self.levels = np.clip(v / (p + 1e-9), 0.0, 1.0)
        self.fps = fps

    def mouth_at(self, local_t: float) -> str:
        i = int(local_t * self.fps)
        if i < 0 or i >= len(self.levels):
            return "closed"
        lv = float(self.levels[i])
        if lv < 0.12:
            return "closed"
        if lv < 0.45:
            return "half"
        return "open"
