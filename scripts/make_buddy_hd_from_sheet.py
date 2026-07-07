"""Build the separate Buddy dog rig from the supplied sprite sheet.

Buddy is a new dog identity with its own source sheet, generated parts, demo
episode, and tests.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "cartoon" / "source" / "buddy_parts_sheet.png"
OUT = ROOT / "assets" / "cartoon" / "characters" / "buddy_hd"

INK = (42, 31, 24, 255)
FUR = (207, 115, 39, 255)
FUR_DARK = (116, 67, 38, 255)
CREAM = (249, 205, 139, 255)


def _is_checker_bg(px: tuple[int, int, int]) -> bool:
    r, g, b = px
    mx, mn = max(px), min(px)
    return mx - mn <= 12 and mx >= 218 and r >= 218 and g >= 218 and b >= 218


def _strip_connected_checker(im: Image.Image) -> Image.Image:
    """Make only exterior checkerboard pixels transparent.

    Interior white details such as eyes/teeth stay opaque because the flood fill
    starts from the crop border and cannot cross the character outline.
    """
    rgba = im.convert("RGBA")
    w, h = rgba.size
    src = rgba.load()
    seen: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not _is_checker_bg(src[x, y][:3]):
            continue
        src[x, y] = (0, 0, 0, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        return rgba
    pad = 8
    x0 = max(0, bbox[0] - pad)
    y0 = max(0, bbox[1] - pad)
    x1 = min(w, bbox[2] + pad)
    y1 = min(h, bbox[3] + pad)
    return rgba.crop((x0, y0, x1, y1))


def crop(sheet: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    return _strip_connected_checker(sheet.crop(box))


def crop_split(sheet: Image.Image, box: tuple[int, int, int, int], part: str) -> Image.Image:
    x0, y0, x1, y1 = box
    h = y1 - y0
    if part == "upper":
        return crop(sheet, (x0, y0, x1, y0 + int(h * 0.60)))
    if part == "lower":
        return crop(sheet, (x0, y0 + int(h * 0.44), x1, y1))
    raise ValueError(part)


def save(im: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f"{name}.png")


def small_cap() -> Image.Image:
    im = Image.new("RGBA", (62, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([4, 8, 58, 44], fill=INK)
    d.ellipse([9, 12, 53, 40], fill=FUR)
    return im


def neck_stub() -> Image.Image:
    im = Image.new("RGBA", (64, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([12, 6, 52, 70], radius=16, fill=INK)
    d.rounded_rectangle([17, 10, 47, 66], radius=12, fill=CREAM)
    return im


def transparent_placeholder(size: tuple[int, int] = (24, 24)) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def write_rig() -> None:
    rig = {
        "type": "skeletal",
        "scale": 0.88,
        "space": [760, 1060],
        "feet_y": 1015,
        "cx": 380,
        "joints": {
            "neck": [380, 450],
            "shoulder_left": [302, 538],
            "shoulder_right": [458, 538],
            "hip_left": [346, 668],
            "hip_right": [414, 668],
            "tail": [494, 646],
        },
        "face": {"brows": [380, 255], "eyes": [380, 300], "mouth": [380, 418]},
        "pivot": {
            "head": [0.50, 0.91],
            "torso": [0.50, 0.48],
            "upper_arm": [0.50, 0.08],
            "forearm": [0.50, 0.14],
            "thigh": [0.50, 0.08],
            "shin": [0.50, 0.14],
            "tail": [0.14, 0.78],
        },
        "bone": {"upper_arm": 0.78, "forearm": 0.0, "thigh": 0.82, "shin": 0.0},
        "neck_raise": 28,
        "torso_dy": -10,
        "render_padding": 250,
        "neck_stub": True,
        "overlay_only": True,
    }
    (OUT / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def main() -> None:
    sheet = Image.open(SOURCE).convert("RGB")
    OUT.mkdir(parents=True, exist_ok=True)

    save(crop(sheet, (40, 24, 438, 332)), "head")
    # A neutral fallback for look_back. It is intentionally not used unless a
    # scene asks for look_back.
    save(crop(sheet, (40, 24, 438, 332)), "head_back")
    save(crop(sheet, (452, 68, 690, 372)), "torso")
    save(crop(sheet, (692, 170, 795, 366)).rotate(28, resample=Image.BICUBIC, expand=True), "tail")

    arm_left = (188, 376, 300, 646)
    arm_right = (812, 378, 926, 648)
    leg_left = (204, 654, 314, 896)
    leg_right = (812, 666, 930, 898)
    save(crop_split(sheet, arm_left, "upper"), "upper_arm_left")
    save(crop_split(sheet, arm_left, "lower"), "forearm_left")
    save(crop_split(sheet, arm_right, "upper"), "upper_arm_right")
    save(crop_split(sheet, arm_right, "lower"), "forearm_right")
    save(crop_split(sheet, leg_left, "upper"), "thigh_left")
    save(crop_split(sheet, leg_left, "lower"), "shin_left")
    save(crop_split(sheet, leg_right, "upper"), "thigh_right")
    save(crop_split(sheet, leg_right, "lower"), "shin_right")
    save(small_cap(), "knee_left")
    save(small_cap(), "knee_right")
    save(neck_stub(), "neck_patch")

    # The sheet has 9 distinct snout-mouths; the rig uses 10 viseme names. The
    # talk ladder (_viseme) walks X -> B -> C -> E -> D from rest to widest, so
    # C and D MUST be different images. We map the small/medium/big openings to
    # B/C/D and park the one unavoidable duplicate on "A" (an alias the
    # animation code never selects), instead of collapsing C and D together.
    mouth_boxes = {
        "X": (12, 1226, 140, 1334),     # closed rest
        "A": (140, 1226, 270, 1334),    # small open (alias; unused by animation)
        "B": (140, 1226, 270, 1334),    # small open -> smallest talk open
        "C": (266, 1226, 400, 1338),    # medium open smile -> mid talk open
        "D": (408, 1214, 554, 1346),    # big open bark -> widest talk open
        "E": (560, 1226, 676, 1338),    # surprised O
        "F": (674, 1228, 778, 1336),    # small o
        "G": (776, 1228, 884, 1338),    # teeth grin
        "H": (876, 1228, 994, 1338),    # tongue out
        "sad": (990, 1228, 1110, 1338), # frown
    }
    for name, box in mouth_boxes.items():
        save(crop(sheet, box), f"mouth_{name}")

    # Buddy's supplied head already has eyes and brows, so these are placeholders
    # for compatibility with the shared rig tests/loader.
    for name in ("open", "closed", "happy"):
        save(transparent_placeholder(), f"eyes_{name}")
    for name in ("neutral", "happy", "sad", "surprised"):
        save(transparent_placeholder(), f"brows_{name}")

    write_rig()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
