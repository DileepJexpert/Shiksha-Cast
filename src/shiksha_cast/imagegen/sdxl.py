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
        from diffusers import DiffusionPipeline

        logger.info("Loading image model %s ...", self._model_id)
        self._pipe = DiffusionPipeline.from_pretrained(
            self._model_id,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        self._pipe.set_progress_bar_config(disable=True)

        # On an 8 GB GPU shared with desktop apps, loading the whole SDXL pipeline
        # straight to CUDA OOMs. Offload to CPU and stream components to the GPU on
        # demand (peak VRAM ~2-3 GB), with attention/VAE slicing for extra safety.
        try:
            self._pipe.enable_model_cpu_offload()
            self._pipe.enable_attention_slicing()
            try:
                self._pipe.enable_vae_slicing()
            except Exception:
                pass
            logger.info("Image model loaded with CPU offload (8 GB-safe).")
        except Exception as e:
            logger.warning("CPU offload unavailable (%s); falling back to .to(cuda)", e)
            self._pipe = self._pipe.to("cuda")

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

    def unload(self) -> None:
        """Free the model from VRAM and return cached memory to the driver.

        Critical on 8 GB GPUs: lets the (out-of-process) Veena TTS worker load
        without OOM after image generation in the same ai-build run.
        """
        if self._pipe is None:
            return
        del self._pipe
        self._pipe = None
        try:
            import gc

            import torch

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("SDXL unloaded; VRAM released.")
        except Exception:
            pass
