from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
HOST_OUT = ROOT / "assets" / "kinnu" / "host"
BG_OUT = ROOT / "build" / "k02-star-bridge-counting" / "backgrounds"
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


def text_with_outline(
    d: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: tuple[int, int, int],
    anchor: str = "mm",
    stroke: int = 8,
):
    d.text(
        xy,
        text,
        font=font(FONT_BLACK, size),
        fill=fill,
        anchor=anchor,
        stroke_width=stroke,
        stroke_fill=(255, 255, 255),
    )


def star_points(cx: float, cy: float, r1: float, r2: float, points: int = 5, rot: float = -math.pi / 2):
    pts = []
    for i in range(points * 2):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * math.pi / points
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_star(
    d: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    fill=(255, 218, 55),
    outline=(255, 255, 255),
    width: int = 5,
):
    d.polygon(star_points(cx, cy, r, r * 0.45), fill=fill, outline=outline)
    if width > 1:
        d.line(star_points(cx, cy, r, r * 0.45) + [star_points(cx, cy, r, r * 0.45)[0]], fill=outline, width=width, joint="curve")


def draw_glow_star(img: Image.Image, cx: float, cy: float, r: float, fill, glow, number: str | None = None, bright: bool = True):
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    for mul, alpha in [(3.2, 38), (2.3, 54), (1.55, 80)]:
        gd.polygon(star_points(cx, cy, r * mul, r * mul * 0.45), fill=(*glow, alpha))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(8 if bright else 5))
    img.alpha_composite(glow_layer)

    d = ImageDraw.Draw(img)
    draw_star(d, cx, cy, r, fill=fill, outline=(255, 255, 255), width=6 if bright else 3)
    if number:
        d.text(
            (cx, cy + 3),
            number,
            font=font(FONT_BLACK, max(24, int(r * 0.82))),
            fill=(63, 76, 170),
            anchor="mm",
            stroke_width=max(2, int(r * 0.07)),
            stroke_fill=(255, 255, 255),
        )


