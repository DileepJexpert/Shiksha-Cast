"""Reusable in-scene teaching graphics for Kinnu tutorial videos.

Two layers, both pure functions that paint onto an RGBA frame:

  * ``draw_board``   -- a classroom chalkboard with a title and lines that are
                        revealed one-by-one over time (the core of maths
                        step-by-step solving, word/letter cards, recaps, ...).
                        It lives in WORLD space (behind the characters, so the
                        camera zoom/pan moves it like part of the scene).
  * ``draw_overlays``-- timed UI graphics on top of everything: title banners
                        and speech-bubble callouts ("carry the 1!", "OOPS!").

Both consume plain JSON-serializable dicts so they pickle cleanly into the
render worker pool. Times are seconds relative to the start of the scene.

Board spec (scene["board"]):
    title: "Addition with Carry"
    pos:   [0.66, 0.40]      # center, fraction of W/H   (default right side)
    size:  [0.58, 0.62]      # w,h fraction of W/H
    lines:
      - { text: "27 + 5",          at: 0.5 }
      - { text: "7 + 5 = 12",      at: 2.0 }
      - { text: "Answer: 32",      at: 6.0, color: yellow, big: true }

Overlay spec items (scene["overlays"]):
    - { type: banner,  text: "Let's Learn!", start: 0.0, end: 3.0 }
    - { type: callout, text: "carry the 1!", pos: [0.6, 0.5], start: 4, end: 7 }
    - { type: label,   text: "1 + 1 = 2",    pos: [0.5, 0.8], start: 0, end: 5 }
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# kid-friendly fonts, in order of preference; fall back to PIL's default bitmap
_FONT_CANDIDATES = [
    "comicbd.ttf", "comici.ttf", "comic.ttf",      # Comic Sans family
    "ariblk.ttf", "arialbd.ttf", "arial.ttf",      # Arial family
    "segoeuib.ttf", "segoeui.ttf",
]
_WIN_FONTS = Path("C:/Windows/Fonts")
_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}

CHALK = (236, 240, 230, 255)
CHALK_YELLOW = (255, 226, 120, 255)
CHALK_PINK = (255, 175, 200, 255)
CHALK_BLUE = (150, 215, 255, 255)
BOARD_GREEN = (38, 74, 52, 255)
BOARD_FRAME = (138, 94, 58, 255)
BOARD_FRAME_DK = (104, 68, 40, 255)
INK = (40, 36, 44, 255)

_COLORS = {
    "white": CHALK, "yellow": CHALK_YELLOW, "pink": CHALK_PINK, "blue": CHALK_BLUE,
}


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    f = _font_cache.get(key)
    if f is not None:
        return f
    names = _FONT_CANDIDATES if bold else _FONT_CANDIDATES[2:]
    for name in names:
        p = _WIN_FONTS / name
        try:
            f = ImageFont.truetype(str(p) if p.exists() else name, size)
            break
        except Exception:  # noqa: BLE001
            continue
    if f is None:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def _fade(t: float, start: float, end: float, d: float = 0.25) -> float:
    """0..1 opacity with a short fade in/out; 0 outside [start, end]."""
    if t < start or t >= end:
        return 0.0
    if t < start + d:
        return (t - start) / d
    if t > end - d:
        return max(0.0, (end - t) / d)
    return 1.0


def _wrap(draw, text, font, max_w):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _text_centered(draw, cx, y, text, font, fill, outline=None, ow=0):
    w = draw.textlength(text, font=font)
    x = cx - w / 2
    if outline:
        for dx in (-ow, 0, ow):
            for dy in (-ow, 0, ow):
                if dx or dy:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)
    return w


# --------------------------------------------------------------------------- #
#  Chalkboard
# --------------------------------------------------------------------------- #
def draw_board(frame: Image.Image, board: dict, t: float, W: int, H: int) -> None:
    pos = board.get("pos", [0.66, 0.40])
    size = board.get("size", [0.58, 0.62])
    cw, ch = size[0] * W, size[1] * H
    cx, cy = pos[0] * W, pos[1] * H
    x0, y0, x1, y1 = cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2

    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # wooden frame + board
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=BOARD_FRAME,
                        outline=BOARD_FRAME_DK, width=6)
    m = max(14, int(cw * 0.022))
    bx0, by0, bx1, by1 = x0 + m, y0 + m, x1 - m, y1 - m
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=14, fill=BOARD_GREEN)

    inner_w = bx1 - bx0
    pad = inner_w * 0.07
    title = board.get("title")
    cur_y = by0 + (by1 - by0) * 0.05
    if title:
        tf = _font(max(20, int(ch * 0.105)))
        _text_centered(d, (bx0 + bx1) / 2, cur_y, str(title), tf, CHALK)
        ty = cur_y + (ch * 0.105) * 1.15
        d.line([bx0 + pad, ty, bx1 - pad, ty], fill=CHALK, width=3)
        cur_y = ty + (by1 - by0) * 0.06

    lines = board.get("lines", [])
    lh = (by1 - cur_y) / max(1, len(lines))
    lf = _font(max(18, int(min(lh * 0.62, ch * 0.085))))
    bf = _font(max(22, int(min(lh * 0.82, ch * 0.11))))
    for ln in lines:
        if isinstance(ln, str):
            ln = {"text": ln}
        if t < float(ln.get("at", 0.0)):
            continue
        font = bf if ln.get("big") else lf
        color = _COLORS.get(ln.get("color", "white"), CHALK)
        d.text((bx0 + pad, cur_y), str(ln.get("text", "")), font=font, fill=color)
        cur_y += lh

    frame.alpha_composite(layer)


# --------------------------------------------------------------------------- #
#  UI overlays (banners + callouts)
# --------------------------------------------------------------------------- #
def _draw_banner(d, text, cx, cy, W, H, color):
    font = _font(max(24, int(H * 0.052)))
    tw = d.textlength(text, font=font)
    pad_x, pad_y = H * 0.030, H * 0.018
    bw, bh = tw + pad_x * 2, (H * 0.052) + pad_y * 2
    x0, y0 = cx - bw / 2, cy - bh / 2
    fill = {"yellow": (255, 206, 64, 255), "green": (88, 196, 120, 255),
            "pink": (255, 140, 180, 255), "blue": (95, 180, 240, 255)}.get(color, (255, 206, 64, 255))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(bh / 2),
                        fill=fill, outline=(255, 255, 255, 255), width=5)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(bh / 2),
                        outline=INK, width=3)
    _text_centered(d, cx, y0 + pad_y - 2, text, font, INK)


def _draw_callout(d, text, cx, cy, W, H, color):
    font = _font(max(20, int(H * 0.040)))
    max_w = W * 0.28
    wrapped = _wrap(d, text, font, max_w)
    lh = H * 0.046
    tw = max((d.textlength(s, font=font) for s in wrapped), default=10)
    pad = H * 0.018
    bw = tw + pad * 2
    bh = lh * len(wrapped) + pad * 2
    x0, y0 = cx - bw / 2, cy - bh / 2
    border = {"yellow": (245, 195, 60, 255), "pink": (240, 110, 160, 255),
              "blue": (80, 165, 230, 255), "green": (80, 185, 115, 255)}.get(color, (240, 110, 160, 255))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=22,
                        fill=(255, 255, 255, 245), outline=border, width=6)
    # little tail pointing down-left toward the speaker
    d.polygon([(x0 + bw * 0.22, y0 + bh - 2), (x0 + bw * 0.10, y0 + bh + 26),
               (x0 + bw * 0.40, y0 + bh - 2)], fill=(255, 255, 255, 245), outline=border)
    yy = y0 + pad
    for s in wrapped:
        _text_centered(d, cx, yy, s, font, INK)
        yy += lh


def _draw_label(d, text, cx, cy, W, H, color):
    font = _font(max(22, int(H * 0.046)))
    fill = _COLORS.get(color, (255, 255, 255, 255))
    _text_centered(d, cx, cy - H * 0.023, text, font, fill,
                   outline=INK, ow=max(2, int(H * 0.003)))


def draw_overlays(frame: Image.Image, overlays: list, t: float, W: int, H: int) -> None:
    for ov in overlays:
        a = _fade(t, float(ov.get("start", 0.0)), float(ov.get("end", 1e9)))
        if a <= 0.0:
            continue
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        typ = ov.get("type", "banner")
        text = str(ov.get("text", ""))
        color = ov.get("color")
        if typ == "banner":
            pos = ov.get("pos", [0.5, 0.12])
        elif typ == "label":
            pos = ov.get("pos", [0.5, 0.85])
        else:
            pos = ov.get("pos", [0.5, 0.45])
        cx, cy = pos[0] * W, pos[1] * H
        if typ == "banner":
            _draw_banner(d, text, cx, cy, W, H, color)
        elif typ == "label":
            _draw_label(d, text, cx, cy, W, H, color)
        else:
            _draw_callout(d, text, cx, cy, W, H, color)
        if a < 1.0:
            alpha = layer.getchannel("A").point(lambda v: int(v * a))
            layer.putalpha(alpha)
        frame.alpha_composite(layer)
