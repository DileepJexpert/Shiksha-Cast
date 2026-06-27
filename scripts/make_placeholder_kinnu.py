"""Draw a PLACEHOLDER girl-Kinnu rig (character + 3 mouth shapes) so the lip-sync
engine can be tested end-to-end before the real ChatGPT character assets exist.

Outputs to assets/kinnu_rig_placeholder/:
  character_base.png  (transparent, no mouth)
  mouth_closed.png / mouth_half.png / mouth_open.png  (transparent)
  rig.json            (mouth anchor + filenames)

Replace these with real transparent ChatGPT PNGs later; keep rig.json's anchor.
"""
import json
import os

from PIL import Image, ImageDraw

OUT = "assets/kinnu_rig_placeholder"
os.makedirs(OUT, exist_ok=True)
W, H = 700, 920
INK = (30, 30, 30, 255)

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
cx = W // 2

# shirt (yellow)
d.rounded_rectangle([cx - 150, 560, cx + 150, 905], radius=70, fill=(247, 200, 50, 255), outline=INK, width=9)
# neck
d.rectangle([cx - 30, 470, cx + 30, 575], fill=(255, 255, 255, 255), outline=INK, width=6)
# head
d.ellipse([cx - 185, 120, cx + 185, 490], fill=(255, 255, 255, 255), outline=INK, width=11)
# hair strands
for dx in (-45, -18, 12, 40):
    d.line([(cx + dx, 130), (cx + dx - 9, 66)], fill=INK, width=9)
# hair bow (girl marker)
bx, by = cx + 95, 158
d.polygon([(bx, by), (bx - 48, by - 32), (bx - 48, by + 32)], fill=(240, 90, 110, 255), outline=(120, 30, 50, 255))
d.polygon([(bx, by), (bx + 48, by - 32), (bx + 48, by + 32)], fill=(240, 90, 110, 255), outline=(120, 30, 50, 255))
d.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=(220, 60, 90, 255))
# eyes
ey = 305
for ex in (cx - 72, cx + 72):
    d.ellipse([ex - 34, ey - 40, ex + 34, ey + 40], fill=(255, 255, 255, 255), outline=INK, width=6)
    d.ellipse([ex - 15, ey - 6, ex + 19, ey + 32], fill=INK)
    d.ellipse([ex - 2, ey + 2, ex + 11, ey + 15], fill=(255, 255, 255, 255))
# cheeks
for ex in (cx - 115, cx + 115):
    d.ellipse([ex - 24, ey + 52, ex + 24, ey + 90], fill=(255, 170, 170, 130))
img.save(f"{OUT}/character_base.png")

MOUTH_ANCHOR = [cx, 432]  # where the mouth's CENTER sits within the character image


def make_mouth(name, fn, size=(180, 160)):
    m = Image.new("RGBA", size, (0, 0, 0, 0))
    make_mouth_draw = ImageDraw.Draw(m)
    fn(make_mouth_draw, size)
    m.save(f"{OUT}/{name}.png")


def closed(dd, s):
    w, h = s
    dd.line([(w * 0.3, h * 0.5), (w * 0.7, h * 0.5)], fill=(120, 40, 40, 255), width=11)


def half(dd, s):
    w, h = s
    dd.ellipse([w * 0.33, h * 0.38, w * 0.67, h * 0.62], fill=(120, 40, 40, 255))


def open_m(dd, s):
    w, h = s
    dd.ellipse([w * 0.27, h * 0.24, w * 0.73, h * 0.82], fill=(120, 40, 40, 255))
    dd.ellipse([w * 0.4, h * 0.6, w * 0.6, h * 0.8], fill=(230, 120, 130, 255))  # tongue


make_mouth("mouth_closed", closed)
make_mouth("mouth_half", half)
make_mouth("mouth_open", open_m)

rig = {
    "character": "character_base.png",
    "mouths": {"closed": "mouth_closed.png", "half": "mouth_half.png", "open": "mouth_open.png"},
    "mouth_anchor": MOUTH_ANCHOR,
    "size": [W, H],
}
json.dump(rig, open(f"{OUT}/rig.json", "w"), indent=2)
print("placeholder Kinnu rig ->", OUT)