def night_background() -> Image.Image:
    img = Image.new("RGBA", (W, H), (17, 28, 88, 255))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(18 + 35 * t)
        g = int(27 + 12 * t)
        b = int(86 + 70 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b, 255))

    rng = random.Random(1202)
    for _ in range(170):
        x = rng.randint(0, W - 1)
        y = rng.randint(35, H - 150)
        r = rng.choice([2, 2, 3, 4])
        color = rng.choice([(255, 255, 255, 230), (255, 242, 165, 220), (170, 222, 255, 210)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)
        if r >= 3:
            d.line([x - 9, y, x + 9, y], fill=color, width=2)
            d.line([x, y - 9, x, y + 9], fill=color, width=2)

    # Soft cloud shapes near horizon, away from the host area.
    for box in [(1040, 815, 1530, 990), (1370, 760, 1950, 960), (620, 870, 1040, 1030)]:
        d.ellipse(box, fill=(104, 82, 160, 86))
    return img


def bridge_positions() -> list[tuple[int, int]]:
    pts = []
    for i in range(10):
        t = i / 9
        x = int(355 + 1270 * t)
        y = int(815 - 430 * math.sin(t * math.pi))
        pts.append((x, y))
    return pts


def draw_bridge(img: Image.Image, bright_upto: int = 0, lit: set[int] | None = None, all_faint: bool = True):
    lit = set() if lit is None else lit
    d = ImageDraw.Draw(img)
    pts = bridge_positions()
    d.line(pts, fill=(255, 199, 45, 120), width=22, joint="curve")
    d.line(pts, fill=(255, 245, 145, 160), width=8, joint="curve")
    for idx, (x, y) in enumerate(pts, start=1):
        active = idx <= bright_upto or idx in lit
        if all_faint or active:
            r = 56 if active else 39
            fill = (255, 217, 47) if active else (126, 109, 160)
            glow = (255, 219, 67) if active else (120, 135, 205)
            draw_glow_star(img, x, y, r, fill=fill, glow=glow, number=str(idx), bright=active)


def draw_banner(d: ImageDraw.ImageDraw, x: int, y: int, text: str):
    d.rounded_rectangle([x, y, x + 250, y + 74], radius=24, fill=(255, 255, 255), outline=(67, 78, 172), width=5)
    d.polygon([(x, y + 42), (x - 45, y + 68), (x, y + 74)], fill=(255, 214, 68), outline=(67, 78, 172))
    d.polygon([(x + 250, y + 42), (x + 295, y + 68), (x + 250, y + 74)], fill=(255, 214, 68), outline=(67, 78, 172))
    d.text((x + 125, y + 37), text, font=font(FONT_BLACK, 38), fill=(67, 78, 172), anchor="mm")


def title_bg(img: Image.Image, text: str, size: int = 66):
    d = ImageDraw.Draw(img)
    text_with_outline(d, (W // 2, 78), text, size, (55, 102, 224), stroke=8)


def draw_wrong_numbers(img: Image.Image):
    d = ImageDraw.Draw(img)
    for text, x, y, ang, color in [
        ("1", 1045, 255, -16, (255, 233, 72)),
        ("2", 1440, 345, 19, (89, 210, 255)),
        ("4", 1240, 645, -23, (255, 119, 143)),
        ("7", 1655, 525, 14, (182, 255, 91)),
    ]:
        layer = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.text((90, 90), text, font=font(FONT_BLACK, 86), fill=color, anchor="mm", stroke_width=6, stroke_fill=(255, 255, 255))
        layer = layer.rotate(ang, expand=True, resample=Image.Resampling.BICUBIC)
        img.alpha_composite(layer, (x - layer.width // 2, y - layer.height // 2))


def draw_confetti(img: Image.Image):
    d = ImageDraw.Draw(img)
    rng = random.Random(606)
    colors = [(255, 76, 112), (255, 214, 57), (75, 204, 255), (128, 232, 108), (210, 132, 255)]
    for _ in range(80):
        x = rng.randint(560, 1780)
        y = rng.randint(150, 780)
        c = rng.choice(colors)
        d.rounded_rectangle([x, y, x + 16, y + 8], radius=3, fill=c)


def draw_buttons(d: ImageDraw.ImageDraw):
    d.rounded_rectangle([1230, 585, 1510, 695], radius=35, fill=(255, 255, 255), outline=(40, 80, 190), width=6)
    d.text((1370, 640), "Like", font=font(FONT_BLACK, 48), fill=(40, 91, 215), anchor="mm")
    d.rounded_rectangle([1210, 725, 1585, 845], radius=38, fill=(255, 65, 84), outline=(255, 255, 255), width=7)
    d.text((1398, 785), "Subscribe", font=font(FONT_BLACK, 46), fill=(255, 255, 255), anchor="mm")


def make_backgrounds():
    BG_OUT.mkdir(parents=True, exist_ok=True)

    scenes: list[Image.Image] = []

    img = night_background()
    title_bg(img, "Kinnu & the Star Bridge — Count 1 to 10!", 56)
    draw_bridge(img, all_faint=True)
    draw_wrong_numbers(img)
    scenes.append(img)

    img = night_background()
    title_bg(img, "1 — One!", 80)
    pts = bridge_positions()
    d = ImageDraw.Draw(img)
    d.line(pts, fill=(255, 199, 45, 110), width=18, joint="curve")
    for idx, (x, y) in enumerate(pts, start=1):
        if idx == 1:
            draw_glow_star(img, x, y, 94, fill=(255, 222, 42), glow=(255, 225, 64), number="1", bright=True)
        else:
            draw_glow_star(img, x, y, 38, fill=(122, 111, 158), glow=(120, 135, 205), number=str(idx), bright=False)
    scenes.append(img)

    img = night_background()
    title_bg(img, "1, 2, 3", 80)
    draw_bridge(img, bright_upto=3, all_faint=True)
    scenes.append(img)

    img = night_background()
    title_bg(img, "4, 5 — Halfway!", 74)
    draw_bridge(img, bright_upto=5, all_faint=True)
    draw_banner(ImageDraw.Draw(img), 1080, 510, "Halfway!")
    scenes.append(img)

    img = night_background()
    title_bg(img, "6, 7, 8", 80)
    draw_bridge(img, lit={6, 7, 8}, all_faint=True)
    for x, y in bridge_positions()[5:8]:
        ImageDraw.Draw(img).arc([x - 118, y - 92, x + 118, y + 112], 205, 335, fill=(255, 255, 255, 170), width=6)
    scenes.append(img)

    img = night_background()
    title_bg(img, "9, 10 — You did it!", 72)
    draw_bridge(img, bright_upto=10, all_faint=True)
    draw_confetti(img)
    scenes.append(img)

    img = night_background()
    title_bg(img, "Your turn! Count 1 to 10", 68)
    d = ImageDraw.Draw(img)
    pts = bridge_positions()
    for idx, (x, y) in enumerate(pts, start=1):
        # Exactly ten separated stars, no duplicate star shapes nearby.
        draw_glow_star(img, x, y, 58, fill=(255, 218, 53), glow=(255, 221, 78), number=str(idx), bright=True)
    scenes.append(img)

    img = night_background()
    title_bg(img, "1 to 10 done! Like & Subscribe — A Katixo channel", 55)
    draw_bridge(img, bright_upto=10, all_faint=True)
    d = ImageDraw.Draw(img)
    for idx, (x, y) in enumerate(bridge_positions(), start=1):
        d.text((x, y + 110), str(idx), font=font(FONT_BLACK, 54), fill=(255, 241, 82), anchor="mm", stroke_width=6, stroke_fill=(70, 70, 145))
    draw_buttons(d)
    scenes.append(img)

    for i, img in enumerate(scenes, start=1):
        img.convert("RGB").save(BG_OUT / f"bg_{i:03d}.png", quality=95)


def draw_kinnu_host(mouth: str) -> Image.Image:
    img = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    black = (18, 18, 18)
    yellow = (255, 215, 26)
    blue = (43, 110, 220)
    pink = (255, 38, 145)

    # Torso and arms are identical across all mouth states.
    d.line([(300, 528), (158, 668)], fill=black, width=18)
    d.line([(600, 528), (742, 668)], fill=black, width=18)
    d.ellipse([120, 635, 196, 711], fill=(255, 255, 255), outline=black, width=8)
    d.ellipse([704, 635, 780, 711], fill=(255, 255, 255), outline=black, width=8)
    d.rounded_rectangle([288, 482, 612, 760], radius=54, fill=yellow, outline=black, width=12)
    d.polygon([(278, 690), (622, 690), (680, 812), (220, 812)], fill=yellow, outline=black)
    d.rounded_rectangle([320, 750, 420, 885], radius=32, fill=blue, outline=black, width=10)
    d.rounded_rectangle([480, 750, 580, 885], radius=32, fill=blue, outline=black, width=10)

    # Head, hair, bow.
    d.ellipse([242, 120, 658, 536], fill=(255, 255, 255), outline=black, width=13)
    d.pieslice([226, 74, 674, 384], 180, 360, fill=(22, 22, 26), outline=black, width=9)
    for off in [-92, -42, 15, 72]:
        d.arc([350 + off, 58, 510 + off, 270], 205, 305, fill=black, width=7)
    d.polygon([(285, 122), (178, 32), (196, 178)], fill=pink, outline=black)
    d.polygon([(292, 122), (398, 28), (384, 178)], fill=pink, outline=black)
    d.ellipse([238, 72, 328, 162], fill=pink, outline=black, width=8)

    # Friendly eyes.
    for ex in [370, 530]:
        d.ellipse([ex - 49, 270, ex + 49, 370], fill=(255, 255, 255), outline=black, width=8)
        d.ellipse([ex - 16, 305, ex + 16, 340], fill=black)
        d.ellipse([ex - 6, 300, ex + 5, 312], fill=(255, 255, 255))

    if mouth == "closed":
        d.arc([395, 398, 505, 470], 15, 165, fill=black, width=9)
    elif mouth == "half":
        d.ellipse([418, 402, 482, 472], fill=(28, 28, 28), outline=black, width=7)
        d.ellipse([438, 444, 470, 466], fill=(255, 96, 130))
    elif mouth == "open":
        d.ellipse([390, 388, 510, 500], fill=(28, 28, 28), outline=black, width=8)
        d.ellipse([420, 456, 490, 494], fill=(255, 96, 130))
    else:
        raise ValueError(mouth)

    return img


def make_host():
    HOST_OUT.mkdir(parents=True, exist_ok=True)
    for name in ["closed", "half", "open"]:
        draw_kinnu_host(name).save(HOST_OUT / f"{name}.png")


def main():
    make_host()
    make_backgrounds()
    print(f"Wrote host PNGs to {HOST_OUT}")
    print(f"Wrote backgrounds to {BG_OUT}")


if __name__ == "__main__":
    main()
