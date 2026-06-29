"""Local, free "Whisk-style" character remixer: keep Kinnu's identity (from a single
reference image) while changing her pose / action / scene via a text prompt.

Built on the same 8 GB-safe SDXL setup as imagegen/sdxl.py, plus IP-Adapter (image
prompting, no training). This is an ASSET / STILLS factory — thumbnails, posters,
"Kinnu in a scene", nicer cutout source art — NOT animation (per-frame would flicker).

Model downloads (one-time): IP-Adapter weights (~700 MB) + ViT-H image encoder (~2.5 GB).
SDXL-Turbo itself is reused from the existing cache.

Usage (see scripts/make_kinnu_stills.py for presets):
    from shiksha_cast.imagegen.ipadapter import KinnuRemixer
    rx = KinnuRemixer()
    rx.generate("assets/cartoon/source/kinnu_3d_ref.png",
                "Kinnu waving hello in a sunny garden", Path("out.png"))
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SDXL_TURBO = "stabilityai/sdxl-turbo"
SDXL_BASE = "stabilityai/stable-diffusion-xl-base-1.0"
IP_REPO = "h94/IP-Adapter"
# vit-h adapter for SDXL: lighter + better identity than the bigG default; its encoder
# lives at models/image_encoder (loaded explicitly so diffusers doesn't grab the wrong one).
IP_SUBFOLDER = "sdxl_models"
IP_WEIGHT = "ip-adapter_sdxl_vit-h.bin"
IMG_ENCODER_SUBFOLDER = "models/image_encoder"

# Anchor Kinnu's identity + exact colors in TEXT too, so IP-Adapter's strong color
# transfer (which otherwise tints the bow/shoes with the dominant yellow) is corrected.
# Tuned so the IP-Adapter keeps Kinnu ON-BRAND. Lessons (see SKILL.md):
#  - say "plain SOLID yellow dress" — "vibrant colors" in the style made a rainbow dress.
#  - put rainbow/multicolor/striped in the NEGATIVE or it invents a patterned dress.
#  - ip_scale ~0.8 keeps the yellow dress + single subject; lower (0.6) drifts off-brand.
KINNU_DESC = (
    "a cute Indian toddler girl named Kinnu, wearing a plain SOLID bright YELLOW dress, "
    "warm brown skin, black hair in a high ponytail with a small PINK bow, "
    "big round brown eyes, blue shoes"
)
DEFAULT_STYLE = (
    "Pixar-style 3D cartoon, soft toy render, smooth shading, clean, plain solid colors, "
    "studio lighting, high quality, single character, full body, centered"
)
DEFAULT_NEGATIVE = (
    "multicolor dress, rainbow dress, patterned dress, polka dots, striped dress, "
    "pink dress, blue dress, two girls, twins, duplicate, clone, multiple people, "
    "extra person, two heads, extra limbs, extra arms, deformed, mutated, blurry, "
    "low quality, text, watermark, logo, scary, realistic photo, adult, ugly, distorted face"
)


class KinnuRemixer:
    """SDXL-Turbo + IP-Adapter character remixer (8 GB VRAM safe via CPU offload)."""

    def __init__(self, model_id: str = SDXL_BASE, num_steps: int | None = None):
        self._pipe = None
        self._model_id = model_id
        self._is_turbo = "turbo" in model_id
        # turbo: 6 steps @ guidance 0 (no negative prompt). base: 28 steps @ CFG 6.
        self._num_steps = num_steps if num_steps is not None else (6 if self._is_turbo else 28)
        self._default_guidance = 0.0 if self._is_turbo else 6.0

    def _load(self) -> None:
        if self._pipe is not None:
            return
        import torch
        from diffusers import AutoPipelineForText2Image
        from transformers import CLIPVisionModelWithProjection

        logger.info("Loading ViT-H image encoder for IP-Adapter ...")
        image_encoder = CLIPVisionModelWithProjection.from_pretrained(
            IP_REPO, subfolder=IMG_ENCODER_SUBFOLDER, torch_dtype=torch.float16,
        )

        logger.info("Loading SDXL pipeline %s ...", self._model_id)
        pipe = AutoPipelineForText2Image.from_pretrained(
            self._model_id, torch_dtype=torch.float16, variant="fp16",
            image_encoder=image_encoder,
        )
        pipe.set_progress_bar_config(disable=True)

        logger.info("Loading IP-Adapter weights %s ...", IP_WEIGHT)
        pipe.load_ip_adapter(IP_REPO, subfolder=IP_SUBFOLDER, weight_name=IP_WEIGHT)

        # 8 GB-safe: stream components to GPU on demand + slice the VAE.
        # NOTE: do NOT enable_attention_slicing() here -- it replaces every UNet
        # attention processor with SlicedAttnProcessor, clobbering the IP-Adapter
        # processors load_ip_adapter() installed (-> 'tuple has no attribute shape').
        # With torch 2.x the default SDPA processors are already memory-efficient.
        try:
            pipe.enable_model_cpu_offload()
            try:
                pipe.enable_vae_slicing()
            except Exception:
                pass
            logger.info("Remixer loaded with CPU offload (8 GB-safe).")
        except Exception as e:  # noqa: BLE001
            logger.warning("CPU offload unavailable (%s); using .to(cuda)", e)
            pipe = pipe.to("cuda")
        self._pipe = pipe

    def generate(
        self,
        ref_image: str | Path,
        prompt: str,
        output_path: Path,
        *,
        ip_scale: float = 0.8,
        width: int = 832,
        height: int = 1216,
        steps: int | None = None,
        guidance: float | None = None,
        seed: int = 12345,
        negative: str = DEFAULT_NEGATIVE,
        style: str = DEFAULT_STYLE,
        desc: str = KINNU_DESC,
    ) -> Path:
        self._load()
        import torch
        from PIL import Image

        ref = Image.open(ref_image).convert("RGB")
        self._pipe.set_ip_adapter_scale(ip_scale)
        # text-anchor identity + colors, then the scene/pose, then style
        full_prompt = f"{prompt}. {desc}. {style}"
        guidance = self._default_guidance if guidance is None else guidance
        gen = torch.Generator(device="cpu").manual_seed(seed)

        image = self._pipe(
            prompt=full_prompt,
            negative_prompt=negative,
            ip_adapter_image=ref,
            num_inference_steps=steps or self._num_steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=gen,
        ).images[0]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path))
        logger.info("Generated: %s", output_path)
        return output_path

    def unload(self) -> None:
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
        except Exception:
            pass
