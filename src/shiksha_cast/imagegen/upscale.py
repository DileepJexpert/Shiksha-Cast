"""Local AI image upscaling on the GPU (Real-ESRGAN via spandrel).

This was the missing GPU step: backgrounds/thumbnails/character art were only
LANCZOS-resized. Real-ESRGAN reconstructs detail. We use the *anime/cartoon* 4x model
(RealESRGAN_x4plus_anime_6B) because it's tuned for clean cartoon art and is light
(6 RRDB blocks) so it fits 8 GB. Tiled inference keeps VRAM low.

spandrel is used (not the old `realesrgan` pip package) because the latter imports
torchvision.transforms.functional_tensor, removed in torchvision >= 0.17.

Usage:
    from shiksha_cast.imagegen.upscale import Upscaler
    up = Upscaler()
    up.upscale_file("in.png", "out.png", to_size=(1920, 1080))  # 4x then fit to 1080p
"""
from __future__ import annotations

import logging
import math
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = _ROOT / "assets" / "models" / "realesrgan" / "RealESRGAN_x4plus_anime_6B.pth"
MODEL_URL = ("https://github.com/xinntao/Real-ESRGAN/releases/download/"
             "v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth")


class Upscaler:
    """Real-ESRGAN upscaler (8 GB-safe via tiling). Loads lazily."""

    def __init__(self, model_path: str | Path = DEFAULT_MODEL, device: str | None = None,
                 tile: int = 512, tile_pad: int = 16):
        self.model_path = Path(model_path)
        self.device = device
        self.tile = tile
        self.tile_pad = tile_pad
        self._model = None
        self.scale = 4

    def _ensure_model_file(self) -> None:
        if self.model_path.exists():
            return
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading upscale model -> %s", self.model_path)
        urllib.request.urlretrieve(MODEL_URL, self.model_path)

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from spandrel import ModelLoader

        self._ensure_model_file()
        self.device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        m = ModelLoader().load_from_file(str(self.model_path))
        m.to(self.device).eval()
        self._model = m
        self.scale = int(getattr(m, "scale", 4))
        logger.info("Upscaler ready (%s, x%d) on %s", self.model_path.name, self.scale, self.device)

    def _run(self, tensor):
        import torch
        with torch.no_grad():
            return self._model(tensor)

    def _tiled(self, t):
        """Tile the input so a 4x of a large image fits in 8 GB."""
        import torch

        b, c, h, w = t.shape
        s = self.scale
        if self.tile <= 0 or (h <= self.tile and w <= self.tile):
            return self._run(t)
        out = torch.zeros(b, c, h * s, w * s, dtype=t.dtype, device=t.device)
        tile, pad = self.tile, self.tile_pad
        for iy in range(math.ceil(h / tile)):
            for ix in range(math.ceil(w / tile)):
                x0, y0 = ix * tile, iy * tile
                x1, y1 = min(x0 + tile, w), min(y0 + tile, h)
                px0, py0 = max(x0 - pad, 0), max(y0 - pad, 0)
                px1, py1 = min(x1 + pad, w), min(y1 + pad, h)
                op = self._run(t[:, :, py0:py1, px0:px1])
                cx0, cy0 = (x0 - px0) * s, (y0 - py0) * s
                cx1, cy1 = cx0 + (x1 - x0) * s, cy0 + (y1 - y0) * s
                out[:, :, y0 * s:y1 * s, x0 * s:x1 * s] = op[:, :, cy0:cy1, cx0:cx1]
                del op
                if self.device == "cuda":
                    torch.cuda.empty_cache()
        return out

    def upscale(self, image, to_size=None):
        """Upscale a PIL image 4x; optionally LANCZOS-fit to `to_size` (w, h)."""
        self._load()
        import numpy as np
        import torch
        from PIL import Image

        img = image.convert("RGB")
        arr = np.asarray(img).astype("float32") / 255.0
        t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(self.device)
        out = self._tiled(t)
        res = (out.clamp(0, 1).squeeze(0).permute(1, 2, 0).cpu().numpy() * 255.0)
        res = Image.fromarray(res.round().astype("uint8"))
        if to_size:
            res = res.resize(tuple(to_size), Image.LANCZOS)
        return res

    def upscale_file(self, in_path, out_path, to_size=None) -> Path:
        from PIL import Image

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.upscale(Image.open(in_path), to_size=to_size).save(str(out_path))
        logger.info("Upscaled %s -> %s", in_path, out_path)
        return out_path

    def unload(self) -> None:
        if self._model is None:
            return
        self._model = None
        try:
            import gc

            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
