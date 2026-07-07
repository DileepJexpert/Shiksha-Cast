"""Build quick talking-figure rigs for the family sample video.

These are sample rigs, not final Option-C articulated puppets. They use the
new source sheets as full-body talking figures with mouth overlays so we can
render a real three-character story today.
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

SOURCE = ROOT / "assets" / "cartoon" / "source"
CHARS = ROOT / "assets" / "cartoon" / "characters"
DIST = ROOT / "dist"

SPACE = (760, 1060)
FEET_Y = 1024
CX = 380


@dataclass(frozen=True)
class FigureSpec:
    cid: str
    display_name: str
    source: str
    body_box: tuple[int, int, int, int]
    mouth_xy: tuple[int, int]
    scale: float
    head_box: tuple[int, int, int, int] | None = None
    route: str = "sample_talking_figure_from_option_c_sheet"


SPECS = [
    FigureSpec(
        cid="story_father_v2_hd",
        display_name="Papa / Suresh",
        source="story_father_parts_sheet_v2.png",
        body_box=(338, 112, 640, 842),
        mouth_xy=(380, 166),
        scale=1.0,
        head_box=(58, 106, 300, 428),
    ),
    FigureSpec(
        cid="story_mother_hd",
        display_name="Mummy / Sunita",
        source="story_mother_parts_sheet.png",
        body_box=(52, 138, 328, 1250),
        mouth_xy=(380, 170),
        scale=0.96,
    ),
    FigureSpec(
        cid="story_grandmother_hd",
        display_name="Dadiji",
        source="story_grandmother_parts_sheet.png",
        body_box=(54, 138, 326, 1248),
        mouth_xy=(380, 168),
        scale=0.95,
    ),
]


def crop_rgba(sheet: Image.Image, box: tuple[int, int, int, int], pad: int = 8) -> Image.Image:
    left, top, right, bottom = box
    im = sheet.crop((
        max(0, left - pad),
        max(0, top - pad),
        min(sheet.width, right + pad),
        min(sheet.height, bottom + pad),
    )).convert("RGBA")
    im = keep_largest_alpha_component(im)
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        return im
    l, t, r, b = bbox
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


def keep_largest_alpha_component(im: Image.Image) -> Image.Image:
    alpha = im.getchannel("A")
    w, h = im.size
    seen: set[tuple[int, int]] = set()
    best: set[tuple[int, int]] = set()
    pix = alpha.load()
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or pix[x, y] < 12:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            comp: set[tuple[int, int]] = set()
            while stack:
                cx, cy = stack.pop()
                comp.add((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and pix[nx, ny] >= 12:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    if not best:
        return im
    out_alpha = Image.new("L", im.size, 0)
    out_pix = out_alpha.load()
    for x, y in best:
        out_pix[x, y] = pix[x, y]
    out = im.copy()
    out.putalpha(out_alpha)
    return out


def mouth(kind: str) -> Image.Image:
    im = Image.new("RGBA", (120, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 60, 38
    lip = (112, 48, 42, 230)
    dark = (55, 20, 24, 245)
    tongue = (198, 86, 91, 235)
    if kind == "X":
        d.arc([30, 22, 90, 54], 15, 165, fill=lip, width=4)
        return im
    if kind == "sad":
        d.arc([32, 36, 88, 68], 195, 345, fill=lip, width=4)
        return im
    sizes = {
        "A": (15, 8),
        "B": (18, 11),
        "C": (25, 16),
        "D": (34, 24),
        "E": (21, 25),
        "F": (16, 18),
        "G": (29, 12),
        "H": (30, 18),
    }
    mw, mh = sizes[kind]
    d.ellipse([cx - mw, cy - mh, cx + mw, cy + mh], fill=dark, outline=lip, width=3)
    if mh > 13:
        d.ellipse([cx - mw * 0.45, cy + 2, cx + mw * 0.45, cy + mh * 0.84], fill=tongue)
    if kind in {"D", "G"}:
        d.chord([cx - mw + 4, cy - mh + 4, cx + mw - 4, cy + 6], 180, 360, fill=(255, 245, 235, 240))
    return im


def transparent(size: tuple[int, int] = (24, 24)) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def build_body(sheet: Image.Image, spec: FigureSpec) -> Image.Image:
    body = crop_rgba(sheet, spec.body_box)
    if spec.head_box is None:
        return body.resize((int(body.width * 940 / body.height), 940), Image.LANCZOS)

    head = crop_rgba(sheet, spec.head_box)
    head = head.resize((218, int(head.height * 218 / head.width)), Image.LANCZOS)
    body = body.resize((304, int(body.height * 304 / body.width)), Image.LANCZOS)
    canvas = Image.new("RGBA", (360, 1050), (0, 0, 0, 0))
    canvas.alpha_composite(head, ((canvas.width - head.width) // 2, 0))
    canvas.alpha_composite(body, ((canvas.width - body.width) // 2, 232))
    bbox = canvas.getchannel("A").getbbox()
    if bbox is not None:
        canvas = canvas.crop(bbox)
    return canvas.resize((int(canvas.width * 940 / canvas.height), 940), Image.LANCZOS)


def write_rig(spec: FigureSpec, out: Path) -> None:
    rig = {
        "type": "skeletal",
        "scale": spec.scale,
        "space": list(SPACE),
        "feet_y": FEET_Y,
        "cx": CX,
        "joints": {
            "neck": [380, 238],
            "shoulder_left": [380, 400],
            "shoulder_right": [380, 400],
            "hip_left": [380, 660],
            "hip_right": [380, 660],
        },
        "face": {"brows": [380, 200], "eyes": [380, 228], "mouth": list(spec.mouth_xy)},
        "pivot": {
            "head": [0.5, 0.5],
            "torso": [0.5, 0.5],
            "upper_arm": [0.5, 0.5],
            "forearm": [0.5, 0.5],
            "thigh": [0.5, 0.5],
            "shin": [0.5, 0.5],
        },
        "bone": {"upper_arm": 0.1, "forearm": 0.0, "thigh": 0.1, "shin": 0.0},
        "part_scale": {"mouth": 0.42},
        "neck_raise": 0,
        "torso_dy": -240,
        "render_padding": 220,
        "neck_stub": False,
        "joint_caps": {"shoulder": False, "elbow": False, "knee": False},
        "overlay_only": True,
    }
    (out / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def write_manifest(spec: FigureSpec, out: Path) -> None:
    manifest = {
        "id": spec.cid,
        "display_name": spec.display_name,
        "universe": "story",
        "asset_route": spec.route,
        "source_assets": {"front_parts_sheet": f"assets/cartoon/source/{spec.source}"},
        "capabilities": {
            "talk": True,
            "front_gestures": ["idle", "talk"],
            "side_walk_sprite": False,
            "side_walk_cycle_frames": False,
        },
        "notes": [
            "Sample video rig only.",
            "Replace with a full sliced Option-C rig before production use.",
        ],
    }
    (out / "asset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_one(spec: FigureSpec) -> None:
    sheet = Image.open(SOURCE / spec.source).convert("RGBA")
    out = CHARS / spec.cid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    build_body(sheet, spec).save(out / "torso.png")

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
        transparent().save(out / f"{name}.png")
    for kind in ("X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"):
        mouth(kind).save(out / f"mouth_{kind}.png")
    write_rig(spec, out)
    write_manifest(spec, out)
    print(f"rebuilt {out}")


def _pose_for(cid: str, t: float):
    from shiksha_cast.cartoon.build import _adv_pose

    actions = [{"who": cid, "do": "talk", "levels": [0.7] * 90, "start": 0.0, "end": 4.5}]
    return _adv_pose(cid, actions, t, 15, 0.0, 0.5, "right")


def preview() -> None:
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter

    DIST.mkdir(exist_ok=True)
    tw, th = 340, 500
    sheet = Image.new("RGBA", (len(SPECS) * tw, th), (255, 255, 255, 255))
    for idx, spec in enumerate(SPECS):
        ch = SkeletalCharacter(CHARS / spec.cid)
        bg = Image.new("RGBA", (tw, th), (238, 241, 246, 255))
        pose, _x, facing, bob = _pose_for(spec.cid, 0.9)
        ch.place(bg, pose, 0.5, th - 28, int(th * 0.88), facing=facing, bob=bob)
        d = ImageDraw.Draw(bg)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            font = ImageFont.load_default()
        d.rectangle([0, 0, tw, 34], fill=(40, 40, 60, 255))
        d.text((10, 5), spec.display_name, fill=(255, 255, 255, 255), font=font)
        d.rectangle([0, 0, tw - 1, th - 1], outline=(120, 130, 150, 255), width=2)
        sheet.alpha_composite(bg, (idx * tw, 0))
    out = DIST / "_story_family_sample_rigs_preview.png"
    sheet.convert("RGB").save(out)
    print(f"preview -> {out}")


def main() -> None:
    for spec in SPECS:
        build_one(spec)
    preview()


if __name__ == "__main__":
    main()
