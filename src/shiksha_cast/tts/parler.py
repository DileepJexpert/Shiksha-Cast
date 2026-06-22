from __future__ import annotations

import logging
from pathlib import Path

from shiksha_cast.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class ParlerTTSProvider(TTSProvider):
    """Indic Parler-TTS (Apache-2.0) — local GPU/CPU inference."""

    def __init__(self, device: str | None = None):
        self._model = None
        self._tokenizer = None
        self._device = device

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
        logger.info("Loading Indic Parler-TTS on %s...", device)

        model_name = "ai4bharat/indic-parler-tts"
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = ParlerTTSForConditionalGeneration.from_pretrained(model_name).to(device)
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
        return duration

    def name(self) -> str:
        return "parler"
