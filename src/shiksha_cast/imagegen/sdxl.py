from __future__ import annotations

import logging
from pathlib import Path

from shiksha_cast.imagegen.base import ImageProvider

logger = logging.getLogger(__name__)

SDXL_TURBO = "stabilityai/sdxl-turbo"
SDXL_BASE = "stabilityai/stable-diffusion-xl-base-1.0"


class SDXLImageProvider(ImageProvider):
    """SDXL Turbo — fast image generation that fits in 8 GB VRAM."""

    def __init__(self, model_id: str = SDXL_TURBO, num_steps: int = 4):
        self._pipe = None
        self._model_id = model_id
        self._num_steps = num_steps

    def _load(self) -> None:
        if self._pipe is not None:
            return

        import torch
        from diffusers import AutoPipelineForText2Image

        logger.info("Loading image model %s ...", self._model_id)
        self._pipe = AutoPipelineForText2Image.from_pretrained(
            self._model_id,
            torch_dtype=torch.float16,
            variant="fp16",
        ).to("cuda")

        self._pipe.set_progress_bar_config(disable=True)
        logger.info("Image model loaded on CUDA.")

    def generate(self, prompt: str, output_path: Path, width: int = 1024, height: int = 576) -> Path:
        self._load()

        style_suffix = (
            ", digital illustration, educational, clean, vibrant colors, "
            "professional, high quality, 4k"
        )
        full_prompt = prompt + style_suffix

        image = self._pipe(
            prompt=full_prompt,
            num_inference_steps=self._num_steps,
            guidance_scale=0.0 if "turbo" in self._model_id else 7.5,
            width=width,
            height=height,
        ).images[0]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path))
        logger.info("Generated: %s", output_path)
        return output_path

    def name(self) -> str:
        return "sdxl"
