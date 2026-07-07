"""Generate two new reusable 2D cutout rig characters that plug into the existing
Kinnu skeletal rig (src/shiksha_cast/cartoon/rig2.py):

  * gappu_hd  -- a cute, slightly-mischievous BOY (green shirt, blue shorts).
  * vibhu_hd  -- Kinnu's little brother: smaller, bigger head, light-blue shirt.

Design rules (kept identical to kinnu_hd so the rig math lines up exactly):
  * Same canvas/space, joints, bone fractions, face anchors and pivots as the
    rig defaults (which are tuned for kinnu_hd). We only change the *artwork* and,
    for Vibhu, the overall `scale` + a bigger head + chubbier limbs (toddler look).
  * Every part is drawn procedurally with PIL using ONE shared palette per
    character, so colours/outlines never drift between parts (no AI randomness).
  * Thick black outline, transparent background, parts sized to match kinnu_hd's
    so hands/feet never clip (render_padding handles the rest).

Kinnu herself is NEVER touched -- she stays the fixed brand character.

Run:
    .venv-veena/Scripts/python.exe scripts/make_kinnu_castmates.py
This writes assets/cartoon/characters/{gappu_hd,vibhu_hd}/ and three preview
sheets in dist/.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CHARS = ROOT / "assets" / "cartoon" / "characters"
INK = (38, 34, 42, 255)          # thick black-ish outline
LW = 8                            # outline width (HD)

# ---- part pixel sizes (match kinnu_hd so the default rig geometry fits) ----
UP_ARM = (64, 209)
FOREARM = (74, 212)
THIGH = (80, 206)
SHIN = (116, 211)
TORSO = (231, 236)
KNEE = (58, 44)
MOUTH_CANVAS = (150, 124)
EYES_CANVAS = (210, 120)
BROWS_CANVAS = (196, 70)


def _new(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _shade(rgb, f):
    return (int(rgb[0] * f), int(rgb[1] * f), int(rgb[2] * f), 255)


# --------------------------------------------------------------------------- #
#  Character palette / proportion spec
# --------------------------------------------------------------------------- #
class Spec:
    def __init__(self, **kw):
        self.__dict__.update(kw)


GAPPU = Spec(
    cid="gappu_hd",
    skin=(243, 200, 158, 255),       # warm tan, different from Kinnu
    hair=(28, 24, 30, 255),          # short black hair
    shirt=(70, 175, 95, 255),        # green shirt
    shorts=(54, 110, 200, 255),      # blue shorts
    shoe=(245, 245, 250, 255),       # white sneakers
    shoe_trim=(70, 175, 95, 255),
    head=(300, 300),
    head_pivot=[0.5, 0.95],
    limb_w=1.0,
    scale=1.0,
    eye_scale=1.0,
    fringe="tuft",                   # short spiky tuft
    face=None,                       # use rig defaults
)

VIBHU = Spec(
    cid="vibhu_hd",
    skin=(250, 214, 178, 255),       # like Kinnu (brothers/sister), a touch lighter
    hair=(26, 22, 28, 255),
    shirt=(120, 195, 240, 255),      # light blue shirt
    shorts=(40, 60, 120, 255),       # navy shorts
    shoe=(225, 70, 70, 255),         # little red shoes
    shoe_trim=(255, 255, 255, 255),
    head=(346, 356),                 # bigger head -> childlike
    head_pivot=[0.5, 0.95],
    limb_w=1.16,                     # chubbier toddler limbs
    scale=0.84,                      # clearly smaller/younger
    eye_scale=1.22,                  # big innocent eyes
    fringe="curl",                   # tiny forehead curl
    # nudge features to sit nicely inside the bigger head
    face={"brows": [380, 262], "eyes": [380, 312], "mouth": [380, 382]},
)


# --------------------------------------------------------------------------- #
#  Limb parts
# --------------------------------------------------------------------------- #
def make_upper_arm(spec):
    w, h = UP_ARM
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    r = (w - LW) / 2
    d.rounded_rectangle([LW / 2, 2, w - LW / 2, h - 2], radius=r,
                        fill=spec.skin, outline=INK, width=LW)
    return img


def make_forearm(spec):
    w, h = FOREARM
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    cx = w / 2
    # forearm shaft
    d.rounded_rectangle([LW / 2, 2, w - LW / 2, h * 0.74], radius=(w - LW) / 2,
                        fill=spec.skin, outline=INK, width=LW)
    # mitten hand at the bottom
    hr = w * 0.62
    hy = h - 2 * hr - 2
    d.ellipse([cx - hr, hy, cx + hr, hy + 2 * hr], fill=spec.skin, outline=INK, width=LW)
    # thumb bump
    d.ellipse([cx + hr - 14, hy + hr - 6, cx + hr + 12, hy + hr + 26],
              fill=spec.skin, outline=INK, width=LW)
    # cover the seam where the shaft meets the hand so it reads as one piece
    d.rounded_rectangle([LW / 2 + 2, h * 0.55, w - LW / 2 - 2, h * 0.78],
                        radius=18, fill=spec.skin)
    return img


def make_thigh(spec):
    w, h = THIGH
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    r = (w - LW) / 2
    # skin leg
    d.rounded_rectangle([LW / 2, 2, w - LW / 2, h - 2], radius=r,
                        fill=spec.skin, outline=INK, width=LW)
    # shorts cover the top ~60% so the leg clearly reads as wearing shorts
    sh = int(h * 0.60)
    d.rounded_rectangle([LW / 2 - 2, 2, w - LW / 2 + 2, sh], radius=20,
                        fill=spec.shorts, outline=INK, width=LW)
    # flat hem
    d.line([LW / 2, sh, w - LW / 2, sh], fill=INK, width=LW)
    return img


def make_shin(spec):
    w, h = SHIN
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    cx = w / 2
    legw = w * 0.42 * spec.limb_w
    # skin lower leg (narrower than the shoe canvas)
    d.rounded_rectangle([cx - legw, 2, cx + legw, h * 0.80], radius=legw,
                        fill=spec.skin, outline=INK, width=LW)
    # sneaker pointing forward (+x = facing right; place() flips for left)
    sy = h * 0.66
    d.rounded_rectangle([cx - legw, sy, cx + w * 0.46, h - 4], radius=22,
                        fill=spec.shoe, outline=INK, width=LW)
    # sole
    d.rounded_rectangle([cx - legw, h - 20, cx + w * 0.46, h - 4], radius=8,
                        fill=spec.shoe_trim, outline=INK, width=max(4, LW - 3))
    # lace/trim stripe
    d.line([cx - legw + 8, sy + 14, cx + w * 0.30, sy + 4], fill=spec.shoe_trim,
           width=max(4, LW - 3))
    return img


def make_knee(spec):
    w, h = KNEE
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    d.ellipse([3, 3, w - 3, h - 3], fill=spec.skin, outline=INK, width=max(5, LW - 2))
    return img


def make_torso(spec):
    w, h = TORSO
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    # T-shirt: wide shoulders tapering slightly to the waist, rounded corners
    top, bot = 6, h - 4
    sl, sr = w * 0.07, w * 0.93          # shoulder line
    wl, wr = w * 0.13, w * 0.87          # waist line
    d.polygon([(sl, top + 18), (sr, top + 18), (wr, bot), (wl, bot)],
              fill=spec.shirt)
    # rounded shoulder caps + outline pass
    d.rounded_rectangle([sl, top, sr, bot], radius=30, outline=INK, width=LW)
    d.line([(sl + 4, top + 18), (wl + 2, bot)], fill=INK, width=LW)
    d.line([(sr - 4, top + 18), (wr - 2, bot)], fill=INK, width=LW)
    d.line([(wl, bot), (wr, bot)], fill=INK, width=LW)
    # round collar notch
    cx = w / 2
    d.arc([cx - 36, top - 22, cx + 36, top + 34], 20, 160, fill=INK, width=LW)
    return img


# --------------------------------------------------------------------------- #
#  Head
# --------------------------------------------------------------------------- #
def make_head(spec):
    w, h = spec.head
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    cx = w / 2
    # the face circle sits in the LOWER part of the canvas (room for hair on top)
    face_d = w * 0.92
    fx0, fx1 = cx - face_d / 2, cx + face_d / 2
    fy1 = h - 4
    fy0 = fy1 - face_d
    # ears (drawn first; hair overlaps their tops)
    er = face_d * 0.13
    ey = fy0 + face_d * 0.52
    for ex in (fx0 + 4, fx1 - 4):
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=spec.skin,
                  outline=INK, width=LW)
    # face
    d.ellipse([fx0, fy0, fx1, fy1], fill=spec.skin, outline=INK, width=LW)
    # hair: black cap over the top of the head
    hx0, hx1 = fx0 - 6, fx1 + 6
    hy0 = fy0 - 10
    d.pieslice([hx0, hy0, hx1, hy0 + face_d + 12], 178, 362, fill=spec.hair)

    # Tidy the forehead with a curved skin patch. The earlier straight chord
    # left a dark horizontal strip across Vibhu's eyes, which looked like
    # unwanted glasses in the final video.
    left = fx0 + face_d * 0.08
    right = fx1 - face_d * 0.08
    hairline = []
    for i in range(25):
        t = i / 24
        x = left + (right - left) * t
        edge = abs(t - 0.5) * 2
        if spec.fringe == "curl":
            y = fy0 + face_d * (0.26 + 0.05 * (edge ** 1.4))
        else:
            y = fy0 + face_d * (0.23 + 0.07 * (edge ** 1.5))
        hairline.append((x, y))
    patch = _new((w, h))
    pd = ImageDraw.Draw(patch)
    fill_bottom = fy0 + face_d * (0.50 if spec.fringe == "curl" else 0.47)
    pd.polygon(hairline + [(right, fill_bottom), (left, fill_bottom)], fill=spec.skin)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([fx0, fy0, fx1, fy1], fill=255)
    patch_alpha = ImageChops.multiply(patch.getchannel("A"), mask)
    patch.putalpha(patch_alpha)
    img.alpha_composite(patch)
    if spec.fringe != "curl":
        d.line(hairline, fill=spec.hair, width=max(4, LW - 3))
    # hairline detail
    if spec.fringe == "tuft":
        # a neat little widow's peak at the centre hairline (boyish, but does
        # NOT overlap the eyebrows the way loose forehead spikes did)
        peak_y = fy0 + face_d * 0.16
        d.polygon([(cx - 18, peak_y - 4), (cx, peak_y + 22), (cx + 18, peak_y - 4)],
                  fill=spec.hair)
        # a small side sweep for a touch of character
        d.polygon([(fx0 + face_d * 0.20, peak_y - 10),
                   (fx0 + face_d * 0.40, peak_y - 4),
                   (fx0 + face_d * 0.22, peak_y + 8)], fill=spec.hair)
    else:  # tiny forehead curl (toddler)
        bx = cx
        by = fy0 + face_d * 0.24
        d.arc([bx - 22, by - 18, bx + 22, by + 26], 250, 470, fill=spec.hair, width=12)
    # small nose at face centre (lands between eyes & mouth in world space)
    nose_y = fy0 + face_d * 0.60
    d.arc([cx - 13, nose_y - 8, cx + 13, nose_y + 14], 30, 150, fill=INK, width=6)
    # redraw the face outline so the chin/jaw stays crisp over the hair
    d.ellipse([fx0, fy0, fx1, fy1], outline=INK, width=LW)
    return img


# --------------------------------------------------------------------------- #
#  Face overlays (drawn centred; the rig places them by image centre)
# --------------------------------------------------------------------------- #
def make_eyes(spec, kind):
    w, h = EYES_CANVAS
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    cx, cy = w / 2, h / 2
    sp = 52                                   # half the eye spacing
    ew = 30 * spec.eye_scale
    eh = 36 * spec.eye_scale
    centers = [(cx - sp, cy), (cx + sp, cy)]
    if kind == "open":
        for ex, ey in centers:
            d.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=(255, 255, 255, 255),
                      outline=INK, width=LW)
            ir = ew * 0.74
            iy = ey + eh * 0.10
            d.ellipse([ex - ir, iy - ir, ex + ir, iy + ir], fill=(54, 38, 30, 255))
            d.ellipse([ex - ir * 0.45, iy - ir * 0.45, ex + ir * 0.45, iy + ir * 0.45],
                      fill=(18, 14, 16, 255))
            d.ellipse([ex - ir * 0.2, iy - ir * 0.62, ex + ir * 0.34, iy - ir * 0.10],
                      fill=(255, 255, 255, 255))
    elif kind == "closed":
        for ex, ey in centers:
            d.arc([ex - ew, ey - eh * 0.5, ex + ew, ey + eh], 18, 162, fill=INK, width=LW)
    elif kind == "happy":
        for ex, ey in centers:
            d.arc([ex - ew, ey - eh, ex + ew, ey + eh * 0.6], 200, 340, fill=INK, width=LW)
    return img


def make_brows(spec, kind):
    w, h = BROWS_CANVAS
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    cx, cy = w / 2, h / 2
    sp = 52
    bw = 30
    col = spec.hair
    if kind == "neutral":
        for sgn in (-1, 1):
            ex = cx + sgn * sp
            d.line([ex - bw, cy + 2, ex + bw, cy - 4], fill=col, width=12)
    elif kind == "happy":
        for sgn in (-1, 1):
            ex = cx + sgn * sp
            d.arc([ex - bw, cy - 4, ex + bw, cy + 26], 196, 344, fill=col, width=12)
    elif kind == "sad":
        # inner ends raised
        for sgn in (-1, 1):
            ex = cx + sgn * sp
            inner = (ex - sgn * bw, cy - 8)
            outer = (ex + sgn * bw, cy + 12)
            d.line([inner, outer], fill=col, width=12)
    elif kind == "surprised":
        for sgn in (-1, 1):
            ex = cx + sgn * sp
            d.arc([ex - bw, cy - 2, ex + bw, cy + 34], 200, 340, fill=col, width=12)
    return img


def make_mouth(spec, kind):
    w, h = MOUTH_CANVAS
    img = _new((w, h))
    d = ImageDraw.Draw(img)
    cx, cy = w / 2, h / 2
    inner = (165, 58, 58, 255)
    tongue = (228, 120, 120, 255)
    if kind == "X":
        d.arc([cx - 34, cy - 24, cx + 34, cy + 30], 18, 162, fill=INK, width=9)
        return img
    if kind == "sad":
        d.arc([cx - 34, cy + 4, cx + 34, cy + 56], 200, 340, fill=INK, width=9)
        return img
    params = {
        "A": (40, 30), "B": (22, 16), "C": (54, 42), "D": (74, 62),
        "E": (38, 52), "F": (30, 30), "G": (66, 32), "H": (50, 46),
    }
    mw, mh = params.get(kind, (50, 42))
    box = [cx - mw, cy - mh, cx + mw, cy + mh]
    d.ellipse(box, fill=inner, outline=INK, width=9)
    # tongue at the bottom of the open mouth
    d.ellipse([cx - mw * 0.5, cy + mh * 0.12, cx + mw * 0.5, cy + mh * 0.92], fill=tongue)
    if kind in ("D", "G"):  # show a top teeth band on big smiles
        d.chord([cx - mw + 6, cy - mh + 5, cx + mw - 6, cy + mh * 0.2],
                182, 358, fill=(255, 252, 250, 255))
    d.ellipse(box, outline=INK, width=9)
    return img


# --------------------------------------------------------------------------- #
#  Assemble one character folder
# --------------------------------------------------------------------------- #
MOUTHS = ["X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"]
EYES = ["open", "closed", "happy"]
BROWS = ["neutral", "happy", "sad", "surprised"]


def build_character(spec):
    out = CHARS / spec.cid
    out.mkdir(parents=True, exist_ok=True)

    parts = {
        "upper_arm_left": make_upper_arm(spec),
        "upper_arm_right": make_upper_arm(spec),
        "forearm_left": make_forearm(spec),
        "forearm_right": make_forearm(spec),
        "thigh_left": make_thigh(spec),
        "thigh_right": make_thigh(spec),
        "shin_left": make_shin(spec),
        "shin_right": make_shin(spec),
        "knee_left": make_knee(spec),
        "knee_right": make_knee(spec),
        "torso": make_torso(spec),
        "head": make_head(spec),
    }
    for k in MOUTHS:
        parts[f"mouth_{k}"] = make_mouth(spec, k)
    for k in EYES:
        parts[f"eyes_{k}"] = make_eyes(spec, k)
    for k in BROWS:
        parts[f"brows_{k}"] = make_brows(spec, k)

    for name, im in parts.items():
        im.save(out / f"{name}.png")

    cfg = {"type": "skeletal", "scale": spec.scale, "pivot": {"head": spec.head_pivot}}
    if spec.face:
        cfg["face"] = spec.face
    (out / "rig2.json").write_text(json.dumps(cfg, indent=2))
    print(f"  {spec.cid}: wrote {len(parts)} parts + rig2.json -> {out}")
    return out


# --------------------------------------------------------------------------- #
#  Preview sheets
# --------------------------------------------------------------------------- #
def _pose_for(cid, action):
    """Return a (pose, bob) for a named preview action via the real _adv_pose."""
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
    pose, x_cur, facing, bob = _adv_pose(cid, actions, t, 15, 0.0, 0.5, "right")
    if action == "talk":
        pose["mouth"] = "C"
    return pose, bob, facing


def _tile(ch, action, label, tw=340, th=470):
    from PIL import ImageFont
    bg = Image.new("RGBA", (tw, th), (236, 240, 247, 255))
    if action == "talk":
        pose, bob = {"arm_left": (0, 2), "arm_right": (0, -2), "mouth": "C",
                     "eyes": "open", "brows": "neutral", "head_turn": "center"}, 0.0
        facing = "right"
    else:
        pose, bob, facing = _pose_for(ch_cid(ch), action)
    if abs(float(pose.get("body_angle", 0.0) or 0.0)) > 0.05:   # swim: body lies flat
        ch.place(bg, pose, 0.5, int(th * 0.52), int(th * 0.50), facing=facing, bob=bob)
    else:
        ch.place(bg, pose, 0.5, th - 28, int(th * 0.74), facing=facing, bob=bob)
    d = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    d.rectangle([0, 0, tw, 34], fill=(40, 40, 60, 255))
    d.text((10, 4), label, fill=(255, 255, 255, 255), font=font)
    d.rectangle([0, 0, tw - 1, th - 1], outline=(120, 130, 150, 255), width=2)
    return bg


_CID_BY_DIR: dict = {}


def ch_cid(ch):
    return _CID_BY_DIR[ch.dir]


def _sheet(ch, actions, cols=4):
    tiles = [_tile(ch, a, a) for a in actions]
    rows = math.ceil(len(tiles) / cols)
    tw, th = tiles[0].size
    sheet = Image.new("RGBA", (cols * tw, rows * th), (255, 255, 255, 255))
    for i, t in enumerate(tiles):
        sheet.alpha_composite(t, ((i % cols) * tw, (i // cols) * th))
    return sheet


def build_previews():
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter

    actions = ["idle", "talk", "wave", "point", "cheer", "sad", "cry", "jump",
               "swim", "look_left", "look_right", "look_back"]
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)

    gappu = SkeletalCharacter(CHARS / "gappu_hd")
    vibhu = SkeletalCharacter(CHARS / "vibhu_hd")
    _CID_BY_DIR[gappu.dir] = "gappu_hd"
    _CID_BY_DIR[vibhu.dir] = "vibhu_hd"

    _sheet(gappu, actions).convert("RGB").save(dist / "_gappu_rig_preview.png")
    print("  preview ->", dist / "_gappu_rig_preview.png")
    _sheet(vibhu, actions).convert("RGB").save(dist / "_vibhu_rig_preview.png")
    print("  preview ->", dist / "_vibhu_rig_preview.png")

    # combined sheet: a few key actions, Gappu over Vibhu
    combo_actions = ["idle", "wave", "point", "cheer", "jump", "look_back"]
    g = _sheet(gappu, combo_actions, cols=len(combo_actions))
    v = _sheet(vibhu, combo_actions, cols=len(combo_actions))
    combo = Image.new("RGBA", (g.width, g.height + v.height), (255, 255, 255, 255))
    combo.alpha_composite(g, (0, 0))
    combo.alpha_composite(v, (0, g.height))
    combo.convert("RGB").save(dist / "_gappu_vibhu_actions_preview.png")
    print("  preview ->", dist / "_gappu_vibhu_actions_preview.png")


def main():
    print("Building castmate characters (Kinnu stays untouched):")
    build_character(GAPPU)
    build_character(VIBHU)
    print("Rendering preview sheets:")
    build_previews()
    print("Done.")


if __name__ == "__main__":
    main()
