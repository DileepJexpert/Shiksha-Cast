"""Slice the 5 keyed (transparent) Kinnu-3D batch images into named rig parts via
connected components. Outputs assets/cartoon/characters/kinnu_3d/ + a verification montage.

keyed1=arms(4)  keyed2=head+torso(2)  keyed3=eyes+brows  keyed4=legs(4)  keyed5=mouths(9)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "assets" / "cartoon" / "source" / "kinnu3d_raw"
OUT = ROOT / "assets" / "cartoon" / "characters" / "kinnu_3d"
OUT.mkdir(parents=True, exist_ok=True)


def blobs(img, min_frac=0.004):
    """Return list of (cx, cy, bbox, PIL_crop) for each connected opaque region."""
    a = np.array(img.convert("RGBA"))
    mask = a[..., 3] > 40
    lbl, n = ndimage.label(mask)
    out = []
    total = mask.size
    for i in range(1, n + 1):
        ys, xs = np.where(lbl == i)
        if len(xs) < min_frac * total:
            continue
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        crop = img.crop((x0, y0, x1 + 1, y1 + 1))
        out.append({"cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2,
                    "bbox": (x0, y0, x1, y1), "img": crop})
    return out


def rows_then_cols(items, n_rows):
    """Cluster items into n_rows by cy, then sort each row by cx; return flat list."""
    items = sorted(items, key=lambda b: b["cy"])
    # simple k-row split by gaps
    per = max(1, round(len(items) / n_rows))
    rows = [items[i:i + per] for i in range(0, len(items), per)]
    flat = []
    for r in rows:
        flat.extend(sorted(r, key=lambda b: b["cx"]))
    return flat


def save(crop, name):
    crop.save(OUT / f"{name}.png")
    return name


def main():
    saved = []
    # keyed2: head + torso
    b = sorted(blobs(Image.open(RAW / "keyed2.png")), key=lambda z: z["cx"])
    saved += [save(b[0]["img"], "head"), save(b[1]["img"], "torso")]
    # keyed1: arms (L->R): upper_arm_left, forearm_left, upper_arm_right, forearm_right
    b = sorted(blobs(Image.open(RAW / "keyed1.png")), key=lambda z: z["cx"])
    for crop, nm in zip(b, ["upper_arm_left", "forearm_left", "upper_arm_right", "forearm_right"]):
        saved.append(save(crop["img"], nm))
    # keyed4: legs (L->R): thigh_left, shin_left, thigh_right, shin_right
    b = sorted(blobs(Image.open(RAW / "keyed4.png")), key=lambda z: z["cx"])
    for crop, nm in zip(b, ["thigh_left", "shin_left", "thigh_right", "shin_right"]):
        saved.append(save(crop["img"], nm))
    # keyed5: 9 mouths in a 3x3 grid -> viseme names by openness order
    b = blobs(Image.open(RAW / "keyed5.png"))
    grid = rows_then_cols(b, 3)
    mouth_names = ["mouth_B", "mouth_C", "mouth_D",     # row1: closed-smile, open-smile, big-open
                   "mouth_E", "mouth_F", "mouth_G",     # row2: aah, oh, half
                   "mouth_H", "mouth_A", "mouth_X"]     # row3: tongue, teeth, neutral/rest
    for crop, nm in zip(grid, mouth_names):
        saved.append(save(crop["img"], nm))
    # keyed3: eyes + brows (best-effort for later; group top row as eye pairs)
    eb = blobs(Image.open(RAW / "keyed3.png"))
    print(f"[info] keyed3 has {len(eb)} eye/brow blobs (saved raw for later)")

    # montage
    parts = sorted(OUT.glob("*.png"))
    cols = 6; cw, ch = 220, 240
    rows = (len(parts) + cols - 1) // cols
    m = Image.new("RGBA", (cols * cw, rows * ch), (90, 140, 180, 255)); d = ImageDraw.Draw(m)
    for i, p in enumerate(parts):
        im = Image.open(p).convert("RGBA"); im.thumbnail((cw - 12, ch - 28))
        x = (i % cols) * cw + 6; y = (i // cols) * ch + 4
        m.alpha_composite(im, (x, y)); d.text((x, y + ch - 20), p.stem, fill=(255, 255, 0, 255))
    m.convert("RGB").save(ROOT / "dist" / "_kinnu3d_parts.png")
    print(f"saved {len(saved)} parts -> {OUT}")
    print("montage -> dist/_kinnu3d_parts.png")


if __name__ == "__main__":
    main()
