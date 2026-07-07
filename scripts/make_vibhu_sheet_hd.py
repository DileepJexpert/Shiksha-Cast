"""Build a separate Vibhu rig from the supplied ChatGPT-style parts sheet.

This intentionally writes a new character id, ``vibhu_sheet_hd``, so the current
``vibhu_hd`` tutorials are not disturbed while we compare the improved design.

Run:
    .venv-veena/Scripts/python.exe scripts/make_vibhu_sheet_hd.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SOURCE = ROOT / "assets" / "cartoon" / "source" / "vibhu_sheet.png"
OUT = ROOT / "assets" / "cartoon" / "characters" / "vibhu_sheet_hd"
DIST = ROOT / "dist"

TARGETS = {
    "head": (356, 368),
    "torso": (231, 236),
    "upper_arm": (64, 209),
    "forearm": (74, 212),
    "thigh": (82, 206),
    "shin": (116, 211),
    "knee": (58, 44),
    "eyes": (210, 120),
    "brows": (196, 70),
    "mouth": (150, 124),
}


def _is_checker_bg(px: tuple[int, int, int]) -> bool:
    r, g, b = px
    return max(px) - min(px) <= 16 and r >= 220 and g >= 220 and b >= 220


def _strip_connected_checker(im: Image.Image) -> Image.Image:
    """Make exterior checkerboard pixels transparent without deleting white art."""
    rgba = im.convert("RGBA")
    w, h = rgba.size
    src = rgba.load()
    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

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


def _fit_canvas(
    im: Image.Image,
    target: tuple[int, int],
    pad: int = 4,
    v_align: str = "center",
) -> Image.Image:
    """Fit a cropped part on a stable transparent canvas for the shared rig."""
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    tw, th = target
    if im.width == 0 or im.height == 0:
        return Image.new("RGBA", target, (0, 0, 0, 0))
    scale = min((tw - pad * 2) / im.width, (th - pad * 2) / im.height)
    scale = max(0.05, scale)
    rw = max(1, int(im.width * scale))
    rh = max(1, int(im.height * scale))
    resized = im.resize((rw, rh), Image.LANCZOS)
    out = Image.new("RGBA", target, (0, 0, 0, 0))
    if v_align == "top":
        y = pad
    elif v_align == "bottom":
        y = th - rh - pad
    else:
        y = (th - rh) // 2
    out.alpha_composite(resized, ((tw - rw) // 2, y))
    return out


def _crop(
    sheet: Image.Image,
    box: tuple[int, int, int, int],
    key: str,
    pad: int = 4,
    v_align: str = "center",
) -> Image.Image:
    return _fit_canvas(
        _strip_connected_checker(sheet.crop(box)),
        TARGETS[key],
        pad=pad,
        v_align=v_align,
    )


def _save(im: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f"{name}.png")


def _write_rig() -> None:
    rig = {
        "type": "skeletal",
        "scale": 0.84,
        "space": [760, 1060],
        "feet_y": 1015,
        "cx": 380,
        "joints": {
            "neck": [380, 452],
            "shoulder_left": [296, 516],
            "shoulder_right": [464, 516],
            "hip_left": [352, 648],
            "hip_right": [408, 648],
        },
        "face": {
            "brows": [380, 264],
            "eyes": [380, 315],
            "mouth": [380, 392],
        },
        "pivot": {
            "head": [0.50, 0.95],
            "torso": [0.50, 0.50],
            "upper_arm": [0.50, 0.08],
            "forearm": [0.50, 0.13],
            "thigh": [0.50, 0.08],
            "shin": [0.50, 0.13],
        },
        "bone": {
            "upper_arm": 0.68,
            "forearm": 0.0,
            "thigh": 0.44,
            "shin": 0.0,
        },
        "neck_raise": 30,
        "torso_dy": -8,
        "render_padding": 240,
    }
    (OUT / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def _build_parts() -> None:
    sheet = Image.open(SOURCE).convert("RGB")
    OUT.mkdir(parents=True, exist_ok=True)

    # Head/body/limbs.
    head = _crop(sheet, (58, 26, 474, 449), "head", pad=2)
    _save(head, "head")
    _save(head, "head_back")
    _save(_crop(sheet, (512, 145, 802, 398), "torso"), "torso")
    _save(_crop(sheet, (825, 156, 924, 397), "upper_arm", v_align="top"), "upper_arm_left")
    _save(_crop(sheet, (975, 156, 1074, 397), "upper_arm", v_align="top"), "upper_arm_right")
    _save(_crop(sheet, (49, 457, 215, 642), "forearm", v_align="top"), "forearm_left")
    _save(_crop(sheet, (359, 467, 495, 656), "forearm", v_align="top"), "forearm_right")
    _save(_crop(sheet, (576, 464, 722, 655), "thigh", v_align="top"), "thigh_left")
    _save(_crop(sheet, (897, 464, 1042, 655), "thigh", v_align="top"), "thigh_right")
    _save(_crop(sheet, (69, 677, 206, 866), "shin", v_align="top"), "shin_left")
    _save(_crop(sheet, (365, 677, 507, 866), "shin", v_align="top"), "shin_right")
    _save(_crop(sheet, (657, 764, 740, 839), "knee"), "knee_left")
    _save(_crop(sheet, (884, 764, 966, 839), "knee"), "knee_right")

    # Face overlays.
    _save(_crop(sheet, (90, 920, 320, 1030), "eyes"), "eyes_open")
    _save(_crop(sheet, (430, 930, 675, 1035), "eyes"), "eyes_closed")
    _save(_crop(sheet, (760, 960, 1005, 1035), "eyes"), "eyes_happy")

    _save(_crop(sheet, (65, 1095, 250, 1170), "brows"), "brows_neutral")
    _save(_crop(sheet, (320, 1092, 520, 1170), "brows"), "brows_happy")
    _save(_crop(sheet, (595, 1090, 785, 1170), "brows"), "brows_sad")
    _save(_crop(sheet, (855, 1090, 1035, 1170), "brows"), "brows_surprised")

    mouths = {
        "X": (72, 1266, 208, 1324),
        "A": (318, 1248, 410, 1334),
        "B": (318, 1248, 410, 1334),
        "C": (318, 1248, 410, 1334),
        "D": (490, 1230, 655, 1338),
        "E": (735, 1238, 830, 1334),
        "F": (735, 1238, 830, 1334),
        "G": (490, 1230, 655, 1338),
        "H": (490, 1230, 655, 1338),
        "sad": (910, 1258, 1035, 1322),
    }
    for name, box in mouths.items():
        _save(_crop(sheet, box, "mouth"), f"mouth_{name}")

    _write_rig()


def _pose_for(cid: str, action: str):
    from shiksha_cast.cartoon.build import _adv_pose

    presets = {
        "idle": ([], 0.3),
        "wave": ([{"who": cid, "do": "wave", "start": 0.0, "end": 3.0}], 1.2),
        "point": ([{"who": cid, "do": "point", "side": "right", "start": 0.0, "end": 3.0}], 1.2),
        "cheer": ([{"who": cid, "do": "cheer", "start": 0.0, "end": 3.0}], 1.0),
        "sad": ([{"who": cid, "do": "sad", "start": 0.0, "end": 4.0}], 1.0),
        "cry": ([{"who": cid, "do": "cry", "start": 0.0, "end": 4.0}], 0.6),
        "jump": ([{"who": cid, "do": "jump", "start": 0.0, "end": 1.2}], 0.55),
        "swim": ([{"who": cid, "do": "swimto", "to": 0.7, "start": 0.0, "end": 4.0}], 0.5),
        "look_left": ([{"who": cid, "do": "look_left", "start": 0.0, "end": 1.5}], 0.7),
        "look_right": ([{"who": cid, "do": "look_right", "start": 0.0, "end": 1.5}], 0.7),
        "look_back": ([{"who": cid, "do": "look_back", "start": 0.0, "end": 1.5}], 0.7),
    }
    actions, t = presets[action]
    return _adv_pose(cid, actions, t, 15, 0.0, 0.5, "right")


def _tile(ch, action: str, tw: int = 340, th: int = 470) -> Image.Image:
    bg = Image.new("RGBA", (tw, th), (236, 240, 247, 255))
    cid = "vibhu_sheet_hd"
    if action == "talk":
        pose = {
            "arm_left": (0, 2),
            "arm_right": (0, -2),
            "mouth": "C",
            "eyes": "open",
            "brows": "neutral",
            "head_turn": "center",
        }
        bob = 0.0
        facing = "right"
    else:
        pose, _x_cur, facing, bob = _pose_for(cid, action)
    if abs(float(pose.get("body_angle", 0.0) or 0.0)) > 0.05:
        ch.place(bg, pose, 0.5, int(th * 0.52), int(th * 0.50), facing=facing, bob=bob)
    else:
        ch.place(bg, pose, 0.5, th - 28, int(th * 0.74), facing=facing, bob=bob)

    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle([0, 0, tw, 34], fill=(40, 40, 60, 255))
    draw.text((10, 4), action, fill=(255, 255, 255, 255), font=font)
    draw.rectangle([0, 0, tw - 1, th - 1], outline=(120, 130, 150, 255), width=2)
    return bg


def _build_preview() -> None:
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter

    DIST.mkdir(exist_ok=True)
    ch = SkeletalCharacter(OUT)
    actions = [
        "idle",
        "talk",
        "wave",
        "point",
        "cheer",
        "sad",
        "cry",
        "jump",
        "swim",
        "look_left",
        "look_right",
        "look_back",
    ]
    cols = 4
    tiles = [_tile(ch, action) for action in actions]
    tw, th = tiles[0].size
    sheet = Image.new("RGBA", (cols * tw, math.ceil(len(tiles) / cols) * th), (255, 255, 255, 255))
    for idx, tile in enumerate(tiles):
        sheet.alpha_composite(tile, ((idx % cols) * tw, (idx // cols) * th))
    out = DIST / "_vibhu_sheet_rig_preview.png"
    sheet.convert("RGB").save(out)
    print(f"preview -> {out}")


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source sheet: {SOURCE}")
    _build_parts()
    print(f"wrote {OUT}")
    _build_preview()


if __name__ == "__main__":
    main()
