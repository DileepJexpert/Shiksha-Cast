"""Slice the new transparent Indian-Kinnu rig sheet (the labeled montage from ChatGPT)
into the 26 named parts the advanced skeletal engine (rig2.py) expects, strip the text
labels under each part, and optionally recolor the peachy skin to a warm brown Indian
tone. Output: assets/cartoon/characters/<name>/ with 26 PNGs + rig2.json.

Layout assumed (left->right per row), matching the provided sheet:
  Row 1: torso, head, upper_arm_left, forearm_left, upper_arm_right, forearm_right
  Row 2: brows_neutral, brows_happy, brows_sad, brows_surprised, eyes_open, eyes_closed, eyes_happy
  Row 3: mouth_A, mouth_B, mouth_C, mouth_D, mouth_E, mouth_F, mouth_G, mouth_H, mouth_X
  Row 4: thigh_left, shin_left, thigh_right, shin_right

Usage:
  python scripts/slice_indian_sheet.py <sheet.png> [out_name] [--brown] [--montage]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

ROWS = [
    ["torso", "head", "upper_arm_left", "forearm_left", "upper_arm_right", "forearm_right"],
    ["brows_neutral", "brows_happy", "brows_sad", "brows_surprised",
     "eyes_open", "eyes_closed", "eyes_happy"],
    ["mouth_A", "mouth_B", "mouth_C", "mouth_D", "mouth_E",
     "mouth_F", "mouth_G", "mouth_H", "mouth_X"],
    ["thigh_left", "shin_left", "thigh_right", "shin_right"],
]


def _bands(mask_1d, min_gap, min_len):
    """Return [(start,end)] runs of True separated by gaps >= min_gap; drop runs < min_len."""
    idx = np.where(mask_1d)[0]
    if len(idx) == 0:
        return []
    runs, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > min_gap:
            runs.append((s, p)); s = i
        p = i
    runs.append((s, p))
    return [(a, b) for a, b in runs if b - a + 1 >= min_len]


def _strip_label(cell_alpha, cell):
    """Remove the text label: find the lowest ink band; if it's a thin strip under a clear
    gap, crop it off. Returns possibly-trimmed PIL cell."""
    rows_ink = cell_alpha.sum(axis=1) > 0
    bands = _bands(rows_ink, min_gap=4, min_len=2)
    if len(bands) >= 2:
        last_s, last_e = bands[-1]
        prev_e = bands[-2][1]
        h = cell_alpha.shape[0]
        # label heuristic: last band is short and sits in the lower third with a gap above it
        if (last_e - last_s + 1) < 0.28 * h and last_s > 0.55 * h and (last_s - prev_e) > 4:
            return cell.crop((0, 0, cell.width, last_s - 2))
    return cell


def _autocrop(im):
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def recolor_skin_brown(im, target=(176, 122, 78)):
    """Map peachy skin (high R, R>G>B, light, low-ish sat) to a warm brown, preserving shading."""
    a = np.array(im.convert("RGBA")).astype(np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    lum = (0.3 * r + 0.59 * g + 0.11 * b)
    skin = ((r > 200) & (g > 150) & (g < 235) & (b > 120) & (b < 210)
            & (r >= g) & (g >= b) & ((r - b) > 18) & (al > 0))
    ref = 210.0  # approx luminance of mid peachy skin
    for c in range(3):
        a[..., c][skin] = np.clip(target[c] * (lum / ref), 0, 255).astype(np.int16)[skin]
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    flags = {x for x in sys.argv[1:] if x.startswith("--")}
    if not args:
        print("usage: slice_indian_sheet.py <sheet.png> [out_name] [--brown] [--montage]")
        return
    sheet_path = Path(args[0])
    name = args[1] if len(args) > 1 else "kinnu_in"
    out = ROOT / "assets" / "cartoon" / "characters" / name
    out.mkdir(parents=True, exist_ok=True)

    sheet = Image.open(sheet_path).convert("RGBA")
    A = np.array(sheet)[..., 3]
    H, W = A.shape

    # --- find row bands by horizontal projection of alpha ---
    row_ink = A.sum(axis=1) > (0.002 * 255 * W)
    row_bands = _bands(row_ink, min_gap=max(10, H // 60), min_len=max(12, H // 60))
    if len(row_bands) != 4:
        print(f"[warn] found {len(row_bands)} row bands (expected 4): {row_bands}")

    saved = 0
    for ri, (ry0, ry1) in enumerate(row_bands[:4]):
        names = ROWS[ri]
        strip = A[ry0:ry1 + 1, :]
        col_ink = strip.sum(axis=0) > 0
        col_bands = _bands(col_ink, min_gap=max(8, W // 120), min_len=max(6, W // 200))
        if len(col_bands) != len(names):
            print(f"[warn] row {ri}: {len(col_bands)} cols, expected {len(names)} -> {names}")
        for ci, (cx0, cx1) in enumerate(col_bands):
            if ci >= len(names):
                break
            cell = sheet.crop((cx0, ry0, cx1 + 1, ry1 + 1))
            ca = np.array(cell)[..., 3]
            cell = _strip_label(ca, cell)
            cell = _autocrop(cell)
            cell.save(out / f"{names[ci]}.png")
            saved += 1

    if "--brown" in flags:
        for p in out.glob("*.png"):
            recolor_skin_brown(Image.open(p)).save(p)
        print("recolored skin -> brown")

    (out / "rig2.json").write_text(json.dumps({"type": "skeletal", "scale": 1.0}, indent=2))
    print(f"{name}: saved {saved}/26 parts -> {out}")

    if "--montage" in flags:
        parts = sorted(out.glob("*.png"))
        cols = 6
        rows_n = (len(parts) + cols - 1) // cols
        cw, ch = 220, 240
        m = Image.new("RGBA", (cols * cw, rows_n * ch), (200, 200, 200, 255))
        from PIL import ImageDraw
        d = ImageDraw.Draw(m)
        for i, p in enumerate(parts):
            im = Image.open(p)
            s = min(cw / im.width, (ch - 24) / im.height, 1.0)
            im = im.resize((int(im.width * s), int(im.height * s)))
            x = (i % cols) * cw + (cw - im.width) // 2
            y = (i // cols) * ch + 4
            m.alpha_composite(im, (x, y))
            d.text(((i % cols) * cw + 4, (i // cols) * ch + ch - 18), p.stem, fill=(0, 0, 0, 255))
        mp = ROOT / "dist" / f"{name}_montage.png"
        m.convert("RGB").save(mp)
        print("montage ->", mp)


if __name__ == "__main__":
    main()
