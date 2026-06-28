"""Create a cast character by recoloring the Kinnu host rig (placeholder art).

Recolors the yellow outfit to a per-character colour (keeping shading) so we have
distinct characters to drive the multi-character engine TODAY. Replace these with
real ChatGPT designs later by dropping closed/half/open.png into the character folder.

Usage:
  python scripts/make_character_variant.py <name> <R,G,B> [--bow R,G,B]
Example:
  python scripts/make_character_variant.py gappu 70,140,230
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "kinnu_rig"
OUTROOT = ROOT / "assets" / "characters"


def recolor(img: Image.Image, target, bow_target=None) -> Image.Image:
    arr = np.array(img.convert("RGBA")).astype(np.int16)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    lum = (0.3 * r + 0.6 * g + 0.1 * b) / 255.0
    # yellow outfit: high R, high G, low B
    yellow = (r > 175) & (g > 145) & (b < 130) & (a > 0)
    for c in range(3):
        arr[..., c][yellow] = np.clip(target[c] * lum, 0, 255).astype(np.int16)[yellow]
    if bow_target is not None:
        # pink bow: high R, low-ish G, mid B
        pink = (r > 190) & (g < 150) & (b > 90) & (b < 200) & (a > 0)
        for c in range(3):
            arr[..., c][pink] = np.clip(bow_target[c] * (lum + 0.2), 0, 255).astype(np.int16)[pink]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("color", help="outfit R,G,B")
    ap.add_argument("--bow", default=None, help="bow R,G,B (optional)")
    a = ap.parse_args()
    target = tuple(int(x) for x in a.color.split(","))
    bow = tuple(int(x) for x in a.bow.split(",")) if a.bow else None

    out = OUTROOT / a.name
    out.mkdir(parents=True, exist_ok=True)
    for state in ("closed", "half", "open"):
        src = SRC / f"{state}.png"
        recolor(Image.open(src), target, bow).save(out / f"{state}.png")
    json.dump(
        {"frames": {"closed": "closed.png", "half": "half.png", "open": "open.png"}},
        open(out / "rig.json", "w"), indent=2,
    )
    print(f"{a.name} -> {out}")


def register_kinnu():
    """Copy the real Kinnu rig into the cast registry as 'kinnu'."""
    out = OUTROOT / "kinnu"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("closed.png", "half.png", "open.png", "rig.json"):
        shutil.copy(SRC / f, out / f)
    print(f"kinnu -> {out}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        register_kinnu()
    else:
        main()
