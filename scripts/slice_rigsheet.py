"""Key out the checkerboard background of the Kinnu rig sheet and slice it into named
transparent part PNGs using a known row/column grid (gap-merge keeps 2-eyes/2-brows
together and excludes the text labels). Emits a verification montage.

Output: assets/cartoon/source/parts/<name>.png  +  parts_montage.png
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "cartoon" / "source" / "kinnu_rigsheet.png"
PARTS = ROOT / "assets" / "cartoon" / "source" / "parts"
PARTS.mkdir(parents=True, exist_ok=True)

# part-only y-bands (exclude label text) + explicit (name, x0, x1) column ranges.
ROWS = [
    (5, 326, [("torso", 40, 300), ("head", 300, 760), ("upper_arm_left", 760, 900),
              ("forearm_left", 900, 1080), ("upper_arm_right", 1080, 1280), ("forearm_right", 1280, 1460)]),
    (420, 530, [("brows_neutral", 20, 225), ("brows_happy", 225, 444), ("brows_sad", 444, 612),
                ("brows_surprised", 612, 770), ("eyes_open", 770, 995), ("eyes_closed", 995, 1227),
                ("eyes_happy", 1227, 1460)]),
    (595, 705, [("mouth_A", 30, 200), ("mouth_B", 200, 340), ("mouth_C", 340, 530), ("mouth_D", 530, 700),
                ("mouth_E", 700, 840), ("mouth_F", 840, 990), ("mouth_G", 990, 1160),
                ("mouth_H", 1160, 1310), ("mouth_X", 1310, 1460)]),
    (755, 980, [("thigh_left", 280, 440), ("shin_left", 440, 700),
                ("thigh_right", 760, 930), ("shin_right", 930, 1180)]),
]


def key_background(im):
    rgb = np.asarray(im.convert("RGB")).astype(np.int16)
    bright = rgb.max(2); sat = rgb.max(2) - rgb.min(2)
    bg_cand = (bright > 170) & (sat < 48)
    lbl, _ = ndimage.label(bg_cand)
    border = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
    border.discard(0)
    bg = np.isin(lbl, list(border))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    return np.dstack([np.asarray(im.convert("RGB")), alpha])


def runs_from_cols(present, merge_gap):
    runs = []
    i = 0
    n = len(present)
    while i < n:
        if present[i]:
            j = i
            while j < n and present[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    # merge runs separated by a small gap
    merged = [runs[0]] if runs else []
    for r in runs[1:]:
        if r[0] - merged[-1][1] < merge_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return merged


def main():
    rgba = key_background(Image.open(SRC))
    Image.fromarray(rgba, "RGBA").save(ROOT / "assets" / "cartoon" / "source" / "kinnu_keyed.png")
    alpha = rgba[..., 3]
    saved = {}
    for y0, y1, cells in ROWS:
        for name, cx0, cx1 in cells:
            sub = alpha[y0:y1, cx0:cx1]
            ys, xs = np.nonzero(sub)
            if len(ys) == 0:
                print(f"[warn] {name}: empty")
                continue
            px0, px1 = cx0 + xs.min(), cx0 + xs.max() + 1
            py0, py1 = y0 + ys.min(), y0 + ys.max() + 1
            Image.fromarray(rgba[py0:py1, px0:px1], "RGBA").save(PARTS / f"{name}.png")
            saved[name] = (px1 - px0, py1 - py0)
    print(f"saved {len(saved)} parts -> {PARTS}")

    # montage
    cols = 7
    cell = 220
    rows = (len(saved) + cols - 1) // cols
    mont = Image.new("RGBA", (cols * cell, rows * (cell + 24)), (240, 240, 245, 255))
    d = ImageDraw.Draw(mont)
    for i, (name, _) in enumerate(saved.items()):
        im = Image.open(PARTS / f"{name}.png")
        im.thumbnail((cell - 20, cell - 20))
        cx, cy = (i % cols) * cell, (i // cols) * (cell + 24)
        mont.alpha_composite(im, (cx + (cell - im.width) // 2, cy + (cell - im.height) // 2))
        d.text((cx + 6, cy + cell), name, fill=(20, 20, 30))
    mont.convert("RGB").save(ROOT / "assets" / "cartoon" / "source" / "parts_montage.png")
    print("montage -> parts_montage.png")


if __name__ == "__main__":
    main()
