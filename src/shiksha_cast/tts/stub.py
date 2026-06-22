from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from shiksha_cast.tts.base import TTSProvider

WORDS_PER_SECOND = 2.5
BLIP_SECONDS = 0.2
BLIP_FREQ = 660.0
BLIP_AMPLITUDE = 0.12


class StubTTSProvider(TTSProvider):
    """Placeholder provider for testing the pipeline without a TTS model.

    Produces a clip of the right length (so video timing can be verified) with
    just a short soft blip at the start, then silence. This is NOT real voice --
    install the [tts] extra for Indic Parler-TTS narration.
    """

    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        sample_rate = 22050
        word_count = len(text.split())
        duration = max(2.0, word_count / WORDS_PER_SECOND)

        n_samples = int(sample_rate * duration)
        samples = np.zeros(n_samples, dtype=np.float32)

        # Short soft blip at the start to signal "slide audio here", then silence.
        blip_samples = min(int(sample_rate * BLIP_SECONDS), n_samples)
        t = np.linspace(0, BLIP_SECONDS, blip_samples, dtype=np.float32)
        envelope = np.sin(np.pi * np.linspace(0, 1, blip_samples, dtype=np.float32))
        samples[:blip_samples] = BLIP_AMPLITUDE * envelope * np.sin(2 * np.pi * BLIP_FREQ * t)

        pcm = (samples * 32767).astype(np.int16)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

        return duration

    def name(self) -> str:
        return "stub"
