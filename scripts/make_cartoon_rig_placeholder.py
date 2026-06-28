"""Generate a PLACEHOLDER separated-part cartoon rig so the cutout animation engine
can be built & tested before real ChatGPT character art exists.

Each body part is drawn on its own full 600x900 transparent canvas at its true
location, so rotating a part about its joint pivot (shoulder/hip/neck) is exact.
Replace these PNGs with real transparent art later; keep rig.json's pivots.

Output: assets/cartoon/characters/<name>/  (parts + eye/mouth states + rig.json)
Usage:  python scripts/make_cartoon_rig_placeholder.py <name> [R,G,B shirt] [R,G,B pants]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SP = (600, 900)                      # rig coordinate space
INK = (30, 30, 36, 255)

# joints (pivots) in rig space
J = {
    "neck": (300, 470), "shoulder_left": (238, 520), "shoulder_right": (362, 520),
    "hip_left": (272, 618), "hip_right": (328, 618),
}


def canvas():
    return Image.new("RGBA", SP, (0, 0, 0, 0))


def rrect(d, box, r, fill, outline=INK, w=8):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def make(name, shirt=(247, 200, 50), pants=(60, 120, 230), skin=(255, 222, 188),
         hair=(40, 35, 45), shoe=(50, 90, 200), bow=(240, 90, 120)):
    out = ROOT / "assets" / "cartoon" / "characters" / name
    out.mkdir(parents=True, exist_ok=True)

    def save(img, fn):
        img.save(out / fn)

    # --- BODY (torso) ---
    img = canvas(); d = ImageDraw.Draw(img)
    d.rectangle([285, 455, 315, 520], fill=skin, outline=INK, width=6)        # neck
    rrect(d, [212, 505, 388, 735], 60, shirt)                                  # torso
    d.ellipse([268, 520, 332, 556], fill=(255, 255, 255, 120))                # collar hint
    save(img, "body.png")

    # --- HEAD (no eyes/mouth; those are layers) ---
    img = canvas(); d = ImageDraw.Draw(img)
    for s in (-1, 1):                                                          # ears
        d.ellipse([300 + s * 118 - 22, 360, 300 + s * 118 + 22, 404], fill=skin, outline=INK, width=6)
    d.ellipse([185, 250, 415, 500], fill=skin, outline=INK, width=9)          # face
    d.pieslice([183, 232, 417, 470], 180, 360, fill=hair)                      # hair cap
    for dx in (-60, -28, 6, 40):                                               # fringe strands
        d.line([(300 + dx, 250), (300 + dx - 10, 198)], fill=hair, width=10)
    bx, by = 372, 268                                                          # bow
    d.polygon([(bx, by), (bx - 40, by - 26), (bx - 40, by + 26)], fill=bow, outline=INK)
    d.polygon([(bx, by), (bx + 40, by - 26), (bx + 40, by + 26)], fill=bow, outline=INK)
    d.ellipse([bx - 13, by - 13, bx + 13, by + 13], fill=(220, 60, 95, 255))
    for s in (-1, 1):                                                          # eyebrows
        d.line([(300 + s * 56 - 18, 330), (300 + s * 56 + 18, 322)], fill=hair, width=7)
    for s in (-1, 1):                                                          # cheeks
        d.ellipse([300 + s * 66 - 22, 408, 300 + s * 66 + 22, 440], fill=(255, 160, 165, 130))
    save(img, "head.png")

    # --- EYES (open / closed) ---
    for state in ("open", "closed"):
        img = canvas(); d = ImageDraw.Draw(img)
        for s in (-1, 1):
            ex, ey = 300 + s * 56, 372
            if state == "open":
                d.ellipse([ex - 26, ey - 30, ex + 26, ey + 30], fill=(255, 255, 255, 255), outline=INK, width=5)
                d.ellipse([ex - 11, ey - 4, ex + 17, ey + 26], fill=INK)
                d.ellipse([ex - 4, ey + 2, ex + 6, ey + 12], fill=(255, 255, 255, 255))
            else:
                d.line([(ex - 24, ey), (ex + 24, ey)], fill=INK, width=7)
        save(img, f"eye_{state}.png")

    # --- MOUTHS (closed / half / open) ---
    specs = {"closed": ("smile",), "half": ("oval", 0.5), "open": ("oval", 1.0)}
    for st, spec in specs.items():
        img = canvas(); d = ImageDraw.Draw(img)
        mx, my = 300, 442
        if spec[0] == "smile":
            d.arc([mx - 30, my - 18, mx + 30, my + 18], 20, 160, fill=(150, 60, 70, 255), width=8)
        else:
            o = spec[1]
            w, h = 36, 14 + 26 * o
            d.ellipse([mx - w, my - h, mx + w, my + h], fill=(120, 40, 50, 255))
            d.rectangle([mx - w, my - h, mx + w, my - h + h * 0.5], fill=(255, 255, 255, 255))
            d.ellipse([mx - w * 0.6, my + h * 0.1, mx + w * 0.6, my + h], fill=(235, 120, 130, 255))
        save(img, f"mouth_{st}.png")

    # --- ARMS (hang straight down from shoulders) ---
    for side, sx, fxoff in (("left", J["shoulder_left"][0], -16), ("right", J["shoulder_right"][0], 16)):
        img = canvas(); d = ImageDraw.Draw(img)
        sy = 520
        rrect(d, [sx - 18, sy, sx + 18, sy + 150], 18, shirt)                  # upper sleeve+arm
        d.ellipse([sx + fxoff - 24, sy + 150, sx + fxoff + 24, sy + 198], fill=skin, outline=INK, width=6)  # hand
        save(img, f"arm_{side}.png")

    # --- LEGS (hang straight down from hips) ---
    for side, hx in (("left", J["hip_left"][0]), ("right", J["hip_right"][0])):
        img = canvas(); d = ImageDraw.Draw(img)
        hy = 618
        rrect(d, [hx - 22, hy, hx + 22, hy + 210], 20, pants)                  # leg
        rrect(d, [hx - 30, hy + 196, hx + 40, hy + 250], 22, shoe)            # shoe
        save(img, f"leg_{side}.png")

    rig = {
        "name": name, "space": list(SP), "feet": [300, 880], "scale": 1.0,
        "parts": [
            {"name": "arm_left", "img": "arm_left.png", "pivot": list(J["shoulder_left"]), "z": 0},
            {"name": "leg_left", "img": "leg_left.png", "pivot": list(J["hip_left"]), "z": 0},
            {"name": "leg_right", "img": "leg_right.png", "pivot": list(J["hip_right"]), "z": 1},
            {"name": "body", "img": "body.png", "pivot": [300, 600], "z": 2},
            {"name": "arm_right", "img": "arm_right.png", "pivot": list(J["shoulder_right"]), "z": 3},
            {"name": "head", "img": "head.png", "pivot": list(J["neck"]), "z": 4},
        ],
        "eyes": {"open": "eye_open.png", "closed": "eye_closed.png", "z": 5},
        "mouths": {"closed": "mouth_closed.png", "half": "mouth_half.png", "open": "mouth_open.png", "z": 6},
        "head_part": "head",
    }
    json.dump(rig, open(out / "rig.json", "w"), indent=2)
    print(f"{name} part-rig -> {out}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "kinnu2d"
    shirt = tuple(int(x) for x in sys.argv[2].split(",")) if len(sys.argv) > 2 else (247, 200, 50)
    pants = tuple(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else (60, 120, 230)
    make(name, shirt=shirt, pants=pants)
