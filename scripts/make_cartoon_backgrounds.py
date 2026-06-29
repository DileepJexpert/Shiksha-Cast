"""Generate cartoon scene BACKGROUNDS locally on the GPU (SDXL-Turbo, 8 GB-safe) into
assets/cartoon/backgrounds/. No characters -> reusable across episodes; the cutout
cast animates on top. This is the right GPU use: one-time asset generation.

Usage:
  python scripts/make_cartoon_backgrounds.py                 # all presets
  python scripts/make_cartoon_backgrounds.py night_sky classroom
  python scripts/make_cartoon_backgrounds.py "a candy land with lollipop trees"   # custom prompt
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402
from shiksha_cast.imagegen.sdxl import SDXLImageProvider  # noqa: E402

STYLE = ("flat 2D cartoon background, preschool kids cartoon style, bright cheerful colors, "
         "thick clean outlines, simple shapes, soft lighting, wide shot, empty lower foreground, "
         "no characters, no people, no text")

PRESETS = {
    "classroom": "a bright cheerful preschool classroom with a green chalkboard, colorful shelves and a window",
    "playground": "a sunny playground with swings, a slide, green grass and a blue sky with fluffy clouds",
    "home": "a cozy warm Indian living room with a sofa, a window, and potted plants",
    "garden": "a colorful garden with flowers, trees, a winding path and butterflies on a sunny day",
    "night_sky": "a magical deep blue and purple night sky full of glowing twinkling stars",
    "market": "a colorful Indian vegetable market with stalls full of fruits and vegetables",
    "classroom_full": ("a bright cheerful kindergarten classroom, big green chalkboard on the wall, "
                       "colorful alphabet and number charts, a globe and books on wooden shelves, "
                       "small student desks along the sides, large sunny windows, wooden floor"),
    "pool": ("a sunny outdoor swimming pool with clear sparkling blue water, light blue pool tiles, "
             "green palm trees and a bright blue sky with fluffy clouds, summer day"),
}

OUT = ROOT / "assets" / "cartoon" / "backgrounds"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    args = sys.argv[1:]
    # --upscale: AI-upscale (Real-ESRGAN) to 1080p instead of a plain LANCZOS resize
    use_upscale = "--upscale" in args
    args = [a for a in args if a != "--upscale"] or list(PRESETS)

    prov = SDXLImageProvider()  # SDXL-Turbo, 4 steps, CPU-offload
    raws = []  # (raw_path, final_path)
    for a in args:
        name = a if a in PRESETS else "custom_" + "".join(c for c in a.lower()[:20] if c.isalnum() or c == "_")
        prompt = PRESETS.get(a, a)
        raw = OUT / f"_{name}_raw.png"
        prov.generate(f"{prompt}, {STYLE}", raw, width=1024, height=576)
        raws.append((raw, OUT / f"{name}.png"))
    unload = getattr(prov, "unload", None)
    if unload:
        unload()  # free VRAM before the upscaler loads

    if use_upscale:
        from shiksha_cast.imagegen.upscale import Upscaler  # noqa: E402
        up = Upscaler()
        for raw, final in raws:
            up.upscale_file(raw, final, to_size=(1920, 1080))
            raw.unlink(missing_ok=True)
            print("saved (AI-upscaled)", final)
        up.unload()
    else:
        for raw, final in raws:
            Image.open(raw).convert("RGB").resize((1920, 1080), Image.LANCZOS).save(final)
            raw.unlink(missing_ok=True)
            print("saved", final)


if __name__ == "__main__":
    main()
