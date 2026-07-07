"""Build STORY-UNIVERSE characters as true 2D cutout puppets.

The story universe is separate from Kinnu. These characters use reusable adult
human rigs with separate arms, forearms, thighs, shins, knee caps, eyes, brows,
and mouth visemes, so they can walk/run/talk with the shared cartoon renderer.

Run:
    .venv-veena/Scripts/python.exe scripts/make_story_cast.py
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CHARS = ROOT / "assets" / "cartoon" / "characters"
DIST = ROOT / "dist"
INK = (27, 28, 34, 255)
LW = 7

SPACE = (760, 1060)
FEET_Y = 1015
CX = 380
UPPER_ARM = (72, 220)
FOREARM = (78, 220)
THIGH = (86, 206)
SHIN = (122, 211)
TORSO = (260, 306)
HEAD = (312, 330)
KNEE = (58, 44)
EYES_CANVAS = (214, 118)
BROWS_CANVAS = (198, 72)
MOUTH_CANVAS = (154, 122)


@dataclass(frozen=True)
class StorySpec:
    cid: str
    skin: tuple[int, int, int, int]
    hair: tuple[int, int, int, int]
    hair_hi: tuple[int, int, int, int]
    shirt: tuple[int, int, int, int]
    shirt_dark: tuple[int, int, int, int]
    pants: tuple[int, int, int, int]
    pants_hi: tuple[int, int, int, int]
    shoe: tuple[int, int, int, int]
    sole: tuple[int, int, int, int]
    moustache: bool
    scale: float
    eye_scale: float
    mouth_y: int
    label: str


FATHER = StorySpec(
    cid="story_father_hd",
    skin=(188, 125, 82, 255),
    hair=(25, 27, 33, 255),
    hair_hi=(118, 123, 132, 255),
    shirt=(202, 169, 123, 255),
    shirt_dark=(121, 82, 55, 255),
    pants=(178, 174, 162, 255),
    pants_hi=(207, 204, 194, 255),
    shoe=(55, 44, 34, 255),
    sole=(196, 190, 178, 255),
    moustache=True,
    scale=1.0,
    eye_scale=0.92,
    mouth_y=368,
    label="father",
)

YOUNG = StorySpec(
    cid="story_young_hd",
    skin=(198, 135, 92, 255),
    hair=(22, 24, 30, 255),
    hair_hi=(42, 47, 56, 255),
    shirt=(72, 154, 212, 255),
    shirt_dark=(35, 95, 154, 255),
    pants=(92, 96, 104, 255),
    pants_hi=(132, 136, 144, 255),
    shoe=(88, 54, 34, 255),
    sole=(205, 198, 186, 255),
    moustache=False,
    scale=0.96,
    eye_scale=1.02,
    mouth_y=376,
    label="young man",
)


def _new(size: tuple[int, int], scale: int = 3):
    im = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), scale


def _down(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    return im.resize(size, Image.LANCZOS)


def _box(box, s: int):
    return [int(v * s) for v in box]


def _pts(points, s: int):
    return [(int(x * s), int(y * s)) for x, y in points]


def _line(draw: ImageDraw.ImageDraw, points, fill, width: int, s: int):
    draw.line(_pts(points, s), fill=fill, width=max(1, int(width * s)), joint="curve")


def _shade(rgba, factor: float):
    return (int(rgba[0] * factor), int(rgba[1] * factor), int(rgba[2] * factor), rgba[3])


def _empty(size=(24, 24)):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def make_head(spec: StorySpec) -> Image.Image:
    im, d, s = _new(HEAD)
    cx = HEAD[0] / 2

    d.rounded_rectangle(_box((134, 232, 178, 320), s), radius=14 * s,
                        fill=spec.skin, outline=INK, width=LW * s)
    d.ellipse(_box((34, 124, 82, 190), s), fill=spec.skin, outline=INK, width=LW * s)
    d.ellipse(_box((230, 124, 278, 190), s), fill=spec.skin, outline=INK, width=LW * s)
    _line(d, [(50, 156), (62, 142), (72, 160)], INK, 2, s)
    _line(d, [(262, 156), (250, 142), (240, 160)], INK, 2, s)

    d.ellipse(_box((50, 54, 262, 264), s), fill=spec.skin, outline=INK, width=LW * s)
    d.ellipse(_box((64, 68, 248, 254), s), fill=_shade(spec.skin, 1.12))

    if spec.moustache:
        d.pieslice(_box((42, 20, 260, 174), s), 178, 357, fill=spec.hair, outline=INK, width=LW * s)
        d.pieslice(_box((72, 12, 278, 150), s), 188, 345, fill=spec.hair)
        d.polygon(_pts([(58, 112), (86, 64), (118, 78), (94, 144)], s), fill=spec.hair)
        d.polygon(_pts([(112, 54), (170, 36), (230, 62), (182, 80)], s), fill=spec.hair)
        d.arc(_box((210, 38, 266, 106), s), 250, 86, fill=spec.hair_hi, width=5 * s)
        # Moustache lives on the head, while the mouth viseme overlays below it.
        d.ellipse(_box((110, 198, 154, 226), s), fill=spec.hair)
        d.ellipse(_box((154, 198, 198, 226), s), fill=spec.hair)
        d.rectangle(_box((126, 198, 182, 212), s), fill=spec.hair)
    else:
        d.pieslice(_box((34, 18, 270, 176), s), 178, 357, fill=spec.hair, outline=INK, width=LW * s)
        d.pieslice(_box((72, 10, 284, 154), s), 186, 342, fill=spec.hair)
        d.polygon(_pts([(86, 112), (126, 58), (168, 72), (132, 148)], s), fill=spec.hair)
        d.polygon(_pts([(160, 70), (226, 56), (256, 96), (194, 98)], s), fill=spec.hair)

    # Nose is baked so head turns still have a readable face.
    _line(d, [(156, 164), (148, 190), (160, 194)], _shade(spec.skin, 0.75), 3, s)
    return _down(im, HEAD)


def make_torso(spec: StorySpec) -> Image.Image:
    im, d, s = _new(TORSO)
    w, h = TORSO
    # Collared shirt / kurta-like tunic, body only. Arms and legs are separate.
    body = [(34, 36), (78, 10), (w / 2, 24), (w - 78, 10), (w - 34, 36),
            (w - 20, h - 10), (20, h - 10)]
    d.polygon(_pts(body, s), fill=spec.shirt)
    d.line(_pts(body + [body[0]], s), fill=INK, width=LW * s, joint="curve")
    d.polygon(_pts([(74, 12), (w / 2, 45), (104, 95)], s),
              fill=_shade(spec.shirt, 1.18), outline=spec.shirt_dark)
    d.polygon(_pts([(w - 74, 12), (w / 2, 45), (w - 104, 95)], s),
              fill=_shade(spec.shirt, 1.18), outline=spec.shirt_dark)
    d.line(_box((w / 2, 42, w / 2, h - 28), s), fill=spec.shirt_dark, width=3 * s)
    if spec.moustache:
        d.rounded_rectangle(_box((w / 2 - 18, 76, w / 2 + 18, 190), s),
                            radius=5 * s, fill=_shade(spec.shirt_dark, 0.95),
                            outline=INK, width=2 * s)
        for y in (96, 122, 148, 174):
            d.ellipse(_box((w / 2 - 5, y, w / 2 + 5, y + 10), s),
                      fill=(230, 202, 150, 255))
    else:
        for y in (92, 136, 180, 224):
            d.ellipse(_box((w / 2 - 5, y, w / 2 + 5, y + 10), s),
                      fill=(235, 240, 244, 255), outline=spec.shirt_dark, width=s)
    _line(d, [(36, 80), (70, 118), (74, 220)], _shade(spec.shirt_dark, 0.9), 3, s)
    _line(d, [(w - 36, 80), (w - 70, 118), (w - 74, 220)], _shade(spec.shirt_dark, 0.9), 3, s)
    return _down(im, TORSO)


def make_upper_arm(spec: StorySpec, side: str) -> Image.Image:
    im, d, s = _new(UPPER_ARM)
    w, h = UPPER_ARM
    d.rounded_rectangle(_box((8, 2, w - 8, h - 6), s), radius=24 * s,
                        fill=spec.skin, outline=INK, width=LW * s)
    d.rounded_rectangle(_box((4, 0, w - 4, 78), s), radius=24 * s,
                        fill=spec.shirt, outline=INK, width=LW * s)
    d.line(_box((8, 76, w - 8, 76), s), fill=spec.shirt_dark, width=3 * s)
    return _down(im, UPPER_ARM)


def make_forearm(spec: StorySpec, side: str) -> Image.Image:
    im, d, s = _new(FOREARM)
    w, h = FOREARM
    d.rounded_rectangle(_box((12, 2, w - 12, h - 46), s), radius=22 * s,
                        fill=spec.skin, outline=INK, width=LW * s)
    hand = (6, h - 70, w - 6, h - 2)
    d.ellipse(_box(hand, s), fill=spec.skin, outline=INK, width=LW * s)
    if side == "left":
        fingers = [((20, h - 42), (28, h - 18)), ((39, h - 42), (49, h - 18))]
    else:
        fingers = [((w - 20, h - 42), (w - 28, h - 18)), ((w - 39, h - 42), (w - 49, h - 18))]
    for start, end in fingers:
        _line(d, [start, end], _shade(spec.skin, 0.72), 2, s)
    d.rounded_rectangle(_box((12, h - 90, w - 12, h - 56), s), radius=12 * s, fill=spec.skin)
    return _down(im, FOREARM)


def make_thigh(spec: StorySpec, side: str) -> Image.Image:
    im, d, s = _new(THIGH)
    w, h = THIGH
    fill = spec.pants if side == "left" else spec.pants_hi
    d.rounded_rectangle(_box((8, 2, w - 8, h - 2), s), radius=24 * s,
                        fill=fill, outline=INK, width=LW * s)
    d.line(_box((12, 42, w - 12, 42), s), fill=_shade(fill, 0.72), width=2 * s)
    return _down(im, THIGH)


def make_shin(spec: StorySpec, side: str) -> Image.Image:
    im, d, s = _new(SHIN)
    w, h = SHIN
    cx = w / 2
    fill = spec.pants if side == "left" else spec.pants_hi
    d.rounded_rectangle(_box((cx - 27, 2, cx + 27, h - 42), s), radius=20 * s,
                        fill=fill, outline=INK, width=LW * s)
    if side == "left":
        shoe_box = (cx - 48, h - 68, cx + 40, h - 6)
    else:
        shoe_box = (cx - 40, h - 68, cx + 48, h - 6)
    d.rounded_rectangle(_box(shoe_box, s), radius=22 * s, fill=spec.shoe, outline=INK, width=LW * s)
    d.rounded_rectangle(_box((shoe_box[0] - 3, h - 22, shoe_box[2] + 3, h - 3), s),
                        radius=8 * s, fill=spec.sole, outline=INK, width=3 * s)
    _line(d, [(shoe_box[0] + 16, h - 50), (shoe_box[2] - 14, h - 58)], spec.sole, 3, s)
    return _down(im, SHIN)


def make_knee(spec: StorySpec) -> Image.Image:
    im, d, s = _new(KNEE)
    d.ellipse(_box((4, 6, KNEE[0] - 4, KNEE[1] - 4), s),
              fill=_shade(spec.pants, 1.08), outline=INK, width=4 * s)
    return _down(im, KNEE)


def make_eyes(spec: StorySpec, kind: str) -> Image.Image:
    im, d, s = _new(EYES_CANVAS)
    cx, cy = EYES_CANVAS[0] / 2, EYES_CANVAS[1] / 2
    sp = 48
    ew = 24 * spec.eye_scale
    eh = 28 * spec.eye_scale
    if kind == "open":
        for ex in (cx - sp, cx + sp):
            d.ellipse(_box((ex - ew, cy - eh, ex + ew, cy + eh), s),
                      fill=(255, 255, 250, 255), outline=INK, width=4 * s)
            d.ellipse(_box((ex - 11, cy - 10, ex + 11, cy + 14), s), fill=(70, 42, 24, 255))
            d.ellipse(_box((ex - 5, cy - 2, ex + 5, cy + 9), s), fill=(15, 12, 12, 255))
            d.ellipse(_box((ex - 9, cy - 12, ex - 2, cy - 5), s), fill=(255, 255, 255, 255))
    elif kind == "closed":
        for ex in (cx - sp, cx + sp):
            d.arc(_box((ex - ew, cy - 10, ex + ew, cy + 22), s), 12, 168, fill=INK, width=5 * s)
    else:
        for ex in (cx - sp, cx + sp):
            d.arc(_box((ex - ew, cy - 18, ex + ew, cy + 18), s), 196, 344, fill=INK, width=5 * s)
    return _down(im, EYES_CANVAS)


def make_brows(spec: StorySpec, kind: str) -> Image.Image:
    im, d, s = _new(BROWS_CANVAS)
    cx, cy = BROWS_CANVAS[0] / 2, BROWS_CANVAS[1] / 2
    sp = 50
    col = spec.hair
    if kind == "neutral":
        pairs = [(-1, 0), (1, 0)]
        for side, _ in pairs:
            ex = cx + side * sp
            _line(d, [(ex - 22, cy + 2), (ex + 22, cy - 4)], col, 8, s)
    elif kind == "happy":
        for side in (-1, 1):
            ex = cx + side * sp
            d.arc(_box((ex - 24, cy - 8, ex + 24, cy + 26), s), 195, 345, fill=col, width=8 * s)
    elif kind == "sad":
        _line(d, [(cx - sp - 22, cy + 12), (cx - sp + 22, cy - 8)], col, 8, s)
        _line(d, [(cx + sp - 22, cy - 8), (cx + sp + 22, cy + 12)], col, 8, s)
    else:
        for side in (-1, 1):
            ex = cx + side * sp
            d.arc(_box((ex - 22, cy - 14, ex + 22, cy + 22), s), 200, 340, fill=col, width=8 * s)
    return _down(im, BROWS_CANVAS)


def make_mouth(spec: StorySpec, kind: str) -> Image.Image:
    im, d, s = _new(MOUTH_CANVAS)
    cx, cy = MOUTH_CANVAS[0] / 2, MOUTH_CANVAS[1] / 2
    lip = _shade(spec.skin, 0.58)
    dark = (64, 32, 35, 255)
    tongue = (190, 86, 92, 255)
    if kind == "X":
        d.arc(_box((cx - 28, cy - 20, cx + 28, cy + 24), s), 18, 162, fill=lip, width=5 * s)
        return _down(im, MOUTH_CANVAS)
    if kind == "sad":
        d.arc(_box((cx - 28, cy + 4, cx + 28, cy + 48), s), 198, 342, fill=lip, width=5 * s)
        return _down(im, MOUTH_CANVAS)
    sizes = {"A": (20, 10), "B": (18, 12), "C": (28, 18), "D": (42, 30),
             "E": (24, 30), "F": (22, 22), "G": (36, 16), "H": (34, 24)}
    mw, mh = sizes.get(kind, (28, 18))
    d.ellipse(_box((cx - mw, cy - mh, cx + mw, cy + mh), s), fill=dark, outline=lip, width=4 * s)
    if mh > 14:
        d.ellipse(_box((cx - mw * 0.55, cy + mh * 0.18, cx + mw * 0.55, cy + mh * 0.88), s),
                  fill=tongue)
    if kind in {"D", "G"}:
        d.chord(_box((cx - mw + 5, cy - mh + 4, cx + mw - 5, cy + mh * 0.15), s),
                182, 358, fill=(255, 250, 240, 255))
    d.ellipse(_box((cx - mw, cy - mh, cx + mw, cy + mh), s), outline=lip, width=4 * s)
    return _down(im, MOUTH_CANVAS)


def write_rig(spec: StorySpec, out: Path) -> None:
    rig = {
        "type": "skeletal",
        "scale": spec.scale,
        "space": list(SPACE),
        "feet_y": FEET_Y,
        "cx": CX,
        "joints": {
            "neck": [380, 392],
            "shoulder_left": [292, 462],
            "shoulder_right": [468, 462],
            "hip_left": [338, 650],
            "hip_right": [422, 650],
        },
        "face": {"brows": [380, 258], "eyes": [380, 310], "mouth": [380, spec.mouth_y]},
        "pivot": {
            "head": [0.5, 0.92],
            "torso": [0.5, 0.5],
            "upper_arm": [0.5, 0.08],
            "forearm": [0.5, 0.13],
            "thigh": [0.5, 0.06],
            "shin": [0.5, 0.13],
        },
        "bone": {"upper_arm": 0.78, "forearm": 0.0, "thigh": 0.88, "shin": 0.0},
        "neck_raise": 0,
        "torso_dy": 12,
        "render_padding": 250,
        "neck_stub": True,
        "overlay_only": False,
    }
    (out / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def build_character(spec: StorySpec) -> None:
    out = CHARS / spec.cid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    parts = {
        "head": make_head(spec),
        "head_back": make_head(spec),
        "torso": make_torso(spec),
        "upper_arm_left": make_upper_arm(spec, "left"),
        "upper_arm_right": make_upper_arm(spec, "right"),
        "forearm_left": make_forearm(spec, "left"),
        "forearm_right": make_forearm(spec, "right"),
        "thigh_left": make_thigh(spec, "left"),
        "thigh_right": make_thigh(spec, "right"),
        "shin_left": make_shin(spec, "left"),
        "shin_right": make_shin(spec, "right"),
        "knee_left": make_knee(spec),
        "knee_right": make_knee(spec),
    }
    for name in ("open", "closed", "happy"):
        parts[f"eyes_{name}"] = make_eyes(spec, name)
    for name in ("neutral", "happy", "sad", "surprised"):
        parts[f"brows_{name}"] = make_brows(spec, name)
    for name in ("X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"):
        parts[f"mouth_{name}"] = make_mouth(spec, name)

    for name, im in parts.items():
        im.save(out / f"{name}.png")
    write_rig(spec, out)
    print(f"{spec.cid}: wrote {len(parts)} real rig parts -> {out}")


def _pose_for(cid: str, action: str):
    from shiksha_cast.cartoon.build import _adv_pose

    presets = {
        "idle": ([], 0.3),
        "talk": ([{"who": cid, "do": "talk", "levels": [0.6] * 80, "start": 0.0, "end": 4.0}], 0.8),
        "wave": ([{"who": cid, "do": "wave", "start": 0.0, "end": 3.0}], 1.2),
        "point": ([{"who": cid, "do": "point", "side": "right", "start": 0.0, "end": 3.0}], 1.2),
        "walk": ([{"who": cid, "do": "walkto", "to": 0.65, "start": 0.0, "end": 3.0}], 1.0),
        "run": ([{"who": cid, "do": "runto", "to": 0.75, "start": 0.0, "end": 3.0}], 1.0),
        "sad": ([{"who": cid, "do": "sad", "start": 0.0, "end": 3.0}], 1.0),
        "look_left": ([{"who": cid, "do": "look_left", "start": 0.0, "end": 2.0}], 0.8),
    }
    actions, t = presets[action]
    return _adv_pose(cid, actions, t, 15, 0.0, 0.45, "right")


def _tile(ch, cid: str, action: str, tw: int = 340, th: int = 470) -> Image.Image:
    bg = Image.new("RGBA", (tw, th), (236, 240, 247, 255))
    pose, _x, facing, bob = _pose_for(cid, action)
    ch.place(bg, pose, 0.5, th - 28, int(th * 0.86), facing=facing, bob=bob)
    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle([0, 0, tw, 34], fill=(40, 40, 60, 255))
    draw.text((10, 4), action, fill=(255, 255, 255, 255), font=font)
    draw.rectangle([0, 0, tw - 1, th - 1], outline=(120, 130, 150, 255), width=2)
    return bg


def build_previews() -> None:
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter

    DIST.mkdir(exist_ok=True)
    actions = ["idle", "talk", "wave", "point", "walk", "run", "sad", "look_left"]
    for spec in (FATHER, YOUNG):
        ch = SkeletalCharacter(CHARS / spec.cid)
        tiles = [_tile(ch, spec.cid, action) for action in actions]
        tw, th = tiles[0].size
        cols = 4
        sheet = Image.new("RGBA", (cols * tw, math.ceil(len(tiles) / cols) * th), (255, 255, 255, 255))
        for i, tile in enumerate(tiles):
            sheet.alpha_composite(tile, ((i % cols) * tw, (i // cols) * th))
        out = DIST / f"_{spec.cid}_preview.png"
        sheet.convert("RGB").save(out)
        print(f"preview -> {out}")


def main() -> None:
    for spec in (FATHER, YOUNG):
        build_character(spec)
    build_previews()


if __name__ == "__main__":
    main()
