"""Create green-board English lesson slides for kids.

The generator reads content/**/<episode-id>/script.yaml and renders:
  content/.../<episode-id>/slides/slide_001.png ...
  build/<episode-id>/slides/slide_001.png ...
  content/.../<episode-id>/<episode-id>.pdf

Usage:
  python scripts/make_english_board_slides.py ke01-a-or-an
  python scripts/make_english_board_slides.py --all
"""

from __future__ import annotations

import argparse
import glob
import os
import random
import shutil
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin  # noqa: F401

W, H = 1920, 1080
FONTS = "C:/Windows/Fonts"

WALL = (244, 236, 215)
WOOD = (116, 72, 34)
WOOD_DARK = (74, 43, 22)
BOARD = (24, 95, 67)
BOARD_DARK = (12, 58, 42)
CHALK = (246, 250, 238)
YELLOW = (250, 220, 92)
PINK = (255, 126, 158)
BLUE = (112, 202, 255)
ORANGE = (255, 174, 74)
RED = (244, 90, 90)
LIGHT_GREEN = (154, 232, 144)
KINNU_DIR = Path("assets/cartoon/kinnu_stills")
KINNU_POSE = {
    "title": "wave.up.png",
    "rule": "point.up.png",
    "examples": "point.up.png",
    "contrast": "point.up.png",
    "sentences": "read.up.png",
    "quiz": "think.up.png",
    "recap": "cheer.up.png",
}


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["comicbd.ttf", "segoeuib.ttf", "seguibl.ttf", "arialbd.ttf"]
        if bold
        else ["comic.ttf", "segoeui.ttf", "arial.ttf"]
    )
    for name in names:
        path = Path(FONTS) / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                pass
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw in str(text).split("\n"):
        cur = ""
        words = raw.split()
        if not words:
            lines.append("")
            continue
        for word in words:
            test = f"{cur} {word}".strip()
            if draw.textlength(test, font=fnt) <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines or [""]


def text_center(draw: ImageDraw.ImageDraw, text: str, cx: float, y: float, fnt, fill=CHALK) -> float:
    x = cx - draw.textlength(text, font=fnt) / 2
    draw.text((x + 2, y + 3), text, font=fnt, fill=(0, 0, 0))
    draw.text((x, y), text, font=fnt, fill=fill)
    return y + fnt.size * 1.18


def text_left(draw: ImageDraw.ImageDraw, text: str, x: float, y: float, fnt, fill=CHALK) -> float:
    draw.text((x + 2, y + 3), text, font=fnt, fill=(0, 0, 0))
    draw.text((x, y), text, font=fnt, fill=fill)
    return y + fnt.size * 1.2


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 3) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paste_kinnu(img: Image.Image, kind: str, small: bool = False) -> None:
    pose = KINNU_POSE.get(kind, "wave.up.png")
    path = KINNU_DIR / pose
    if not path.exists():
        return
    kinnu = Image.open(path).convert("RGBA")
    bbox = kinnu.getbbox()
    if bbox:
        kinnu = kinnu.crop(bbox)
    target_h = 245 if small else 310
    scale = target_h / kinnu.height
    target_w = max(1, int(kinnu.width * scale))
    kinnu = kinnu.resize((target_w, target_h), Image.Resampling.LANCZOS)

    shadow = Image.new("RGBA", kinnu.size, (0, 0, 0, 0))
    shadow_alpha = kinnu.getchannel("A").point(lambda a: int(a * 0.28))
    shadow.putalpha(shadow_alpha)
    x = W - target_w - 135
    y = 805 - target_h
    img.alpha_composite(shadow, (x + 10, y + 14))
    img.alpha_composite(kinnu, (x, y))


