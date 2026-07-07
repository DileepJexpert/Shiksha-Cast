"""Generate the reusable Moti puppy cutout rig.

The files are intentionally built from simple local vector drawing primitives so
the dog is reproducible offline and can be improved without depending on an
online image generator.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "cartoon" / "characters" / "moti_hd"

INK = (34, 29, 25, 255)
FUR = (211, 122, 44, 255)
FUR_DARK = (126, 75, 39, 255)
FUR_LIGHT = (244, 203, 136, 255)
CREAM = (255, 226, 174, 255)
NOSE = (28, 26, 24, 255)
COLLAR = (229, 57, 53, 255)
GOLD = (238, 173, 55, 255)
WHITE = (255, 255, 255, 255)
BROWN = (92, 50, 25, 255)


def canvas(size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f"{name}.png")


def ellipse(d, box, fill, outline=INK, width=6) -> None:
    d.ellipse(box, fill=outline)
    inset = width
    d.ellipse(
        [box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset],
        fill=fill,
    )


def rounded(d, box, radius, fill, outline=INK, width=6) -> None:
    d.rounded_rectangle(box, radius=radius, fill=outline)
    inset = width
    d.rounded_rectangle(
        [box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset],
        radius=max(1, radius - inset),
        fill=fill,
    )


def head(back: bool = False) -> Image.Image:
    im, d = canvas((360, 320))
    # ears behind the head
    ellipse(d, [18, 74, 112, 246], FUR_DARK, width=7)
    ellipse(d, [248, 74, 342, 246], FUR_DARK, width=7)
    ellipse(d, [55, 38, 305, 262], FUR, width=8)
    # soft face patch and top tuft
    if not back:
        ellipse(d, [82, 132, 278, 276], CREAM, width=5)
        d.polygon([(156, 42), (174, 2), (186, 42)], fill=INK)
        d.polygon([(160, 42), (174, 12), (184, 42)], fill=FUR)
        d.polygon([(188, 43), (222, 11), (214, 54)], fill=INK)
        d.polygon([(192, 42), (214, 22), (208, 50)], fill=FUR)
        ellipse(d, [145, 174, 215, 222], NOSE, width=5)
        d.line([180, 214, 180, 238], fill=INK, width=5)
    else:
        d.arc([98, 80, 262, 230], 205, 335, fill=FUR_DARK, width=9)
    return im


def torso() -> Image.Image:
    im, d = canvas((300, 390))
    rounded(d, [45, 35, 255, 356], 82, FUR, width=8)
    ellipse(d, [86, 98, 214, 332], CREAM, width=4)
    rounded(d, [50, 28, 250, 74], 22, COLLAR, width=7)
    ellipse(d, [132, 52, 168, 90], GOLD, width=5)
    d.ellipse([142, 64, 158, 80], fill=(154, 100, 28, 255))
    return im


def limb(kind: str, side: str) -> Image.Image:
    if kind in {"upper_arm", "forearm"}:
        im, d = canvas((88, 235 if kind == "upper_arm" else 225))
        rounded(d, [19, 12, 69, im.height - 38], 26, FUR, width=6)
        ellipse(d, [12, im.height - 74, 76, im.height - 10], FUR_LIGHT, width=5)
        for x in (32, 44, 56):
            d.arc([x - 8, im.height - 48, x + 8, im.height - 20], 185, 345, fill=FUR_DARK, width=2)
        return im
    im, d = canvas((100, 235 if kind == "thigh" else 245))
    rounded(d, [20, 10, 80, im.height - 34], 30, FUR, width=6)
    ellipse(d, [10, im.height - 78, 90, im.height - 8], FUR_LIGHT, width=5)
    for x in (32, 50, 68):
        d.arc([x - 9, im.height - 50, x + 9, im.height - 18], 185, 345, fill=FUR_DARK, width=2)
    return im


def knee(side: str) -> Image.Image:
    im, d = canvas((58, 46))
    ellipse(d, [4, 6, 54, 42], FUR, width=4)
    return im


def tail() -> Image.Image:
    im, d = canvas((210, 260))
    # Base is near the upper-left. The tail hangs behind the body and curves down,
    # so even with wagging it reads as a puppy tail, not a front limb.
    pts = [(28, 66), (78, 96), (110, 150), (130, 220)]
    d.line(pts, fill=INK, width=45, joint="curve")
    d.line(pts, fill=FUR, width=34, joint="curve")
    d.ellipse([108, 202, 154, 248], fill=INK)
    d.ellipse([114, 208, 148, 242], fill=CREAM)
    return im


def eyes(kind: str) -> Image.Image:
    im, d = canvas((190, 78))
    if kind == "open":
        for x in (52, 138):
            ellipse(d, [x - 34, 8, x + 34, 74], WHITE, width=4)
            d.ellipse([x - 19, 24, x + 19, 62], fill=BROWN)
            d.ellipse([x - 10, 34, x + 10, 54], fill=NOSE)
            d.ellipse([x - 17, 24, x - 6, 35], fill=WHITE)
    elif kind == "happy":
        for x in (52, 138):
            d.arc([x - 32, 22, x + 32, 70], 200, 340, fill=INK, width=7)
    else:
        for x in (52, 138):
            d.arc([x - 32, 22, x + 32, 70], 20, 160, fill=INK, width=7)
    return im


def brows(kind: str) -> Image.Image:
    im, d = canvas((190, 54))
    if kind == "sad":
        d.line([34, 36, 76, 18], fill=INK, width=8)
        d.line([114, 18, 156, 36], fill=INK, width=8)
    elif kind == "surprised":
        d.arc([28, 12, 82, 46], 190, 350, fill=INK, width=7)
        d.arc([108, 12, 162, 46], 190, 350, fill=INK, width=7)
    elif kind == "happy":
        d.arc([28, 18, 82, 52], 190, 350, fill=INK, width=7)
        d.arc([108, 18, 162, 52], 190, 350, fill=INK, width=7)
    else:
        d.line([30, 28, 78, 22], fill=INK, width=7)
        d.line([112, 22, 160, 28], fill=INK, width=7)
    return im


def mouth(kind: str) -> Image.Image:
    im, d = canvas((170, 96))
    if kind == "X":
        d.arc([46, 18, 86, 60], 20, 160, fill=INK, width=5)
        d.arc([84, 18, 124, 60], 20, 160, fill=INK, width=5)
    elif kind in {"A", "B", "C", "E", "F", "H"}:
        h = {"B": 20, "F": 22, "H": 26, "A": 34, "E": 42, "C": 50}[kind]
        ellipse(d, [66, 34, 104, 34 + h], (92, 34, 28, 255), width=4)
        if h > 34:
            d.ellipse([73, 56, 97, 78], fill=(242, 99, 105, 255))
    elif kind == "D":
        ellipse(d, [54, 22, 116, 88], (82, 25, 22, 255), width=5)
        d.ellipse([66, 58, 104, 88], fill=(244, 104, 108, 255))
    elif kind == "G":
        rounded(d, [50, 35, 120, 68], 12, WHITE, width=4)
        for x in (68, 86, 104):
            d.line([x, 38, x, 66], fill=INK, width=2)
    elif kind == "sad":
        d.arc([48, 40, 122, 92], 200, 340, fill=INK, width=6)
    return im


def write_rig() -> None:
    rig = {
        "type": "skeletal",
        "scale": 0.9,
        "space": [760, 1060],
        "feet_y": 1015,
        "cx": 380,
        "joints": {
            "neck": [380, 450],
            "shoulder_left": [315, 535],
            "shoulder_right": [445, 535],
            "hip_left": [342, 690],
            "hip_right": [418, 690],
            "tail": [535, 655],
        },
        "face": {"brows": [380, 256], "eyes": [380, 300], "mouth": [380, 366]},
        "pivot": {
            "head": [0.5, 0.90],
            "torso": [0.5, 0.47],
            "upper_arm": [0.5, 0.08],
            "forearm": [0.5, 0.14],
            "thigh": [0.5, 0.08],
            "shin": [0.5, 0.14],
            "tail": [0.13, 0.25],
        },
        "bone": {"upper_arm": 0.82, "forearm": 0.0, "thigh": 0.82, "shin": 0.0},
        "neck_raise": 30,
        "torso_dy": -8,
        "render_padding": 240,
        "neck_stub": True,
    }
    (OUT / "rig2.json").write_text(json.dumps(rig, indent=2), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    save(head(False), "head")
    save(head(True), "head_back")
    save(torso(), "torso")
    save(tail(), "tail")
    for side in ("left", "right"):
        save(limb("upper_arm", side), f"upper_arm_{side}")
        save(limb("forearm", side), f"forearm_{side}")
        save(limb("thigh", side), f"thigh_{side}")
        save(limb("shin", side), f"shin_{side}")
        save(knee(side), f"knee_{side}")
    for kind in ("open", "closed", "happy"):
        save(eyes(kind), f"eyes_{kind}")
    for kind in ("neutral", "happy", "sad", "surprised"):
        save(brows(kind), f"brows_{kind}")
    for kind in ("X", "A", "B", "C", "D", "E", "F", "G", "H", "sad"):
        save(mouth(kind), f"mouth_{kind}")
    write_rig()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
