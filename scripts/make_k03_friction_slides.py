from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "kinnu"
OUT = ROOT / "build" / "k03-friction" / "slides"
W, H = 1920, 1080


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts/seguibl.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_BLACK = "seguibl.ttf"
FONT_BOLD = "segoeuib.ttf"
FONT_REG = "segoeui.ttf"


def base_lab(tint: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    bg_path = ASSETS / "background-science-lab.png"
    if bg_path.exists():
        img = Image.open(bg_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGBA", (W, H), (235, 248, 255, 255))
    overlay = Image.new("RGBA", (W, H), (*tint, 45))
    img.alpha_composite(overlay)
    return img


def draw_title(d: ImageDraw.ImageDraw, text: str, y: int = 70, size: int = 72):
    d.text(
        (W // 2, y),
        text,
        font=font(FONT_BLACK, size),
        fill=(40, 93, 220),
        anchor="ma",
        stroke_width=8,
        stroke_fill=(255, 255, 255),
    )


def draw_badge(d: ImageDraw.ImageDraw, n: int):
    d.rounded_rectangle([44, H - 88, 250, H - 35], radius=20, fill=(255, 255, 255), outline=(50, 92, 215), width=4)
    d.text((147, H - 62), f"Slide {n} of 8", font=font(FONT_BOLD, 28), fill=(50, 92, 215), anchor="mm")


def draw_logo(img: Image.Image):
    d = ImageDraw.Draw(img)
    x, y = 46, 38
    d.ellipse([x, y, x + 118, y + 118], fill=(255, 255, 255), outline=(43, 92, 215), width=6)
    d.ellipse([x + 18, y + 26, x + 62, y + 70], fill=(255, 255, 255), outline=(20, 20, 20), width=3)
    d.ellipse([x + 30, y + 44, x + 36, y + 51], fill=(20, 20, 20))
    d.ellipse([x + 46, y + 44, x + 52, y + 51], fill=(20, 20, 20))
    d.arc([x + 28, y + 48, x + 54, y + 66], 0, 180, fill=(20, 20, 20), width=3)
    d.polygon([(x + 45, y + 24), (x + 70, y + 10), (x + 72, y + 38)], fill=(255, 38, 145), outline=(20, 20, 20))
    d.text((x + 83, y + 63), "K", font=font(FONT_BLACK, 52), fill=(43, 92, 215), anchor="mm")


def draw_arrow(d: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int], width: int = 14):
    d.line([start, end], fill=color, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 34
    spread = 0.55
    pts = [
        end,
        (end[0] - math.cos(ang - spread) * length, end[1] - math.sin(ang - spread) * length),
        (end[0] - math.cos(ang + spread) * length, end[1] - math.sin(ang + spread) * length),
    ]
    d.polygon(pts, fill=color)


def load_pose(index: int) -> Image.Image:
    sheet = Image.open(ASSETS / "kinnu-pose-sheet.png").convert("RGBA")
    seg_w = sheet.width / 6
    left = int(index * seg_w)
    right = int((index + 1) * seg_w)
    seg = sheet.crop((max(0, left - 18), 0, min(sheet.width, right + 18), sheet.height))
    alpha = seg.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        seg = seg.crop(bbox)
    return seg


POSES = [load_pose(i) for i in range(6)]


def place(img: Image.Image, pose_idx: int, x: int, y: int, height: int):
    pose = POSES[pose_idx]
    scale = height / pose.height
    size = (int(pose.width * scale), int(pose.height * scale))
    pose = pose.resize(size, Image.Resampling.LANCZOS)
    img.alpha_composite(pose, (x - size[0] // 2, y - size[1]))


def toy_car(d: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, color=(255, 96, 84)):
    w, h = int(230 * scale), int(92 * scale)
    d.rounded_rectangle([x, y, x + w, y + h], radius=int(24 * scale), fill=color, outline=(20, 20, 20), width=max(4, int(6 * scale)))
    d.polygon([(x + 45 * scale, y), (x + 95 * scale, y - 48 * scale), (x + 165 * scale, y - 48 * scale), (x + 205 * scale, y)], fill=(255, 210, 80), outline=(20, 20, 20))
    for cx in [x + 52 * scale, x + 180 * scale]:
        d.ellipse([cx - 25 * scale, y + h - 18 * scale, cx + 25 * scale, y + h + 32 * scale], fill=(20, 20, 20))
        d.ellipse([cx - 10 * scale, y + h - 3 * scale, cx + 10 * scale, y + h + 17 * scale], fill=(255, 255, 255))


def surface_card(d: ImageDraw.ImageDraw, box, label: str, fill, outline=(40, 40, 40), pattern: str | None = None):
    d.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=5)
    x1, y1, x2, y2 = box
    if pattern == "rough":
        for x in range(x1 + 25, x2 - 20, 35):
            for y in range(y1 + 25, y2 - 20, 28):
                d.line([x, y, x + 14, y + 10], fill=(126, 82, 40), width=4)
    elif pattern == "ice":
        for x in range(x1 + 35, x2 - 20, 75):
            d.line([x, y1 + 40, x + 38, y2 - 35], fill=(255, 255, 255), width=5)
    d.text(((x1 + x2) // 2, y2 - 42), label, font=font(FONT_BOLD, 34), fill=(30, 50, 110), anchor="mm")


def save(img: Image.Image, n: int):
    draw_logo(img)
    draw_badge(ImageDraw.Draw(img), n)
    OUT.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT / f"slide_{n:03d}.png", quality=95)


def starburst(d: ImageDraw.ImageDraw, cx: int, cy: int, r1: int, r2: int, points: int, fill, outline):
    pts = []
    for i in range(points * 2):
        r = r1 if i % 2 == 0 else r2
        a = -math.pi / 2 + i * math.pi / points
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.polygon(pts, fill=fill, outline=outline)


def wet_floor_sign(d: ImageDraw.ImageDraw, x: int, y: int):
    d.polygon([(x, y + 220), (x + 88, y), (x + 176, y + 220)], fill=(255, 214, 55), outline=(40, 40, 40))
    d.line([(x + 88, y + 32), (x + 88, y + 135)], fill=(40, 40, 40), width=10)
    d.ellipse([x + 78, y + 158, x + 98, y + 178], fill=(40, 40, 40))
    d.rounded_rectangle([x - 18, y + 218, x + 194, y + 270], radius=16, fill=(255, 255, 255), outline=(40, 40, 40), width=4)
    d.text((x + 88, y + 244), "Wet Floor", font=font(FONT_BOLD, 28), fill=(50, 70, 130), anchor="mm")


def draw_falling_kinnu(img: Image.Image, cx: int, cy: int, scale: float = 1.0, angle: float = -24):
    layer = Image.new("RGBA", (720, 640), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = scale
    ox, oy = 360, 300
    black = (18, 18, 18)
    yellow = (255, 215, 26)
    blue = (28, 128, 224)

    # Arms and legs flying upward.
    d.line([(ox - 80 * s, oy + 80 * s), (ox - 225 * s, oy - 35 * s)], fill=black, width=int(12 * s))
    d.line([(ox + 82 * s, oy + 82 * s), (ox + 230 * s, oy - 80 * s)], fill=black, width=int(12 * s))
    d.ellipse([ox - 250 * s, oy - 70 * s, ox - 185 * s, oy - 8 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))
    d.ellipse([ox + 205 * s, oy - 112 * s, ox + 270 * s, oy - 48 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))

    d.line([(ox - 48 * s, oy + 170 * s), (ox - 145 * s, oy + 15 * s)], fill=black, width=int(13 * s))
    d.line([(ox + 42 * s, oy + 170 * s), (ox + 130 * s, oy + 2 * s)], fill=black, width=int(13 * s))
    d.rounded_rectangle([ox - 185 * s, oy - 45 * s, ox - 105 * s, oy + 115 * s], radius=int(26 * s), fill=blue, outline=black, width=int(6 * s))
    d.rounded_rectangle([ox + 92 * s, oy - 55 * s, ox + 170 * s, oy + 105 * s], radius=int(26 * s), fill=blue, outline=black, width=int(6 * s))
    d.ellipse([ox - 210 * s, oy - 105 * s, ox - 105 * s, oy - 25 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))
    d.ellipse([ox + 110 * s, oy - 125 * s, ox + 215 * s, oy - 45 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))

    # Body.
    d.rounded_rectangle([ox - 92 * s, oy + 80 * s, ox + 92 * s, oy + 235 * s], radius=int(34 * s), fill=yellow, outline=black, width=int(8 * s))
    d.polygon([(ox - 110 * s, oy + 215 * s), (ox + 110 * s, oy + 215 * s), (ox + 148 * s, oy + 285 * s), (ox - 148 * s, oy + 285 * s)], fill=yellow, outline=black)
    for bx in [-30, 0, 30]:
        d.ellipse([ox + bx * s - 8 * s, oy + 130 * s, ox + bx * s + 8 * s, oy + 146 * s], fill=(255, 255, 255))

    # Head.
    d.ellipse([ox - 128 * s, oy - 100 * s, ox + 128 * s, oy + 156 * s], fill=(255, 255, 255), outline=black, width=int(8 * s))
    d.pieslice([ox - 138 * s, oy - 132 * s, ox + 138 * s, oy + 62 * s], 180, 360, fill=(22, 22, 26), outline=black, width=int(6 * s))
    for off in [-48, -18, 14, 48]:
        d.arc([ox - 35 * s + off * s, oy - 145 * s, ox + 70 * s + off * s, oy - 18 * s], 205, 305, fill=black, width=int(5 * s))
    d.polygon([(ox - 105 * s, oy - 100 * s), (ox - 172 * s, oy - 146 * s), (ox - 156 * s, oy - 62 * s)], fill=(255, 38, 145), outline=black)
    d.polygon([(ox - 104 * s, oy - 100 * s), (ox - 47 * s, oy - 148 * s), (ox - 50 * s, oy - 58 * s)], fill=(255, 38, 145), outline=black)
    d.ellipse([ox - 122 * s, oy - 126 * s, ox - 72 * s, oy - 75 * s], fill=(255, 38, 145), outline=black, width=int(5 * s))

    # Spiral eyes and surprised mouth.
    for ex in [ox - 48 * s, ox + 48 * s]:
        d.ellipse([ex - 27 * s, oy - 8 * s, ex + 27 * s, oy + 46 * s], fill=(255, 255, 255), outline=black, width=int(5 * s))
        for rr in [22, 15, 8]:
            d.arc([ex - rr * s, oy + 19 * s - rr * s, ex + rr * s, oy + 19 * s + rr * s], 20, 330, fill=black, width=int(4 * s))
    d.ellipse([ox - 24 * s, oy + 76 * s, ox + 26 * s, oy + 124 * s], fill=(24, 24, 24), outline=black, width=int(4 * s))
    d.ellipse([ox - 5 * s, oy + 96 * s, ox + 18 * s, oy + 118 * s], fill=(255, 92, 130))

    rotated = layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    img.alpha_composite(rotated, (cx - rotated.width // 2, cy - rotated.height // 2))


def draw_wobbling_kinnu(img: Image.Image, cx: int, floor_y: int, scale: float = 1.0):
    layer = Image.new("RGBA", (620, 780), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = scale
    ox, oy = 310, 230
    black = (18, 18, 18)
    yellow = (255, 215, 26)
    blue = (28, 128, 224)

    # Flailing arms and wobbly legs.
    d.line([(ox - 78 * s, oy + 205 * s), (ox - 210 * s, oy + 108 * s)], fill=black, width=int(12 * s))
    d.line([(ox + 78 * s, oy + 205 * s), (ox + 228 * s, oy + 82 * s)], fill=black, width=int(12 * s))
    d.ellipse([ox - 238 * s, oy + 76 * s, ox - 176 * s, oy + 138 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))
    d.ellipse([ox + 204 * s, oy + 50 * s, ox + 266 * s, oy + 112 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))
    d.line([(ox - 42 * s, oy + 360 * s), (ox - 115 * s, oy + 525 * s)], fill=black, width=int(13 * s))
    d.line([(ox + 42 * s, oy + 360 * s), (ox + 138 * s, oy + 510 * s)], fill=black, width=int(13 * s))
    d.ellipse([ox - 172 * s, oy + 508 * s, ox - 70 * s, oy + 562 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))
    d.ellipse([ox + 102 * s, oy + 490 * s, ox + 208 * s, oy + 548 * s], fill=(255, 255, 255), outline=black, width=int(6 * s))

    # Body.
    d.rounded_rectangle([ox - 92 * s, oy + 198 * s, ox + 92 * s, oy + 380 * s], radius=int(34 * s), fill=yellow, outline=black, width=int(8 * s))
    d.polygon([(ox - 106 * s, oy + 350 * s), (ox + 106 * s, oy + 350 * s), (ox + 138 * s, oy + 430 * s), (ox - 138 * s, oy + 430 * s)], fill=yellow, outline=black)
    d.rounded_rectangle([ox - 78 * s, oy + 402 * s, ox - 8 * s, oy + 530 * s], radius=int(24 * s), fill=blue, outline=black, width=int(6 * s))
    d.rounded_rectangle([ox + 8 * s, oy + 402 * s, ox + 82 * s, oy + 520 * s], radius=int(24 * s), fill=blue, outline=black, width=int(6 * s))

    # Head, hair, bow.
    d.ellipse([ox - 126 * s, oy - 28 * s, ox + 126 * s, oy + 224 * s], fill=(255, 255, 255), outline=black, width=int(8 * s))
    d.pieslice([ox - 136 * s, oy - 58 * s, ox + 136 * s, oy + 126 * s], 180, 360, fill=(22, 22, 26), outline=black, width=int(6 * s))
    for off in [-48, -18, 16, 50]:
        d.arc([ox - 34 * s + off * s, oy - 70 * s, ox + 68 * s + off * s, oy + 56 * s], 205, 305, fill=black, width=int(5 * s))
    d.polygon([(ox - 102 * s, oy - 26 * s), (ox - 166 * s, oy - 82 * s), (ox - 154 * s, oy + 6 * s)], fill=(255, 38, 145), outline=black)
    d.polygon([(ox - 100 * s, oy - 26 * s), (ox - 42 * s, oy - 86 * s), (ox - 48 * s, oy + 5 * s)], fill=(255, 38, 145), outline=black)
    d.ellipse([ox - 122 * s, oy - 58 * s, ox - 72 * s, oy - 10 * s], fill=(255, 38, 145), outline=black, width=int(5 * s))

    # Confused eyes and mouth.
    for ex in [ox - 47 * s, ox + 48 * s]:
        d.ellipse([ex - 28 * s, oy + 62 * s, ex + 28 * s, oy + 118 * s], fill=(255, 255, 255), outline=black, width=int(5 * s))
        d.ellipse([ex - 8 * s, oy + 84 * s, ex + 8 * s, oy + 102 * s], fill=black)
    d.arc([ox - 38 * s, oy + 142 * s, ox + 40 * s, oy + 188 * s], 190, 350, fill=black, width=int(6 * s))

    rotated = layer.rotate(-7, expand=True, resample=Image.Resampling.BICUBIC)
    img.alpha_composite(rotated, (cx - rotated.width // 2, floor_y - rotated.height + 95))


def draw_shiny_floor_thought(d: ImageDraw.ImageDraw, x: int, y: int):
    d.ellipse([x - 58, y + 235, x - 18, y + 275], fill=(255, 255, 255), outline=(45, 45, 45), width=4)
    d.ellipse([x - 20, y + 190, x + 34, y + 244], fill=(255, 255, 255), outline=(45, 45, 45), width=4)
    d.rounded_rectangle([x, y, x + 420, y + 210], radius=54, fill=(255, 255, 255), outline=(45, 45, 45), width=5)
    d.rounded_rectangle([x + 55, y + 52, x + 365, y + 158], radius=22, fill=(147, 220, 255), outline=(50, 130, 210), width=5)
    for tx in range(x + 80, x + 360, 70):
        d.line([(tx, y + 55), (tx - 45, y + 158)], fill=(255, 255, 255), width=4)
    for ty in [y + 88, y + 122]:
        d.line([(x + 60, ty), (x + 360, ty)], fill=(255, 255, 255), width=4)
    for sx, sy in [(x + 118, y + 72), (x + 252, y + 92), (x + 310, y + 132)]:
        starburst(d, sx, sy, 18, 8, 5, (255, 255, 255), (70, 150, 220))


def slide1():
    img = base_lab((220, 246, 255))
    d = ImageDraw.Draw(img)
    draw_title(d, "Kinnu phisal gayi! — Friction kya hai?", 70, 60)

    # Glossy wet classroom floor.
    d.rounded_rectangle([0, 610, W, H], radius=0, fill=(170, 222, 245, 180))
    for y in range(650, H, 92):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 100), width=3)
    for x in range(110, W, 210):
        d.line([(x, 610), (x - 120, H)], fill=(255, 255, 255, 80), width=3)
    for x, y, w in [(610, 750, 260), (1120, 690, 330), (420, 900, 190)]:
        d.ellipse([x, y, x + w, y + 28], fill=(255, 255, 255, 120))
        d.arc([x + 20, y + 4, x + w - 20, y + 36], 180, 350, fill=(90, 170, 215), width=4)

    wet_floor_sign(d, 1460, 560)
    draw_falling_kinnu(img, 850, 630, 1.0, -24)

    for off in [0, 38, 76]:
        d.arc([540 - off, 585 - off // 3, 820 - off, 740 - off // 3], 185, 335, fill=(255, 255, 255), width=7)

    starburst(d, 1180, 350, 145, 92, 11, (255, 224, 70), (45, 45, 45))
    d.text((1180, 350), "OOPS!", font=font(FONT_BLACK, 64), fill=(255, 82, 80), anchor="mm", stroke_width=6, stroke_fill=(255, 255, 255))
    d.text((1290, 535), "?", font=font(FONT_BLACK, 128), fill=(255, 190, 38), anchor="mm", stroke_width=8, stroke_fill=(255, 255, 255))
    save(img, 1)


def slide2():
    img = base_lab((227, 250, 255))
    d = ImageDraw.Draw(img)
    draw_title(d, "Gili-chikni floor = phisalna!", 70, 64)

    # Shiny wet tile surface.
    d.rounded_rectangle([0, 595, W, H], radius=0, fill=(160, 220, 246, 185))
    for y in range(630, H, 86):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 125), width=4)
    for x in range(110, W + 200, 205):
        d.line([(x, 595), (x - 125, H)], fill=(255, 255, 255, 100), width=4)
    for x, y, w in [(270, 820, 270), (850, 675, 360), (1215, 845, 250), (1480, 650, 210)]:
        d.ellipse([x, y, x + w, y + 34], fill=(255, 255, 255, 135))
        d.arc([x + 26, y + 5, x + w - 24, y + 42], 180, 350, fill=(80, 165, 220), width=5)

    # Sparkling droplets and wobble marks.
    for x, y in [(650, 720), (1010, 805), (1325, 715), (455, 690), (1510, 880), (760, 905)]:
        d.ellipse([x - 13, y - 19, x + 13, y + 19], fill=(255, 255, 255, 170), outline=(88, 170, 222), width=3)
        d.arc([x - 7, y - 14, x + 9, y + 8], 200, 330, fill=(255, 255, 255), width=3)
    for box in ([665, 560, 790, 640], [955, 530, 1115, 630], [585, 700, 740, 780]):
        d.arc(box, 190, 345, fill=(255, 255, 255), width=7)

    draw_shiny_floor_thought(d, 1265, 255)
    draw_wobbling_kinnu(img, 760, 910, 1.02)
    save(img, 2)


def slide3():
    img = base_lab((232, 250, 255))
    d = ImageDraw.Draw(img)
    draw_title(d, "Smooth = less friction", 70, 70)
    d.rounded_rectangle([610, 675, 1710, 820], radius=34, fill=(175, 230, 255), outline=(55, 125, 210), width=6)
    for x in range(650, 1680, 115):
        d.arc([x, 700, x + 82, 770], 0, 180, fill=(255, 255, 255), width=5)
    toy_car(d, 860, 560, 1.15, (73, 171, 255))
    draw_arrow(d, (835, 520), (1375, 520), (31, 176, 103), 18)
    d.text((1170, 470), "goes far!", font=font(FONT_BLACK, 50), fill=(31, 176, 103), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))
    place(img, 2, 380, 875, 520)
    save(img, 3)


def slide4():
    img = base_lab((255, 237, 221))
    d = ImageDraw.Draw(img)
    draw_title(d, "Rough = more friction", 70, 70)
    surface_card(d, [610, 655, 1710, 835], "rough surface", (212, 153, 88), pattern="rough")
    toy_car(d, 870, 548, 1.15, (255, 132, 65))
    draw_arrow(d, (1310, 520), (1010, 520), (238, 70, 70), 18)
    d.text((1165, 470), "slows fast", font=font(FONT_BLACK, 50), fill=(238, 70, 70), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))
    place(img, 1, 360, 875, 520)
    save(img, 4)


def slide5():
    img = base_lab((245, 255, 230))
    d = ImageDraw.Draw(img)
    draw_title(d, "Friction helps us grip", 70, 70)
    d.rounded_rectangle([730, 660, 1620, 810], radius=28, fill=(180, 225, 143), outline=(45, 115, 45), width=6)
    for x in range(760, 1585, 70):
        d.line([x, 680, x + 35, 790], fill=(87, 153, 74), width=4)
    d.ellipse([970, 500, 1190, 625], fill=(255, 255, 255), outline=(20, 20, 20), width=7)
    d.text((1080, 562), "shoe grip", font=font(FONT_BLACK, 40), fill=(47, 100, 38), anchor="mm")
    draw_arrow(d, (1080, 650), (1080, 790), (47, 100, 38), 16)
    place(img, 4, 405, 875, 560)
    save(img, 5)


def slide6():
    img = base_lab((255, 241, 219))
    d = ImageDraw.Draw(img)
    draw_title(d, "Friction can make heat", 70, 70)
    d.ellipse([740, 335, 1420, 845], fill=(255, 224, 118), outline=(255, 160, 65), width=8)
    d.text((1080, 475), "rub rub!", font=font(FONT_BLACK, 68), fill=(244, 110, 50), anchor="mm", stroke_width=6, stroke_fill=(255, 255, 255))
    d.rounded_rectangle([875, 565, 1045, 720], radius=50, fill=(255, 208, 150), outline=(20, 20, 20), width=6)
    d.rounded_rectangle([1115, 565, 1285, 720], radius=50, fill=(255, 208, 150), outline=(20, 20, 20), width=6)
    draw_arrow(d, (850, 760), (1010, 760), (244, 110, 50), 14)
    draw_arrow(d, (1310, 760), (1150, 760), (244, 110, 50), 14)
    place(img, 0, 360, 875, 540)
    save(img, 6)


def slide7():
    img = base_lab((238, 245, 255))
    d = ImageDraw.Draw(img)
    draw_title(d, "Ice or sandpaper?", 70, 70)
    surface_card(d, [520, 480, 920, 800], "LESS", (158, 226, 255), pattern="ice")
    surface_card(d, [1050, 480, 1450, 800], "MORE", (207, 151, 84), pattern="rough")
    d.text((720, 420), "ICE", font=font(FONT_BLACK, 58), fill=(55, 120, 210), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))
    d.text((1250, 420), "SANDPAPER", font=font(FONT_BLACK, 50), fill=(135, 78, 40), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))
    place(img, 3, 320, 875, 540)
    save(img, 7)


def slide8():
    img = base_lab((255, 249, 225))
    d = ImageDraw.Draw(img)
    draw_title(d, "Friction slows things down!", 70, 66)
    cards = [
        ([610, 365, 900, 645], "SLOW", (255, 205, 205)),
        ([965, 365, 1255, 645], "GRIP", (210, 245, 190)),
        ([1320, 365, 1610, 645], "HEAT", (255, 224, 150)),
    ]
    for box, label, fill in cards:
        d.rounded_rectangle(box, radius=34, fill=fill, outline=(40, 40, 40), width=5)
        d.text(((box[0] + box[2]) // 2, box[1] + 60), label, font=font(FONT_BLACK, 42), fill=(45, 75, 150), anchor="mm")
    toy_car(d, 650, 500, 0.62)
    d.ellipse([1055, 500, 1165, 585], fill=(255, 255, 255), outline=(20, 20, 20), width=5)
    d.rounded_rectangle([1420, 502, 1515, 585], radius=26, fill=(255, 204, 140), outline=(20, 20, 20), width=5)
    place(img, 5, 365, 875, 560)
    d.text((1095, 775), "See you next time!", font=font(FONT_BLACK, 54), fill=(255, 130, 50), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))
    save(img, 8)


def main():
    makers = [slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8]
    for maker in makers:
        maker()
    print(f"Wrote {len(makers)} slides to {OUT}")


if __name__ == "__main__":
    main()
