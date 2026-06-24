"""Shared visual-branding constants and helpers (fonts, colors, gradients).

Used by the thumbnail and intro/outro asset generators so the channel looks
consistent across slides, thumbnails, and bumpers.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

CHANNEL_NAME = "KATIXO SHIKSHA"

# Dark-neon palette (matches scripts/make_slides.py)
BG_TOP = (10, 14, 30)
BG_BOTTOM = (22, 30, 58)
TEXT_LIGHT = (242, 246, 255)
TEXT_MUTED = (170, 182, 205)
SUB_YELLOW = (255, 214, 110)

ACCENTS = [(0, 229, 255), (124, 108, 255), (0, 230, 150), (255, 92, 122), (255, 193, 7)]

# Per-subject accent so a category reads at a glance.
SUBJECT_ACCENT = {
    "human-body": (255, 92, 122),
    "space": (124, 108, 255),
    "technology": (0, 229, 255),
    "physics": (0, 230, 150),
    "chemistry": (255, 193, 7),
    "earth-nature": (0, 230, 150),
    "class-chapter": (124, 108, 255),
    "general-knowledge": (255, 193, 7),
}

_FONT_DIR = "C:/Windows/Fonts/"
_FALLBACKS = ("seguibl.ttf", "segoeuib.ttf", "arialbd.ttf", "arial.ttf")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for n in (name, *_FALLBACKS):
        p = _FONT_DIR + n
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def accent_for(category_key: str, fallback_index: int = 0) -> tuple[int, int, int]:
    return SUBJECT_ACCENT.get(category_key, ACCENTS[fallback_index % len(ACCENTS)])


def gradient(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    for y in range(h):
        t = y / h
        draw.line(
            [(0, y), (w, y)],
            fill=tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)),
        )


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, maxw: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=fnt) <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def new_canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    gradient(d, w, h)
    return img, d
