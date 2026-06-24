from __future__ import annotations

import logging
from pathlib import Path

from shiksha_cast.tts.base import TTSProvider

logger = logging.getLogger(__name__)

# Kokoro always outputs 24 kHz audio.
KOKORO_SAMPLE_RATE = 24000


class KokoroTTSProvider(TTSProvider):
    """Kokoro-82M (Apache-2.0) — crisp, lightweight English TTS.

    Much clearer and far smaller than Parler (~330 MB vs ~8.5 GB), so it runs
    real-time on CPU and comfortably on an 8 GB GPU. Speaker is chosen by a
    preset ``voice`` name (e.g. ``af_heart``); the free-text ``description``
    used by Parler is not applicable and is ignored.
    """

    def __init__(self, voice: str = "af_heart", device: str | None = None, speed: float = 1.0):
        self._pipeline = None
        self._voice = voice or "af_heart"
        # First letter selects the language/accent pack: 'a' US English, 'b' UK English.
        self._lang_code = self._voice[0] if self._voice else "a"
        self._device = device
        self._speed = speed

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        try:
            import torch
            from kokoro import KPipeline
        except ImportError as e:
            raise ImportError(
                "Kokoro TTS not installed. Install with: pip install 'shiksha-cast[kokoro]' "
                "(or: pip install kokoro soundfile)"
            ) from e

        device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(
            "Loading Kokoro-82M (voice=%s, lang=%s) on %s...",
            self._voice,
            self._lang_code,
            device,
        )
        self._pipeline = KPipeline(lang_code=self._lang_code, device=device)
        self._device = device
        logger.info("Kokoro loaded.")

    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        import numpy as np
        import soundfile as sf

        self._load()
        assert self._pipeline is not None

        # Kokoro yields one audio chunk per sentence/segment; stitch them together.
        chunks: list = []
        for _gs, _ps, audio in self._pipeline(text, voice=self._voice, speed=self._speed):
            if audio is None:
                continue
            arr = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
            chunks.append(np.asarray(arr).squeeze())

        if chunks:
            audio_arr = np.concatenate(chunks).astype("float32")
        else:
            # Never write a zero-length file (would break the assemble step).
            audio_arr = np.zeros(int(KOKORO_SAMPLE_RATE * 0.2), dtype="float32")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), audio_arr, KOKORO_SAMPLE_RATE)

        # Release per-utterance GPU memory so fragmentation doesn't accumulate
        # across slides on a tight (8 GB) card.
        if self._device == "cuda":
            import gc

            import torch

            gc.collect()
            torch.cuda.empty_cache()

        return len(audio_arr) / KOKORO_SAMPLE_RATE

    def name(self) -> str:
        return "kokoro"
