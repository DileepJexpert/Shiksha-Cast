"""Build a small realistic social-story sample asset set.

The source PNGs exported by image tools often contain a checkerboard background
as real RGB pixels, not alpha. This script removes that edge-connected
checkerboard, then builds simple talking-figure rigs under the new
assets/characters/social_universe/ folder.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DOWNLOADS = Path.home() / "Downloads"
SOURCE = ROOT / "assets" / "source" / "social_universe"
CHARS = ROOT / "assets" / "characters" / "social_universe"
BGS = ROOT / "assets" / "backgrounds" / "social_universe"
DIST = ROOT / "dist"

SPACE = (720, 1040)
FEET = (360, 1010)


@dataclass(frozen=True)
class SocialFigure:
    cid: str
    display_name: str
    source_file: str
    mouth_xy: tuple[int, int]
    mouth_scale: float = 1.0
    height: int = 930


FIGURES = [
    SocialFigure("student_hd", "Ravi - Student", "00ccae56-eb62-4be1-a9ad-0262652be851.png", (360, 230), 0.48),
    SocialFigure("journalist_hd", "Meera - Journalist", "a27706d0-0f9b-4c62-b7cc-859624e89a17.png", (360, 218), 0.44),
    SocialFigure("officer_hd", "Honest Officer", "db52d846-35ac-4b50-9890-df1f37d2acce.png", (360, 212), 0.44),
    SocialFigure("clerk_hd", "File Clerk", "2100544c-f21e-496a-bccf-c8bdc2edec91.png", (360, 208), 0.44),
    SocialFigure("common_man_hd", "Common Man", "0fbc86ee-2997-40c0-9a79-bd48ac6a4132.png", (360, 220), 0.44),
    SocialFigure("politician_hd", "Netaji", "35d0de70-5088-4ec2-9dae-75ef96a9579d.png", (360, 214), 0.44),
]


def _background_like(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    return max(rgb) - min(rgb) <= 18 and min(rgb) >= 218


def remove_checkerboard(im: Image.Image) -> Image.Image:
    """Remove edge-connected neutral checkerboard pixels while preserving clothes."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    pixels = rgb.load()
    seen = bytearray(w * h)
    bg = bytearray(w * h)
    q: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        idx = y * w + x
        if seen[idx]:
            return
        seen[idx] = 1
        if _background_like(pixels[x, y]):
            bg[idx] = 1
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                push(nx, ny)

    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if bg[row + x]:
                ap[x, y] = 0
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    bbox = out.getchannel("A").getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def fit_to_space(im: Image.Image, target_h: int) -> Image.Image:
    scale = target_h / im.height
    resized = im.resize((max(1, int(im.width * scale)), target_h), Image.LANCZOS)
    canvas = Image.new("RGBA", SPACE, (0, 0, 0, 0))
    x = (SPACE[0] - resized.width) // 2
    y = FEET[1] - resized.height
    canvas.alpha_composite(resized, (x, y))
    return canvas