def board_base(slide_no: int, total: int, chapter: str, brand: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), WALL + (255,))
    d = ImageDraw.Draw(img)

    # Soft wall gradient.
    top, bot = WALL, (230, 218, 195)
    for y in range(H):
        t = y / H
        col = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=col)

    # Floor + board frame.
    d.rectangle([0, 905, W, H], fill=(181, 150, 113))
    d.rectangle([96, 80, W - 96, 890], fill=WOOD_DARK)
    d.rectangle([126, 110, W - 126, 860], fill=WOOD)
    d.rectangle([156, 140, W - 156, 830], fill=BOARD_DARK)
    d.rectangle([176, 160, W - 176, 810], fill=BOARD)

    # Chalk dust texture.
    rng = random.Random(slide_no * 1009)
    for _ in range(900):
        x = rng.randint(185, W - 185)
        y = rng.randint(170, 800)
        val = rng.randint(80, 135)
        d.point((x, y), fill=(val, min(150, val + 30), val))

    d.rectangle([280, 830, 1640, 850], fill=(112, 78, 43))
    for x in [420, 470, 520]:
        d.rounded_rectangle([x, 820, x + 80, 835], radius=8, fill=(235, 235, 220))
    d.rounded_rectangle([1420, 818, 1535, 838], radius=8, fill=(250, 120, 130))

    small = font(30, False)
    d.text((170, 118), brand.upper(), font=font(34), fill=YELLOW)
    badge = f"{slide_no:02d}/{total:02d}"
    d.text((W - 170 - d.textlength(badge, font=small), 122), badge, font=small, fill=(218, 238, 220))
    d.text((170, 860), chapter, font=font(26, False), fill=(90, 68, 42))
    return img, d


