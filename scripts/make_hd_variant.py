"""Make an HD cast variant by recoloring the kinnu_hd part set (dress / bow / shoes),
so we get a second advanced (skeletal) character without new art. Best for same-body
girls (e.g. Anshu). Drop in real per-character art later to fully differentiate.

Usage: python scripts/make_hd_variant.py <name> dressR,G,B bowR,G,B shoeR,G,B
"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "cartoon" / "characters" / "kinnu_hd"


def recolor(img, dress, bow, shoe):
    arr = np.array(img.convert("RGBA")).astype(np.int16)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    lum = (0.3 * r + 0.6 * g + 0.1 * b) / 255.0
    sat = arr[..., :3].max(2) - arr[..., :3].min(2)
    masks = [
        ((r > 175) & (g > 150) & (b < 140) & (a > 0), dress),   # yellow dress
        ((r > 185) & (g < 150) & (b > 95) & (b < 205) & (sat > 60) & (a > 0), bow),  # pink bow
        ((b > 150) & (r < 120) & (g < 150) & (a > 0), shoe),     # blue shoe
    ]
    for mask, target in masks:
        for c in range(3):
            arr[..., c][mask] = np.clip(target[c] * (lum + 0.15), 0, 255).astype(np.int16)[mask]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "anshu_hd"
    dress = tuple(int(x) for x in sys.argv[2].split(",")) if len(sys.argv) > 2 else (150, 90, 200)
    bow = tuple(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else (60, 190, 205)
    shoe = tuple(int(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else (235, 120, 150)
    out = ROOT / "assets" / "cartoon" / "characters" / name
    out.mkdir(parents=True, exist_ok=True)
    for p in SRC.glob("*.png"):
        recolor(Image.open(p), dress, bow, shoe).save(out / p.name)
    shutil.copy(SRC / "rig2.json", out / "rig2.json")
    print(f"{name} -> {out} ({len(list(out.glob('*.png')))} parts)")


if __name__ == "__main__":
    main()
