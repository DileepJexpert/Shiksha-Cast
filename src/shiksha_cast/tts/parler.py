from __future__ import annotations

import logging
from pathlib import Path

from shiksha_cast.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class ParlerTTSProvider(TTSProvider):
    """Indic Parler-TTS (Apache-2.0) — local GPU/CPU inference."""

    def __init__(self, model_name: str = "ai4bharat/indic-parler-tts", device: str | None = None):
        self._model = None
        self._tokenizer = None
        self._device = device
        self._model_name = model_name

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "Parler-TTS dependencies not installed. "
                "Install with: pip install 'shiksha-cast[tts]'"
            ) from e

        device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading Parler-TTS model %s on %s...", self._model_name, device)

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = ParlerTTSForConditionalGeneration.from_pretrained(self._model_name).to(device)
        self._device = device
        logger.info("Model loaded.")

    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        import soundfile as sf
        import torch

        self._load_model()
        assert self._model is not None and self._tokenizer is not None

        input_ids = self._tokenizer(description, return_tensors="pt").input_ids.to(self._device)
        prompt_ids = self._tokenizer(text, return_tensors="pt").input_ids.to(self._device)

        with torch.no_grad():
            generation = self._model.generate(input_ids=input_ids, prompt_input_ids=prompt_ids)

        audio_arr = generation.cpu().numpy().squeeze()
        sample_rate = self._model.config.sampling_rate

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), audio_arr, sample_rate)

        duration = len(audio_arr) / sample_rate

        # Release per-utterance GPU memory so fragmentation doesn't accumulate
        # across slides and OOM a tight (8 GB) card mid-build.
        del generation, input_ids, prompt_ids
        if self._device == "cuda":
            import gc

            gc.collect()
            torch.cuda.empty_cache()

        return duration

    def name(self) -> str:
        return "parler"