def mouth(kind: str, scale: float) -> Image.Image:
    base = Image.new("RGBA", (130, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    cx, cy = 65, 38
    lip = (90, 36, 32, 225)
    dark = (48, 18, 22, 245)
    tongue = (196, 82, 86, 230)
    if kind == "closed":
        d.arc([35, 24, 95, 52], 12, 168, fill=lip, width=4)
    elif kind == "half":
        d.ellipse([45, 24, 85, 54], fill=dark, outline=lip, width=3)
        d.ellipse([52, 38, 78, 56], fill=tongue)
    else:
        d.ellipse([36, 16, 94, 64], fill=dark, outline=lip, width=3)
        d.ellipse([46, 39, 84, 66], fill=tongue)
        d.chord([43, 19, 87, 39], 180, 360, fill=(255, 245, 235, 235))
    if abs(scale - 1.0) > 0.01:
        base = base.resize((max(1, int(base.width * scale)), max(1, int(base.height * scale))), Image.LANCZOS)
    return base


def full_canvas_overlay(part: Image.Image, xy: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGBA", SPACE, (0, 0, 0, 0))
    canvas.alpha_composite(part, (int(xy[0] - part.width / 2), int(xy[1] - part.height / 2)))
    return canvas


def write_rig(fig: SocialFigure, out: Path) -> None:
    rig = {
        "space": list(SPACE),
        "feet": list(FEET),
        "scale": 1.0,
        "parts": [{"name": "body", "img": "body.png", "pivot": [360, 520], "z": 0}],
        "eyes": {"open": "transparent.png", "closed": "transparent.png", "z": 10},
        "mouths": {
            "closed": "mouth_closed.png",
            "half": "mouth_half.png",
            "open": "mouth_open.png",
            "z": 20,
        },
    }
    (out / "rig.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")
    manifest = {
        "id": f"social_universe/{fig.cid}",
        "display_name": fig.display_name,
        "universe": "social_universe",
        "style": "realistic_talking_figure",
        "source_asset": f"assets/source/social_universe/{fig.source_file}",
        "capabilities": {"talk": True, "walk": False, "gesture": False},
        "notes": ["Sample talking rig from a complete full-body PNG; not final articulated puppet."],
    }
    (out / "asset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_character(fig: SocialFigure) -> None:
    src = DOWNLOADS / fig.source_file
    if not src.exists():
        raise FileNotFoundError(src)
    SOURCE.mkdir(parents=True, exist_ok=True)
    CHARS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, SOURCE / fig.source_file)

    out = CHARS / fig.cid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    clean = remove_checkerboard(Image.open(src))
    body = fit_to_space(clean, fig.height)
    body.save(out / "body.png")
    Image.new("RGBA", SPACE, (0, 0, 0, 0)).save(out / "transparent.png")
    full_canvas_overlay(mouth("closed", fig.mouth_scale), fig.mouth_xy).save(out / "mouth_closed.png")
    full_canvas_overlay(mouth("half", fig.mouth_scale), fig.mouth_xy).save(out / "mouth_half.png")
    full_canvas_overlay(mouth("open", fig.mouth_scale), fig.mouth_xy).save(out / "mouth_open.png")
    write_rig(fig, out)
    print(f"built {out}")


def background_public_office() -> None:
    BGS.mkdir(parents=True, exist_ok=True)
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (232, 238, 244))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 180], fill=(35, 69, 112))
    d.rectangle([0, 180, w, 750], fill=(239, 232, 218))
    d.rectangle([0, 750, w, h], fill=(174, 152, 128))
    d.rectangle([0, 742, w, 760], fill=(125, 100, 78))
    d.rectangle([120, 260, 720, 650], fill=(255, 255, 248), outline=(122, 102, 78), width=8)
    d.rectangle([1040, 280, 1750, 660], fill=(224, 237, 246), outline=(122, 102, 78), width=8)
    d.rectangle([1110, 330, 1680, 610], fill=(245, 250, 255))
    d.rectangle([0, 730, w, 790], fill=(118, 84, 52))
    d.rectangle([250, 670, 850, 820], fill=(136, 89, 45), outline=(78, 52, 32), width=6)
    d.rectangle([1080, 670, 1680, 820], fill=(136, 89, 45), outline=(78, 52, 32), width=6)
    d.rectangle([640, 635, 1280, 805], fill=(154, 101, 54), outline=(78, 52, 32), width=8)
    d.rectangle([710, 595, 1210, 670], fill=(235, 235, 225), outline=(80, 80, 75), width=5)
    for x in (310, 430, 550, 670):
        d.rectangle([x, 705, x + 70, 735], fill=(243, 213, 82), outline=(82, 64, 25), width=3)
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 54)
        text_font = ImageFont.truetype("arial.ttf", 38)
    except OSError:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    d.text((135, 275), "Exam Board Office", fill=(25, 45, 70), font=title_font)
    d.text((135, 360), "Complaint Desk", fill=(62, 70, 76), font=text_font)
    d.text((1135, 350), "Truth needs courage.", fill=(35, 69, 112), font=title_font)
    d.text((1135, 430), "No bribe. No paper leak.", fill=(76, 86, 94), font=text_font)
    im.save(BGS / "public_office.png")
    print(f"built {BGS / 'public_office.png'}")


def preview() -> None:
    from shiksha_cast.cartoon.character import Character

    DIST.mkdir(exist_ok=True)
    tw, th = 300, 430
    sheet = Image.new("RGBA", (len(FIGURES) * tw, th), (246, 248, 252, 255))
    for idx, fig in enumerate(FIGURES):
        bg = Image.new("RGBA", (tw, th), (238, 241, 246, 255))
        ch = Character(CHARS / fig.cid)
        ch.place(bg, {"angles": {}, "mouth": "open", "eye": "open"}, 0.5, th - 18, th * 0.92)
        d = ImageDraw.Draw(bg)
        d.rectangle([0, 0, tw, 32], fill=(30, 52, 86, 255))
        d.text((8, 8), fig.display_name, fill=(255, 255, 255, 255))
        sheet.alpha_composite(bg, (idx * tw, 0))
    out = DIST / "_social_universe_sample_preview.png"
    sheet.convert("RGB").save(out)
    print(f"preview {out}")


def main() -> None:
    for fig in FIGURES:
        build_character(fig)
    background_public_office()
    preview()


if __name__ == "__main__":
    main()
