"""Give a 2D cutout character a soft 3D / toy-render LOOK by adding volume shading to the
body parts: brighten the center, darken the rim (rounded-tube shading), and add a soft
top-left highlight. Face layers (eyes/brows/mouth) are left crisp. Output is a new
character folder that drops straight into the existing 2D rig (rig2).

Usage: python scripts/make_3d_style_parts.py <src_char> <out_char> [strength]
"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
CHARS = ROOT / "assets" / "cartoon" / "characters"

# parts that get volume shading (the body); face overlays stay crisp
BODY = {"head", "torso", "upper_arm_left", "upper_arm_right", "forearm_left",
        "forearm_right", "thigh_left", "thigh_right", "shin_left", "shin_right"}


def shade(im: Image.Image, strength: float) -> Image.Image:
    im = im.convert("RGBA")
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    h, w = a.shape
    rad = max(3, int(min(h, w) / 7))
    # volume map: blurred alpha -> high in interior, low near edges
    am = Image.fromarray((a * 255).astype(np.uint8))
    vol = np.array(am.filter(ImageFilter.GaussianBlur(rad))).astype(np.float32) / 255.0
    vmax = vol.max() if vol.max() > 1e-3 else 1.0
    voln = np.clip(vol / vmax, 0, 1)
    # rounded shading: darken rim, lift center
    shade_f = (1.0 - strength * 0.5) + strength * 0.7 * voln  # ~[1-0.5s .. 1+0.2s]
    # top-left highlight: where a shifted volume exceeds the local volume
    sh = np.array(am.filter(ImageFilter.GaussianBlur(rad)))
    sh = np.roll(np.roll(sh, -int(rad * 0.6), axis=0), -int(rad * 0.6), axis=1).astype(np.float32) / 255.0
    hi = np.clip((sh / vmax) - voln, 0, 1) * strength * 90.0
    # protect dark ink outlines (don't brighten near-black pixels)
    lum = 0.3 * arr[..., 0] + 0.59 * arr[..., 1] + 0.11 * arr[..., 2]
    ink = np.clip((lum - 45) / 40.0, 0, 1)  # 0 on ink, 1 on fill
    factor = 1.0 + (shade_f - 1.0) * ink
    for c in range(3):
        arr[..., c] = np.clip(arr[..., c] * factor + hi * ink, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def main():
    if len(sys.argv) < 3:
        print("usage: make_3d_style_parts.py <src_char> <out_char> [strength]")
        return
    src = CHARS / sys.argv[1]; out = CHARS / sys.argv[2]
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.55
    out.mkdir(parents=True, exist_ok=True)
    for p in src.glob("*.png"):
        im = Image.open(p)
        if p.stem in BODY:
            im = shade(im, strength)
        im.save(out / p.name)
    meta = src / "rig2.json"
    if meta.exists():
        shutil.copy(meta, out / "rig2.json")
    print(f"{sys.argv[2]}: 3D-style shading applied (strength {strength}) -> {out}")


if __name__ == "__main__":
    main()
