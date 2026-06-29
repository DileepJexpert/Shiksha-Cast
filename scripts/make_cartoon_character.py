"""Generate ORIGINAL cutout cartoon characters as separated transparent part-PNGs
(drawn procedurally with Pillow — no external art needed). Distinct styles (girl /
boy / teacher) with their own hair, face, outfit, so the cast looks like different
characters. Same joint pivots as the rig so the animation engine works unchanged.

Output: assets/cartoon/characters/<name>/{parts + eye/mouth states + rig.json}

Usage (presets): python scripts/make_cartoon_character.py            # builds kinnu/minku/tara
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SP = (600, 900)
INK = (35, 32, 40, 255)
J = {"neck": (300, 470), "shoulder_left": (238, 520), "shoulder_right": (362, 520),
     "hip_left": (272, 618), "hip_right": (328, 618)}


def cv():
    return Image.new("RGBA", SP, (0, 0, 0, 0))


def rr(d, box, r, fill, outline=INK, w=8):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def make(name, skin, hair, top, bottom, shoe, *, style="girl", bow=None,
         bindi=False, glasses=False, scale=1.0):
    out = ROOT / "assets" / "cartoon" / "characters" / name
    out.mkdir(parents=True, exist_ok=True)
    def S(img, fn): img.save(out / fn)

    HX, HY, RX, RY = 300, 362, 122, 130     # head center + radii

    # ---------- BODY ----------
    img = cv(); d = ImageDraw.Draw(img)
    d.rectangle([286, 452, 314, 522], fill=skin, outline=INK, width=6)        # neck
    if style in ("girl", "teacher"):                                          # dress / kurti
        torso_bottom = 700 if style == "teacher" else 640
        rr(d, [214, 505, 386, torso_bottom], 54, top)
        flare = 250 if style == "teacher" else 210                            # skirt
        d.polygon([(238, torso_bottom - 30), (362, torso_bottom - 30),
                   (300 + flare // 2, 752), (300 - flare // 2, 752)], fill=top, outline=INK)
    else:                                                                     # t-shirt (boy)
        rr(d, [212, 505, 388, 690], 56, top)
    d.ellipse([272, 520, 328, 552], fill=(255, 255, 255, 70))                 # collar sheen
    S(img, "body.png")

    # ---------- HEAD (hair + face, no eyes/mouth) ----------
    img = cv(); d = ImageDraw.Draw(img)
    for s in (-1, 1):
        d.ellipse([HX + s * 116 - 22, HY - 6, HX + s * 116 + 22, HY + 40], fill=skin, outline=INK, width=6)
    d.ellipse([HX - RX, HY - RY, HX + RX, HY + RY], fill=skin, outline=INK, width=9)   # face
    # hair
    if style == "boy":
        d.pieslice([HX - RX - 4, HY - RY - 8, HX + RX + 4, HY + 40], 180, 360, fill=hair)
        for i in range(-3, 4):                                                # spikes
            x = HX + i * 30
            d.polygon([(x - 16, HY - RY + 18), (x, HY - RY - 34), (x + 16, HY - RY + 18)], fill=hair)
    else:
        d.pieslice([HX - RX - 4, HY - RY - 10, HX + RX + 4, HY + 70], 178, 362, fill=hair)
        d.polygon([(HX - RX, HY - 6), (HX - RX - 6, HY + 70), (HX - 60, HY + 30)], fill=hair)  # side bangs
        d.polygon([(HX + RX, HY - 6), (HX + RX + 6, HY + 70), (HX + 60, HY + 30)], fill=hair)
    if style == "girl":                                                       # ponytail + bow
        d.ellipse([HX + RX - 6, HY - 40, HX + RX + 66, HY + 70], fill=hair, outline=INK, width=5)
        bx, by = HX + RX + 16, HY - 36
        bc = bow or (240, 90, 120)
        d.polygon([(bx, by), (bx - 36, by - 24), (bx - 36, by + 24)], fill=bc, outline=INK)
        d.polygon([(bx, by), (bx + 36, by - 24), (bx + 36, by + 24)], fill=bc, outline=INK)
        d.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=(220, 60, 95, 255))
    if style == "teacher":                                                    # bun
        d.ellipse([HX - 34, HY - RY - 46, HX + 34, HY - RY + 22], fill=hair, outline=INK, width=6)
    if bindi:
        d.ellipse([HX - 8, HY - 64, HX + 8, HY - 48], fill=(210, 40, 70, 255))
    for s in (-1, 1):                                                         # eyebrows
        d.line([(HX + s * 54 - 18, HY - 30), (HX + s * 54 + 18, HY - 38)], fill=hair, width=7)
    for s in (-1, 1):                                                         # cheeks
        d.ellipse([HX + s * 70 - 22, HY + 36, HX + s * 70 + 22, HY + 66], fill=(255, 150, 155, 120))
    S(img, "head.png")

    # ---------- EYES ----------
    lashes = style in ("girl", "teacher")
    for state in ("open", "closed"):
        img = cv(); d = ImageDraw.Draw(img)
        for s in (-1, 1):
            ex, ey = HX + s * 54, HY + 2
            if state == "open":
                d.ellipse([ex - 28, ey - 32, ex + 28, ey + 32], fill=(255, 255, 255, 255), outline=INK, width=5)
                d.ellipse([ex - 12, ey - 6, ex + 18, ey + 28], fill=(45, 35, 40, 255))
                d.ellipse([ex - 4, ey, ex + 8, ey + 12], fill=(255, 255, 255, 255))
                if lashes:
                    d.line([(ex + s * 26, ey - 26), (ex + s * 36, ey - 34)], fill=INK, width=5)
            else:
                d.arc([ex - 26, ey - 16, ex + 26, ey + 16], 0, 180, fill=INK, width=6)
        if glasses:
            for s in (-1, 1):
                ex, ey = HX + s * 54, HY + 2
                d.ellipse([ex - 36, ey - 34, ex + 36, ey + 36], outline=(45, 42, 55, 255), width=8)
            d.line([(HX - 18, HY - 4), (HX + 18, HY - 4)], fill=(45, 42, 55, 255), width=7)
        S(img, f"eye_{state}.png")

    # ---------- MOUTHS ----------
    for st in ("closed", "half", "open"):
        img = cv(); d = ImageDraw.Draw(img)
        mx, my = HX, HY + 78
        if st == "closed":
            d.arc([mx - 30, my - 20, mx + 30, my + 16], 18, 162, fill=(150, 60, 70, 255), width=8)
        else:
            o = 0.5 if st == "half" else 1.0
            w, h = 36, 14 + 24 * o
            d.ellipse([mx - w, my - h, mx + w, my + h], fill=(120, 40, 50, 255), outline=INK, width=4)
            d.rectangle([mx - w + 4, my - h + 4, mx + w - 4, my - h * 0.2], fill=(255, 255, 255, 255))
            d.ellipse([mx - w * 0.55, my + h * 0.15, mx + w * 0.55, my + h - 3], fill=(235, 120, 130, 255))
        S(img, f"mouth_{st}.png")

    # ---------- ARMS ----------
    for side, sx, hx in (("left", J["shoulder_left"][0], -14), ("right", J["shoulder_right"][0], 14)):
        img = cv(); d = ImageDraw.Draw(img)
        sy = 520
        rr(d, [sx - 19, sy, sx + 19, sy + 120], 19, top)                      # sleeve+arm
        rr(d, [sx - 17, sy + 110, sx + 17, sy + 150], 17, skin)              # forearm skin
        d.ellipse([sx + hx - 24, sy + 146, sx + hx + 24, sy + 196], fill=skin, outline=INK, width=6)  # hand
        S(img, f"arm_{side}.png")

    # ---------- LEGS ----------
    leg_skin = style == "girl"   # bare legs under dress
    for side, hx in (("left", J["hip_left"][0]), ("right", J["hip_right"][0])):
        img = cv(); d = ImageDraw.Draw(img)
        hy = 618
        if leg_skin:
            rr(d, [hx - 20, hy, hx + 20, hy + 208], 18, skin)
        else:
            rr(d, [hx - 22, hy, hx + 22, hy + 140], 18, bottom)              # shorts/pants
            rr(d, [hx - 19, hy + 130, hx + 19, hy + 210], 16, skin)          # shin
        rr(d, [hx - 30, hy + 196, hx + 40, hy + 250], 22, shoe)             # shoe
        S(img, f"leg_{side}.png")

    rig = {
        "name": name, "space": list(SP), "feet": [300, 880], "scale": scale,
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
    print(f"{name} ({style}) -> {out}")


# Canonical cast: Kinnu, Gappu, Vibhu (toddler), Anshu, Prinshu (glasses).
PRESETS = {
    "kinnu": dict(skin=(255, 214, 176), hair=(45, 35, 42), top=(247, 195, 50),
                  bottom=(60, 120, 230), shoe=(50, 90, 200), style="girl", bow=(240, 90, 120)),
    "gappu": dict(skin=(235, 185, 140), hair=(30, 26, 32), top=(40, 175, 95),
                  bottom=(55, 60, 80), shoe=(40, 90, 200), style="boy"),
    "vibhu": dict(skin=(255, 205, 165), hair=(40, 32, 38), top=(245, 120, 70),
                  bottom=(120, 90, 200), shoe=(230, 90, 90), style="boy", scale=0.72),
    "anshu": dict(skin=(248, 200, 158), hair=(38, 30, 40), top=(170, 90, 205),
                  bottom=(60, 55, 90), shoe=(230, 120, 150), style="girl", bow=(110, 200, 240)),
    "prinshu": dict(skin=(238, 190, 150), hair=(28, 24, 30), top=(70, 130, 230),
                    bottom=(60, 55, 75), shoe=(200, 120, 60), style="boy", glasses=True),
}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in PRESETS:
        make(sys.argv[1], **PRESETS[sys.argv[1]])
    else:
        for n, kw in PRESETS.items():
            make(n, **kw)