def draw_icon(draw: ImageDraw.ImageDraw, name: str, cx: int, cy: int, size: int) -> None:
    n = (name or "").lower()
    r = size // 2
    if n in {"apple", "orange"}:
        color = RED if n == "apple" else ORANGE
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=(60, 30, 20), width=5)
        draw.ellipse([cx - r // 3, cy - r - 22, cx + r // 3, cy - r + 12], fill=(80, 140, 65))
        draw.line([cx, cy - r - 5, cx + 10, cy - r - 28], fill=(70, 35, 20), width=5)
        draw.ellipse([cx - r // 2, cy - r // 2, cx - r // 6, cy - r // 5], fill=(255, 225, 180))
    elif n == "star":
        points = []
        import math

        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else int(r * 0.45)
            points.append((cx + int(math.cos(ang) * rr), cy + int(math.sin(ang) * rr)))
        draw.polygon(points, fill=YELLOW, outline=(110, 75, 20))
    elif n == "egg":
        draw.ellipse([cx - r + 8, cy - r - 10, cx + r - 8, cy + r + 18], fill=(255, 248, 218), outline=(90, 70, 50), width=5)
        draw.ellipse([cx - 22, cy - 18, cx + 22, cy + 26], fill=YELLOW)
    elif n == "umbrella":
        draw.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=PINK, outline=(70, 20, 60), width=5)
        draw.line([cx, cy, cx, cy + r], fill=CHALK, width=7)
        draw.arc([cx - 34, cy + r - 10, cx + 34, cy + r + 60], 0, 180, fill=CHALK, width=7)
        for dx in [-55, 0, 55]:
            draw.line([cx, cy - r + 8, cx + dx, cy], fill=(120, 40, 90), width=4)
    elif n == "ball":
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE, outline=(20, 45, 80), width=5)
        draw.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 0, 360, fill=CHALK, width=5)
        draw.arc([cx - r // 2, cy - r, cx + r // 2, cy + r], 0, 360, fill=CHALK, width=5)
    elif n == "cat":
        draw.polygon([(cx - 62, cy - 20), (cx - 30, cy - 70), (cx - 8, cy - 20)], fill=ORANGE, outline=(70, 35, 20))
        draw.polygon([(cx + 62, cy - 20), (cx + 30, cy - 70), (cx + 8, cy - 20)], fill=ORANGE, outline=(70, 35, 20))
        draw.ellipse([cx - 70, cy - 60, cx + 70, cy + 65], fill=ORANGE, outline=(70, 35, 20), width=5)
        draw.ellipse([cx - 36, cy - 12, cx - 18, cy + 8], fill=(20, 20, 20))
        draw.ellipse([cx + 18, cy - 12, cx + 36, cy + 8], fill=(20, 20, 20))
        draw.polygon([(cx, cy + 12), (cx - 10, cy + 28), (cx + 10, cy + 28)], fill=PINK)
        draw.arc([cx - 30, cy + 18, cx, cy + 52], 0, 70, fill=(40, 20, 20), width=4)
        draw.arc([cx, cy + 18, cx + 30, cy + 52], 110, 180, fill=(40, 20, 20), width=4)
    elif n == "dog":
        draw.ellipse([cx - 68, cy - 58, cx + 68, cy + 62], fill=(180, 110, 55), outline=(70, 35, 20), width=5)
        draw.ellipse([cx - 96, cy - 30, cx - 48, cy + 50], fill=(105, 64, 38), outline=(70, 35, 20), width=4)
        draw.ellipse([cx + 48, cy - 30, cx + 96, cy + 50], fill=(105, 64, 38), outline=(70, 35, 20), width=4)
        draw.ellipse([cx - 38, cy - 20, cx - 18, cy + 2], fill=(20, 20, 20))
        draw.ellipse([cx + 18, cy - 20, cx + 38, cy + 2], fill=(20, 20, 20))
        draw.ellipse([cx - 18, cy + 12, cx + 18, cy + 36], fill=(25, 18, 16))
        draw.arc([cx - 34, cy + 26, cx, cy + 58], 5, 80, fill=(40, 20, 20), width=4)
        draw.arc([cx, cy + 26, cx + 34, cy + 58], 100, 175, fill=(40, 20, 20), width=4)
    elif n == "ice cream":
        draw.polygon([(cx - 46, cy + 12), (cx + 46, cy + 12), (cx, cy + 102)], fill=(224, 154, 83), outline=(80, 45, 20))
        draw.line([cx - 28, cy + 45, cx + 28, cy + 80], fill=(153, 85, 42), width=4)
        draw.line([cx + 28, cy + 45, cx - 28, cy + 80], fill=(153, 85, 42), width=4)
        draw.ellipse([cx - 64, cy - 72, cx + 64, cy + 38], fill=PINK, outline=(90, 35, 60), width=5)
        draw.ellipse([cx - 20, cy - 64, cx + 20, cy - 30], fill=CHALK)
    elif n == "mango":
        draw.ellipse([cx - 62, cy - 70, cx + 68, cy + 68], fill=(255, 192, 49), outline=(92, 65, 20), width=5)
        draw.ellipse([cx - 42, cy - 42, cx + 18, cy + 48], fill=(248, 136, 48))
        draw.ellipse([cx + 12, cy - 94, cx + 70, cy - 48], fill=(74, 150, 62), outline=(30, 80, 35), width=3)
        draw.line([cx + 8, cy - 70, cx + 28, cy - 96], fill=(82, 45, 20), width=6)
    elif n == "kite":
        draw.polygon([(cx, cy - 96), (cx + 80, cy - 8), (cx, cy + 84), (cx - 80, cy - 8)], fill=BLUE, outline=(20, 45, 80))
        draw.line([cx, cy - 96, cx, cy + 84], fill=CHALK, width=4)
        draw.line([cx - 80, cy - 8, cx + 80, cy - 8], fill=CHALK, width=4)
        draw.line([cx, cy + 84, cx + 45, cy + 128, cx + 20, cy + 158], fill=CHALK, width=4)
        draw.polygon([(cx + 35, cy + 118), (cx + 62, cy + 116), (cx + 50, cy + 138)], fill=PINK)
    elif n == "school":
        draw.rectangle([cx - 94, cy - 38, cx + 94, cy + 76], fill=(252, 198, 88), outline=(92, 65, 20), width=5)
        draw.polygon([(cx - 112, cy - 38), (cx, cy - 112), (cx + 112, cy - 38)], fill=RED, outline=(92, 30, 20))
        draw.rectangle([cx - 24, cy + 12, cx + 24, cy + 76], fill=BLUE, outline=(20, 45, 80), width=4)
        for wx in [-62, 46]:
            draw.rectangle([cx + wx, cy - 8, cx + wx + 32, cy + 26], fill=CHALK, outline=(20, 45, 80), width=3)
        f = font(28)
        label = "SCHOOL"
        draw.text((cx - draw.textlength(label, font=f) / 2, cy - 56), label, font=f, fill=CHALK)
    elif n == "elephant":
        draw.ellipse([cx - 86, cy - 48, cx + 52, cy + 62], fill=(155, 170, 178), outline=(55, 70, 80), width=5)
        draw.ellipse([cx - 110, cy - 18, cx - 40, cy + 58], fill=(175, 190, 198), outline=(55, 70, 80), width=4)
        draw.ellipse([cx + 28, cy - 14, cx + 96, cy + 52], fill=(175, 190, 198), outline=(55, 70, 80), width=4)
        draw.ellipse([cx - 34, cy - 18, cx - 14, cy + 2], fill=(20, 20, 20))
        draw.line([cx - 8, cy + 18, cx - 4, cy + 86, cx - 28, cy + 104], fill=(110, 125, 135), width=18)
        draw.arc([cx - 10, cy + 58, cx + 40, cy + 124], 110, 210, fill=(110, 125, 135), width=8)
    elif n == "book":
        draw.rounded_rectangle([cx - 82, cy - 58, cx + 6, cy + 58], radius=8, fill=BLUE, outline=(20, 40, 70), width=5)
        draw.rounded_rectangle([cx - 6, cy - 58, cx + 82, cy + 58], radius=8, fill=(82, 185, 130), outline=(20, 70, 45), width=5)
        draw.line([cx, cy - 55, cx, cy + 55], fill=CHALK, width=4)
        for yy in [-28, -4, 20]:
            draw.line([cx - 65, cy + yy, cx - 20, cy + yy], fill=CHALK, width=3)
            draw.line([cx + 20, cy + yy, cx + 65, cy + yy], fill=CHALK, width=3)
    elif n == "pencil":
        draw.polygon([(cx - 95, cy + 36), (cx + 55, cy - 65), (cx + 82, cy - 25), (cx - 70, cy + 76)], fill=YELLOW, outline=(80, 55, 20))
        draw.polygon([(cx + 55, cy - 65), (cx + 100, cy - 92), (cx + 82, cy - 25)], fill=(230, 190, 140), outline=(80, 55, 20))
        draw.polygon([(cx + 90, cy - 85), (cx + 100, cy - 92), (cx + 96, cy - 72)], fill=(30, 30, 30))
        draw.line([cx - 80, cy + 68, cx + 70, cy - 34], fill=(210, 130, 35), width=5)
    elif n in {"bag", "schoolbag"}:
        draw.rounded_rectangle([cx - 72, cy - 35, cx + 72, cy + 72], radius=22, fill=RED, outline=(70, 20, 20), width=5)
        draw.arc([cx - 40, cy - 75, cx + 40, cy - 4], 180, 360, fill=CHALK, width=8)
        draw.rectangle([cx - 50, cy + 8, cx + 50, cy + 32], fill=ORANGE, outline=(70, 35, 20), width=4)
    elif n in {"near", "far"}:
        scale = 1.0 if n == "near" else 0.55
        rr = int(r * scale)
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=BLUE, outline=CHALK, width=5)
        label = "near" if n == "near" else "far"
        f = font(30)
        draw.text((cx - draw.textlength(label, font=f) / 2, cy + rr + 12), label, font=f, fill=CHALK)
    else:
        draw.rounded_rectangle([cx - 78, cy - 60, cx + 78, cy + 60], radius=18, fill=(55, 130, 95), outline=CHALK, width=4)
        initial = (name[:1] or "?").upper()
        f = font(78)
        draw.text((cx - draw.textlength(initial, font=f) / 2, cy - 50), initial, font=f, fill=YELLOW)


def example_card(draw, box, article: str, word: str, icon: str, color=YELLOW) -> None:
    x1, y1, x2, y2 = box
    rounded(draw, box, 26, (36, 115, 82), outline=(220, 245, 215), width=4)
    draw_icon(draw, icon, int((x1 + x2) / 2), int(y1 + 110), 84)
    f_big = font(62)
    f_word = font(42, False)
    text = article
    draw.text(((x1 + x2) / 2 - draw.textlength(text, font=f_big) / 2, y1 + 215), text, font=f_big, fill=color)
    label = word
    draw.text(((x1 + x2) / 2 - draw.textlength(label, font=f_word) / 2, y1 + 292), label, font=f_word, fill=CHALK)


def render_slide(ep_dir: Path, ep_id: str, data: dict, slide: dict, n: int, total: int) -> Image.Image:
    chapter = data.get("chapter", ep_id)
    brand = data.get("brand", "Katixo English")
    img, d = board_base(n, total, chapter, brand)
    kind = (slide.get("visual") or {}).get("kind", "title")
    v = slide.get("visual") or slide
    left, top, right, bottom = 230, 205, W - 230, 760

    if kind == "title":
        y = 235
        for line in wrap(d, v.get("title", chapter), font(102), right - left):
            y = text_center(d, line, W / 2, y, font(102), YELLOW)
        y += 20
        for line in wrap(d, v.get("subtitle", ""), font(50, False), right - left):
            y = text_center(d, line, W / 2, y, font(50, False), CHALK)
        for i, item in enumerate(v.get("icons", [])):
            draw_icon(d, item, 680 + i * 190, 650, 65)

    elif kind == "rule":
        text_center(d, v.get("title", "Rule"), W / 2, 210, font(78), YELLOW)
        rounded(d, [280, 330, 1640, 495], 28, (18, 75, 54), outline=CHALK, width=4)
        for i, line in enumerate(wrap(d, v.get("rule", ""), font(62), 1240)[:2]):
            text_center(d, line, W / 2, 350 + i * 76, font(62), CHALK)
        y = 570
        for bullet in v.get("bullets", []):
            d.ellipse([330, y + 14, 354, y + 38], fill=YELLOW)
            for line in wrap(d, bullet, font(44, False), 1180):
                text_left(d, line, 380, y, font(44, False), CHALK)
                y += 58
            y += 14

    elif kind == "examples":
        text_center(d, v.get("title", "Examples"), W / 2, 205, font(76), YELLOW)
        items = v.get("items", [])[:4]
        card_w, card_h, gap = 300, 365, 42
        total_w = len(items) * card_w + max(0, len(items) - 1) * gap
        x = int(W / 2 - total_w / 2)
        for item in items:
            example_card(
                d,
                [x, 330, x + card_w, 330 + card_h],
                str(item.get("article", "")),
                str(item.get("word", "")),
                str(item.get("icon", "")),
                tuple(item.get("color", YELLOW)),
            )
            x += card_w + gap

    elif kind == "contrast":
        text_center(d, v.get("title", "Compare"), W / 2, 198, font(76), YELLOW)
        mid = W // 2
        rounded(d, [260, 315, mid - 38, 700], 28, (20, 82, 60), outline=BLUE, width=5)
        rounded(d, [mid + 38, 315, W - 260, 700], 28, (20, 82, 60), outline=PINK, width=5)
        text_center(d, v.get("left_title", ""), (260 + mid - 38) / 2, 345, font(70), BLUE)
        text_center(d, v.get("right_title", ""), (mid + 38 + W - 260) / 2, 345, font(70), PINK)
        draw_icon(d, v.get("left_icon", "near"), int((260 + mid - 38) / 2), 500, 95)
        draw_icon(d, v.get("right_icon", "far"), int((mid + 38 + W - 260) / 2), 500, 95)
        text_center(d, v.get("left_text", ""), (260 + mid - 38) / 2, 615, font(44, False), CHALK)
        text_center(d, v.get("right_text", ""), (mid + 38 + W - 260) / 2, 615, font(44, False), CHALK)

    elif kind == "sentences":
        text_center(d, v.get("title", "Sentences"), W / 2, 200, font(76), YELLOW)
        y = 335
        for line in v.get("lines", []):
            rounded(d, [300, y - 16, 1620, y + 76], 20, (20, 82, 60), outline=(185, 232, 190), width=3)
            text_center(d, str(line), W / 2, y, font(50, False), CHALK)
            y += 118

    elif kind == "quiz":
        text_center(d, v.get("title", "Your Turn"), W / 2, 198, font(78), YELLOW)
        prompt = v.get("prompt", "")
        for i, line in enumerate(wrap(d, prompt, font(68), 1300)):
            text_center(d, line, W / 2, 310 + i * 78, font(68), CHALK)
        choices = v.get("choices", [])
        y = 520
        for idx, choice in enumerate(choices[:3]):
            x = 470 + idx * 340
            fill = (34, 118, 80)
            outline = YELLOW if choice == v.get("answer") else (210, 238, 215)
            rounded(d, [x, y, x + 290, y + 115], 24, fill, outline=outline, width=5)
            text_center(d, str(choice), x + 145, y + 28, font(50), outline)
        hint = v.get("hint", "")
        if hint:
            text_center(d, hint, W / 2, 690, font(42, False), BLUE)

    elif kind == "recap":
        text_center(d, v.get("title", "Remember"), W / 2, 198, font(78), YELLOW)
        y = 330
        colors = [YELLOW, BLUE, PINK, LIGHT_GREEN]
        for i, bullet in enumerate(v.get("bullets", [])):
            col = colors[i % len(colors)]
            d.rounded_rectangle([315, y + 8, 365, y + 58], radius=14, fill=col)
            d.text((333, y + 8), str(i + 1), font=font(34), fill=(25, 60, 45))
            for line in wrap(d, bullet, font(52, False), 1160):
                text_left(d, line, 400, y, font(52, False), CHALK)
                y += 66
            y += 30

    else:
        text_center(d, v.get("title", chapter), W / 2, 260, font(88), YELLOW)
        for i, line in enumerate(wrap(d, v.get("subtitle", ""), font(52, False), 1300)):
            text_center(d, line, W / 2, 430 + i * 64, font(52, False), CHALK)

    paste_kinnu(img, kind, small=kind in {"examples", "contrast", "sentences"})
    return img


def find_episode(ep_id: str) -> Path:
    matches = [Path(p).parent for p in glob.glob(f"content/**/{ep_id}/script.yaml", recursive=True)]
    if not matches:
        raise FileNotFoundError(f"Episode not found: {ep_id}")
    return matches[0]


def build_episode(ep_id: str) -> None:
    ep_dir = find_episode(ep_id)
    data = yaml.safe_load((ep_dir / "script.yaml").read_text(encoding="utf-8")) or {}
    slides = data.get("slides", [])
    if not slides:
        raise ValueError(f"No slides in {ep_dir / 'script.yaml'}")

    out_dirs = [ep_dir / "slides", Path("build") / ep_id / "slides"]
    for out_dir in out_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("slide_*.png"):
            old.unlink()

    rendered: list[Image.Image] = []
    for i, slide in enumerate(slides, start=1):
        img = render_slide(ep_dir, ep_id, data, slide, i, len(slides))
        rendered.append(img.convert("RGB"))
        for out_dir in out_dirs:
            img.convert("RGB").save(out_dir / f"slide_{i:03d}.png", quality=95)

    pdf_path = ep_dir / f"{ep_id}.pdf"
    rendered[0].save(pdf_path, save_all=True, append_images=rendered[1:])

    # Keep the build copy useful for the existing video pipeline.
    shutil.copy2(pdf_path, Path("build") / ep_id / f"{ep_id}.pdf")
    print(f"{ep_id}: {len(slides)} slides -> {ep_dir / 'slides'}")
    print(f"{ep_id}: pdf -> {pdf_path}")


def all_english_board_episode_ids() -> list[str]:
    ids = []
    for path in glob.glob("content/kids-english/**/script.yaml", recursive=True):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if data.get("template") == "english_board":
            ids.append(Path(path).parent.name)
    return sorted(ids)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", nargs="?", help="Episode id, e.g. ke01-a-or-an")
    parser.add_argument("--all", action="store_true", help="Render all english_board decks")
    args = parser.parse_args()

    if args.all:
        ids = all_english_board_episode_ids()
    elif args.episode:
        ids = [args.episode]
    else:
        parser.error("Provide an episode id or --all")

    for ep_id in ids:
        build_episode(ep_id)


if __name__ == "__main__":
    main()
