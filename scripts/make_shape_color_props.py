"""Generate bright, kid-friendly prop PNGs for the English shape + color episodes:
  shapes:  circle, square, triangle, rectangle (k03)
  balloons: red, yellow, blue, green, orange, purple (k04)
All transparent PNGs with a soft outline + highlight, saved to assets/cartoon/props/.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "cartoon" / "props"
OUT.mkdir(parents=True, exist_ok=True)

INK = (40, 36, 46, 255)
S = 460  # canvas

SHAPE_COLORS = {
    "shape_circle": (235, 70, 80),       # red
    "shape_square": (70, 130, 235),      # blue
    "shape_triangle": (70, 190, 110),    # green
    "shape_rectangle": (245, 160, 55),   # orange
}
BALLOON_COLORS = {
    "balloon_red": (230, 65, 70),
    "balloon_yellow": (250, 205, 60),
    "balloon_blue": (70, 140, 235),
    "balloon_green": (75, 190, 110),
    "balloon_orange": (245, 150, 50),
    "balloon_purple": (160, 95, 200),
}


def _highlight(d, box, col):
    """soft white glossy highlight in the upper-left of a bbox."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    hx0 = x0 + w * 0.18; hy0 = y0 + h * 0.12
    d.ellipse([hx0, hy0, hx0 + w * 0.28, hy0 + h * 0.22], fill=(255, 255, 255, 130))


def make_shape(name, col):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = col + (255,)
    m = 60
    if name == "shape_circle":
        box = [m, m, S - m, S - m]
        d.ellipse(box, fill=c, outline=INK, width=10)
        _highlight(d, box, col)
    elif name == "shape_square":
        box = [m, m, S - m, S - m]
        d.rounded_rectangle(box, radius=28, fill=c, outline=INK, width=10)
        _highlight(d, box, col)
    elif name == "shape_triangle":
        pts = [(S / 2, m), (S - m, S - m), (m, S - m)]
        d.polygon(pts, fill=c, outline=INK)
        # thicker outline (polygon width is unreliable across PIL versions)
        d.line(pts + [pts[0]], fill=INK, width=10, joint="curve")
        _highlight(d, [m + 60, m + 70, S - m - 60, S - m], col)
    elif name == "shape_rectangle":
        box = [40, 140, S - 40, S - 140]
        d.rounded_rectangle(box, radius=22, fill=c, outline=INK, width=10)
        _highlight(d, box, col)
    im.save(OUT / f"{name}.png")
    return name


def make_balloon(name, col):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = col + (255,)
    # balloon body (egg-ish ellipse)
    bx0, by0, bx1, by1 = 90, 40, S - 90, 360
    d.ellipse([bx0, by0, bx1, by1], fill=c, outline=INK, width=8)
    _highlight(d, [bx0, by0, bx1, by1], col)
    # knot
    cx = S / 2
    d.polygon([(cx - 20, by1 - 18), (cx + 20, by1 - 18), (cx, by1 + 18)], fill=c, outline=INK)
    # string (gentle S-curve)
    pts = []
    for i in range(0, 101, 5):
        f = i / 100.0
        y = by1 + 18 + f * 80
        x = cx + 18 * __import__("math").sin(f * 6.2)
        pts.append((x, y))
    d.line(pts, fill=INK, width=5, joint="curve")
    im.save(OUT / f"{name}.png")
    return name


def main():
    made = []
    for n, c in SHAPE_COLORS.items():
        made.append(make_shape(n, c))
    for n, c in BALLOON_COLORS.items():
        made.append(make_balloon(n, c))
    print(f"made {len(made)} props -> {OUT}")
    for n in made:
        print("  ", n)


if __name__ == "__main__":
    main()
