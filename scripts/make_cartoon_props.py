"""Generate simple transparent cartoon PROP PNGs for the cutout engine.
Output: assets/cartoon/props/  (star, heart, book, apple, soap, circle, square, triangle)
Usage: python scripts/make_cartoon_props.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "assets" / "cartoon" / "props"
OUT.mkdir(parents=True, exist_ok=True)
INK = (35, 32, 40, 255)
SZ = 300


def cv():
    return Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0))


def star(fill=(255, 205, 60, 255)):
    img = cv(); d = ImageDraw.Draw(img)
    cx = cy = SZ / 2; R, r = 130, 56
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill, outline=INK)
    img.save(OUT / "star.png")


def heart():
    img = cv(); d = ImageDraw.Draw(img)
    d.pieslice([60, 70, 160, 170], 130, 380, fill=(235, 70, 100, 255), outline=INK)
    d.pieslice([140, 70, 240, 170], 160, 410, fill=(235, 70, 100, 255), outline=INK)
    d.polygon([(70, 140), (230, 140), (150, 245)], fill=(235, 70, 100, 255), outline=INK)
    img.save(OUT / "heart.png")


def book():
    img = cv(); d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 80, 240, 220], 12, fill=(70, 140, 230, 255), outline=INK, width=6)
    d.line([(150, 84), (150, 216)], fill=INK, width=6)
    for y in (120, 150, 180):
        d.line([(80, y), (140, y)], fill=(255, 255, 255, 200), width=5)
        d.line([(160, y), (220, y)], fill=(255, 255, 255, 200), width=5)
    img.save(OUT / "book.png")


def apple():
    img = cv(); d = ImageDraw.Draw(img)
    d.ellipse([80, 90, 220, 240], fill=(225, 60, 70, 255), outline=INK, width=6)
    d.line([(150, 95), (150, 60)], fill=(90, 60, 30, 255), width=8)
    d.ellipse([150, 60, 185, 90], fill=(70, 170, 90, 255), outline=INK, width=4)
    img.save(OUT / "apple.png")


def soap():
    img = cv(); d = ImageDraw.Draw(img)
    d.rounded_rectangle([85, 150, 215, 230], 24, fill=(120, 200, 245, 255), outline=INK, width=6)
    for x, y, r in [(120, 120, 26), (160, 95, 32), (200, 125, 24), (140, 150, 18)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 250, 255, 235), outline=INK, width=3)
    img.save(OUT / "soap.png")


def shape(name, fill):
    img = cv(); d = ImageDraw.Draw(img)
    if name == "circle":
        d.ellipse([60, 60, 240, 240], fill=fill, outline=INK, width=7)
    elif name == "square":
        d.rounded_rectangle([66, 66, 234, 234], 14, fill=fill, outline=INK, width=7)
    else:  # triangle
        d.polygon([(150, 56), (244, 240), (56, 240)], fill=fill, outline=INK)
    img.save(OUT / f"{name}.png")


star(); heart(); book(); apple(); soap()
shape("circle", (235, 90, 110, 255))
shape("square", (70, 150, 235, 255))
shape("triangle", (90, 195, 120, 255))
print("props ->", OUT, sorted(p.name for p in OUT.glob("*.png")))
