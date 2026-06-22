from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np

from shiksha_cast.tts.base import TTSProvider

WORDS_PER_SECOND = 2.5


class StubTTSProvider(TTSProvider):
    """Generates a simple sine-wave tone sized to the narration length. For testing."""

    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        sample_rate = 22050
        word_count = len(text.split())
        duration = max(2.0, word_count / WORDS_PER_SECOND)

        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        freq = 440.0
        samples = (0.3 * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples.tobytes())

        return duration

    def name(self) -> str:
        return "stub"
