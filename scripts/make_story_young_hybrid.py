"""Build story_young_hd as a local Option-C hybrid.

This is not a full parts-sheet puppet. It uses:
  - a good SDXL front figure as a talking body
  - a good SDXL side profile as walk/run sprite
  - simple local mouth overlays for lip sync

It replaces the earlier procedural young-man rig until a true external parts
sheet is available.
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

FRONT_SOURCE = ROOT / "dist" / "_spike_story" / "man_young_full.png"
SIDE_SOURCE = ROOT / "dist" / "_spike_story" / "story_young_side_walk.png"
OUT = ROOT / "assets" / "cartoon" / "characters" / "story_young_hd"
DIST = ROOT / "dist"

SPACE = (760, 1060)
FEET_Y = 1020
CX = 380
INK = (32, 27, 24, 255)


def _bg_mask(rgb: np.ndarray) -> np.ndarray:
    mx = rgb.max(axis=2).astype(np.int16)
    mn = rgb.min(axis=2).astype(np.int16)
    avg = rgb.mean(axis=2)
    # The local SDXL sources use a grey textured/checker background. Flood-fill
    # only from the border so similar tones inside the character are preserved.
    return (avg > 118) & (avg < 235) & ((mx - mn) < 34)


def _border_connected(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y, x] or not mask[y, x]:
            continue
        seen[y, x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return seen


def _trim_alpha(im: Image.Image, pad: int = 8) -> Image.Image:
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        return im
    left, top, right, bottom = bbox
    return im.crop((
        max(0, left - pad),
        max(0, top - pad),
        min(im.width, right + pad),
        min(im.height, bottom + pad),
    ))


def strip_bg(src: Image.Image) -> Image.Image:
    rgb = np.array(src.convert("RGB"))
    bg = _border_connected(_bg_mask(rgb))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    out = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    return _trim_alpha(out)


def transparent(size: tuple[int, int] = (24, 24)) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def mouth(kind: str) -> Image.Image:
    im = Image.new("RGBA", (110, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 55, 35
    lip = (95, 45, 38, 230)
    dark = (50, 20, 24, 240)
    tongue = (190, 83, 88, 230)
    if kind == "X":
        d.arc([28, 22, 82, 50], 15, 165, fill=lip, width=4)
        return im
    if kind == "sad":
        d.arc([30, 34, 80, 64], 195, 345, fill=lip, width=4)
        return im
    sizes = {
        "A": (16, 8),
        "B": (18, 10),
        "C": (25, 15),
        "D": (33, 23),
        "E": (20, 24),
        "F": (15, 17),
        "G": (28, 12),
        "H": (29, 17),
    }
    mw, mh = sizes[kind]
    d.ellipse([cx - mw, cy - mh, cx + mw, cy + mh], fill=dark, outline=lip, width=3)
    if mh > 13:
        d.ellipse([cx - mw * 0.45, cy + 2, cx + mw * 0.45, cy + mh * 0.85], fill=tongue)
    if kind in {"D", "G"}:
        d.chord([cx - mw + 4, cy - mh + 4, cx + mw - 4, cy + 6], 180, 360, fill=(255, 245, 235, 240))
    return im


def save_rig(out: Path) -> None:
    rig = {
        "type": "skeletal",
        "scale": 0.97,
        "space": list(SPACE),
        "feet_y": FEET_Y,
        "cx": CX,
        "joints": {
            "neck": [380, 250],
            "shoulder_left": [380, 400],
            "shoulder_right": [380, 400],
            "hip_left": [380, 670],
            "hip_right": [380, 670],
        },
        "face": {"brows": [380, 205], "eyes": [380, 228], "mouth": [380, 235]},
        "pivot": {
            "head": [0.5, 0.5],
            "torso": [0.5, 0.5],
            "upper_arm": [0.5, 0.5],
            "forearm": [0.5, 0.5],
            "thigh": [0.5, 0.5],
            "shin": [0.5, 0.5],
        },
        "bone": {"upper_arm": 0.1, "forearm": 0.0, "thigh": 0.1, "shin": 0.0},
        "part_scale": {"torso": 1.0, "mouth": 0.72},
        "neck_raise": 0,
        "torso_dy": -230,
        "render_padding": 220,
        "neck_stub": False,
        "joint_caps": {"shoulder": False, "elbow": False, "knee": False},
        "overlay_only": True,
    }
    (out / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def save_manifest(out: Path) -> None:
    manifest = {
        "id": "story_young_hd",
        "display_name": "Ravi / Young Man",
        "universe": "story",
        "asset_route": "local_hybrid_talking_figure_plus_side_walk",
        "source_assets": {
            "front_talking_figure": "dist/_spike_story/man_young_full.png",
            "side_walk_reference": "dist/_spike_story/story_young_side_walk.png",
        },
        "capabilities": {
            "talk": True,
            "mouth_visemes": ["X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"],
            "front_gestures": ["idle", "talk"],
            "side_walk_sprite": True,
            "side_walk_cycle_frames": False,
        },
        "notes": [
            "Hybrid checkpoint: realistic talk plus side-walk, not a full gesture puppet.",
            "Replace with option_c_external_part_sheet when a clean separated sheet arrives.",
        ],
    }
    (out / "asset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build() -> None:
    if not FRONT_SOURCE.exists():
        raise FileNotFoundError(FRONT_SOURCE)
    if not SIDE_SOURCE.exists():
        raise FileNotFoundError(SIDE_SOURCE)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    front = strip_bg(Image.open(FRONT_SOURCE))
    front = front.resize((390, int(front.height * 390 / front.width)), Image.LANCZOS)
    front.save(OUT / "torso.png")

    side = strip_bg(Image.open(SIDE_SOURCE))
    side = side.resize((int(side.width * 940 / side.height), 940), Image.LANCZOS)
    side.save(OUT / "side_walk.png")

    # Transparent placeholders keep the shared skeletal renderer happy while the
    # full front figure is carried by torso.png.
    for name in (
        "head",
        "head_back",
        "upper_arm_left",
        "upper_arm_right",
        "forearm_left",
        "forearm_right",
        "thigh_left",
        "thigh_right",
        "shin_left",
        "shin_right",
        "knee_left",
        "knee_right",
        "eyes_open",
        "eyes_closed",
        "eyes_happy",
        "brows_neutral",
        "brows_happy",
        "brows_sad",
        "brows_surprised",
    ):
        transparent().save(OUT / f"{name}.png")
    for kind in ("X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"):
        mouth(kind).save(OUT / f"mouth_{kind}.png")
    save_rig(OUT)
    save_manifest(OUT)
    print(f"rebuilt {OUT}")


def _pose_for(action: str):
    from shiksha_cast.cartoon.build import _adv_pose

    cid = "story_young_hd"
    presets = {
        "idle": ([], 0.3, 0.70),
        "talk": ([{"who": cid, "do": "talk", "levels": [0.7] * 80, "start": 0.0, "end": 4.0}], 0.9, 0.70),
        "walk": ([{"who": cid, "do": "walkto", "to": 0.34, "start": 0.0, "end": 3.0}], 1.2, 0.70),
        "run": ([{"who": cid, "do": "runto", "to": 0.25, "start": 0.0, "end": 3.0}], 1.2, 0.70),
    }
    actions, t, x0 = presets[action]
    return _adv_pose(cid, actions, t, 15, 0.0, x0, "left")


def preview() -> None:
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter

    DIST.mkdir(exist_ok=True)
    ch = SkeletalCharacter(OUT)
    actions = ["idle", "talk", "walk", "run"]
    tw, th = 360, 500
    sheet = Image.new("RGBA", (len(actions) * tw, th), (255, 255, 255, 255))
    for idx, action in enumerate(actions):
        bg = Image.new("RGBA", (tw, th), (238, 241, 246, 255))
        pose, x_frac, facing, bob = _pose_for(action)
        ch.place(bg, pose, 0.5 if action in ("idle", "talk") else x_frac, th - 28, int(th * 0.88), facing=facing, bob=bob)
        d = ImageDraw.Draw(bg)
        try:
            font = ImageFont.truetype("arial.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        d.rectangle([0, 0, tw, 34], fill=(40, 40, 60, 255))
        d.text((10, 4), action, fill=(255, 255, 255, 255), font=font)
        d.rectangle([0, 0, tw - 1, th - 1], outline=(120, 130, 150, 255), width=2)
        sheet.alpha_composite(bg, (idx * tw, 0))
    out = DIST / "_story_young_hd_hybrid_preview.png"
    sheet.convert("RGB").save(out)
    print(f"preview -> {out}")


def main() -> None:
    build()
    preview()


if __name__ == "__main__":
    main()
