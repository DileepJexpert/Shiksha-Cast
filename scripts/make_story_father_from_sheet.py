"""Build story_father_hd from a hand/art-tool character parts sheet.

The source sheet currently comes from:
    assets/cartoon/source/story_father_parts_sheet.png

It is an RGB PNG with a baked checkerboard background. This script removes that
background per crop, writes real transparent rig parts, and creates a preview.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SOURCE = ROOT / "assets" / "cartoon" / "source" / "story_father_parts_sheet.png"
SIDE_SOURCE = ROOT / "assets" / "cartoon" / "source" / "story_father_side_walk.png"
OUT = ROOT / "assets" / "cartoon" / "characters" / "story_father_hd"
DIST = ROOT / "dist"

SPACE = (760, 1060)
FEET_Y = 1030
CX = 380
SKIN = (236, 166, 104, 255)
INK = (36, 28, 25, 255)

# Crop boxes are in source-sheet pixels: left, top, right, bottom.
BOXES = {
    "head": (103, 34, 352, 324),
    "torso": (598, 116, 1005, 657),
    "upper_arm_left": (445, 200, 568, 468),
    "upper_arm_right": (1056, 198, 1182, 468),
    "forearm_left": (455, 468, 586, 738),
    "forearm_right": (1024, 468, 1155, 740),
    "thigh_left": (642, 646, 785, 914),
    "thigh_right": (809, 646, 951, 914),
    "shin_left": (594, 908, 748, 1195),
    "shin_right": (845, 908, 997, 1195),
    "eyes_open": (48, 358, 395, 425),
    "eyes_closed": (48, 590, 220, 653),
    "eyes_happy": (48, 842, 260, 900),
    "brows_neutral": (48, 336, 395, 376),
    "brows_happy": (48, 780, 265, 835),
    "brows_sad": (48, 545, 220, 596),
    "brows_surprised": (48, 1022, 260, 1082),
    "mouth_X": (374, 785, 480, 830),
    "mouth_A": (374, 835, 480, 890),
    "mouth_B": (374, 890, 480, 955),
    "mouth_C": (374, 955, 480, 1025),
    "mouth_D": (374, 1025, 480, 1085),
    "mouth_sad": (374, 1085, 480, 1145),
}

ALIASES = {
    "mouth_E": "mouth_D",
    "mouth_F": "mouth_A",
    "mouth_G": "mouth_C",
    "mouth_H": "mouth_B",
}


def _background_mask(rgb: np.ndarray) -> np.ndarray:
    mx = rgb.max(axis=2).astype(np.int16)
    mn = rgb.min(axis=2).astype(np.int16)
    avg = rgb.mean(axis=2)
    return (avg > 218) & ((mx - mn) < 24)


def _border_connected(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    return seen


def _trim_alpha(im: Image.Image, pad: int = 8) -> Image.Image:
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        return im
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(im.width, right + pad)
    bottom = min(im.height, bottom + pad)
    return im.crop((left, top, right, bottom))


def crop_part(src: Image.Image, box: tuple[int, int, int, int], *, pad: int = 10) -> Image.Image:
    left, top, right, bottom = box
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(src.width, right + pad)
    bottom = min(src.height, bottom + pad)
    crop = src.crop((left, top, right, bottom)).convert("RGB")
    rgb = np.array(crop)
    bg = _border_connected(_background_mask(rgb))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    rgba = np.dstack([rgb, alpha])
    out = Image.fromarray(rgba, "RGBA")
    return _trim_alpha(out)


def save_knee_caps(out: Path) -> None:
    for side in ("left", "right"):
        im = Image.new("RGBA", (62, 42), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([11, 10, 51, 33], fill=(49, 56, 63, 245), outline=(31, 36, 40, 210), width=2)
        im.save(out / f"knee_{side}.png")


def save_rig(out: Path) -> None:
    rig = {
        "type": "skeletal",
        "scale": 1.0,
        "space": list(SPACE),
        "feet_y": FEET_Y,
        "cx": CX,
        "joints": {
            "neck": [380, 300],
            "shoulder_left": [282, 397],
            "shoulder_right": [478, 397],
            "hip_left": [336, 655],
            "hip_right": [424, 655],
        },
        "face": {"brows": [380, 205], "eyes": [380, 252], "mouth": [380, 275]},
        "pivot": {
            "head": [0.5, 0.91],
            "torso": [0.5, 0.5],
            "upper_arm": [0.5, 0.08],
            "forearm": [0.5, 0.12],
            "thigh": [0.5, 0.06],
            "shin": [0.5, 0.11],
        },
        "bone": {"upper_arm": 0.76, "forearm": 0.0, "thigh": 0.86, "shin": 0.0},
        "part_scale": {
            "torso": 0.78,
            "head": 0.92,
            "brows": 0.56,
            "eyes": 0.56,
            "mouth": 0.76,
            "upper_arm": 0.90,
            "forearm": 0.88,
            "thigh": 0.78,
            "shin": 0.78,
        },
        "neck_raise": 0,
        "torso_dy": 10,
        "render_padding": 270,
        "neck_stub": False,
        "joint_caps": {"shoulder": False, "elbow": False, "knee": False},
        "overlay_only": True,
    }
    (out / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def save_manifest(out: Path) -> None:
    manifest = {
        "id": "story_father_hd",
        "display_name": "Papa / Suresh",
        "universe": "story",
        "asset_route": "option_c_external_part_sheet",
        "source_assets": {
            "front_parts_sheet": "assets/cartoon/source/story_father_parts_sheet.png",
            "side_walk_reference": "assets/cartoon/source/story_father_side_walk.png",
        },
        "capabilities": {
            "talk": True,
            "mouth_visemes": ["X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"],
            "front_gestures": ["idle", "talk", "wave", "point", "sad", "look_left"],
            "side_walk_sprite": True,
            "side_walk_cycle_frames": False,
        },
        "notes": [
            "Front art is used for talking and simple gestures.",
            "Side art is used for walking/running to avoid awkward front-view leg crossing.",
            (
                "Next upgrade for true walking: replace side_walk.png with "
                "4-8 same-style side cycle frames."
            ),
        ],
    }
    (out / "asset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def save_side_walk(out: Path) -> None:
    if not SIDE_SOURCE.exists():
        return
    src = Image.open(SIDE_SOURCE).convert("RGB")
    sprite = crop_part(src, (0, 0, src.width, src.height), pad=0)
    # The side art is taller than the front rig. Normalize its source size so
    # char_h_px produces the same on-screen height as the front character.
    target_h = 940
    sprite = sprite.resize((int(sprite.width * target_h / sprite.height), target_h), Image.LANCZOS)
    sprite.save(out / "side_walk.png")


def build() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    src = Image.open(SOURCE).convert("RGB")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    for name, box in BOXES.items():
        im = crop_part(src, box)
        if name == "head":
            im.save(OUT / "head_back.png")
        im.save(OUT / f"{name}.png")
    for dst, src_name in ALIASES.items():
        Image.open(OUT / f"{src_name}.png").save(OUT / f"{dst}.png")
    save_knee_caps(OUT)
    save_side_walk(OUT)
    save_rig(OUT)
    save_manifest(OUT)
    print(f"rebuilt {OUT}")


def _pose_for(action: str):
    from shiksha_cast.cartoon.build import _adv_pose

    cid = "story_father_hd"
    presets = {
        "idle": ([], 0.3, 0.30, 0.30),
        "talk": (
            [{"who": cid, "do": "talk", "levels": [0.7] * 80, "start": 0.0, "end": 4.0}],
            0.9,
            0.30,
            0.30,
        ),
        "wave": ([{"who": cid, "do": "wave", "start": 0.0, "end": 3.0}], 1.1, 0.30, 0.30),
        "point": (
            [{"who": cid, "do": "point", "side": "right", "start": 0.0, "end": 3.0}],
            1.2,
            0.30,
            0.30,
        ),
        "walk": (
            [{"who": cid, "do": "walkto", "to": 0.70, "start": 0.0, "end": 3.0}],
            1.0,
            0.28,
            0.70,
        ),
        "run": (
            [{"who": cid, "do": "runto", "to": 0.78, "start": 0.0, "end": 3.0}],
            1.0,
            0.28,
            0.78,
        ),
        "sad": ([{"who": cid, "do": "sad", "start": 0.0, "end": 3.0}], 1.0, 0.30, 0.30),
        "look_left": ([{"who": cid, "do": "look_left", "start": 0.0, "end": 2.0}], 0.8, 0.30, 0.30),
    }
    actions, t, x0, x1 = presets[action]
    return _adv_pose(cid, actions, t, 15, 0.0, x0, "right"), x1


def preview() -> None:
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter

    DIST.mkdir(exist_ok=True)
    ch = SkeletalCharacter(OUT)
    actions = ["idle", "talk", "wave", "point", "walk", "run", "sad", "look_left"]
    tw, th = 340, 470
    tiles = []
    for action in actions:
        bg = Image.new("RGBA", (tw, th), (238, 241, 246, 255))
        (pose, _x, facing, bob), x_frac = _pose_for(action)
        ch.place(bg, pose, x_frac, th - 28, int(th * 0.88), facing=facing, bob=bob)
        d = ImageDraw.Draw(bg)
        try:
            font = ImageFont.truetype("arial.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        d.rectangle([0, 0, tw, 34], fill=(40, 40, 60, 255))
        d.text((10, 4), action, fill=(255, 255, 255, 255), font=font)
        d.rectangle([0, 0, tw - 1, th - 1], outline=(120, 130, 150, 255), width=2)
        tiles.append(bg)
    sheet = Image.new("RGBA", (4 * tw, math.ceil(len(tiles) / 4) * th), (255, 255, 255, 255))
    for i, tile in enumerate(tiles):
        sheet.alpha_composite(tile, ((i % 4) * tw, (i // 4) * th))
    out = DIST / "_story_father_hd_sheet_preview.png"
    sheet.convert("RGB").save(out)
    print(f"preview -> {out}")


def main() -> None:
    build()
    preview()


if __name__ == "__main__":
    main()
