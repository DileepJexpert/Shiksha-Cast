"""Deterministic bright kids-math slides that DRAW exact objects + equations,
so the visuals always match the narration (AI image models can't count).

Each slide in script.yaml can carry a `visual:` spec. Supported scenes:
  title:    {scene: title, title: "...", subtitle: "..."}
  count:    {scene: count, n: 2, item: laddoo, caption: "..."}        # N objects + big number
  add:      {scene: add, n1: 2, n2: 3, item: laddoo, caption: "...",   # group + group
             result: 5 | question: true}                              # =5  or  =?
  countnum: {scene: countnum, n: 5, item: laddoo, caption: "..."}      # objects numbered 1..N
  mistake:  {scene: mistake, eq: "2 + 3 = 23", caption: "..."}         # wrong eq with X
  bigtext:  {scene: bigtext, big: "...", small: "..."}                 # teacher lines / recap
  cta:      {scene: cta, big: "...", small: "..."}                     # subscribe card

Output: build/<ep>/slides/slide_NNN.png (used by the normal `build` pipeline).
Usage: python scripts/make_kids_slides.py <episode-id>
"""
import glob
import os
import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FONTS = "C:/Windows/Fonts/"
BG_TOP, BG_BOT = (255, 248, 232), (255, 230, 200)   # warm cream
INK = (60, 42, 30)                                   # dark brown text
ACCENT = (240, 90, 110)                              # playful pink/red
GREEN = (40, 170, 90)
RED = (230, 70, 70)
BLUE = (70, 140, 230)


def font(size, bold=True):
    names = (["comicbd.ttf", "comic.ttf"] if bold else ["comic.ttf"]) + ["seguibl.ttf", "arialbd.ttf", "arial.ttf"]
    for n in names:
        p = FONTS + n
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def bg(d):
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3)))
    # confetti dots
    for i in range(36):
        x = (i * 137) % W
        yy = (i * 89) % H
        r = 6 + (i % 3) * 4
        col = [ACCENT, GREEN, BLUE, (250, 200, 60)][i % 4]
        d.ellipse([x, yy, x + r, yy + r], fill=col + (60,) if False else col)


def ctext(d, text, cx, y, f, fill=INK):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)
    return f.size


def draw_laddoo(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(232, 150, 46), outline=(150, 90, 20), width=max(3, r // 12))
    # speckles
    for dx, dy in [(-0.3, -0.2), (0.2, -0.3), (0.3, 0.25), (-0.25, 0.3), (0, 0.05)]:
        d.ellipse([cx + dx * r - 3, cy + dy * r - 3, cx + dx * r + 3, cy + dy * r + 3], fill=(150, 90, 20))
    d.ellipse([cx - r * 0.55, cy - r * 0.6, cx - r * 0.15, cy - r * 0.2], fill=(255, 210, 130))  # highlight


def draw_ball(d, cx, cy, r, color=(70, 140, 230)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=(30, 30, 40), width=max(3, r // 12))
    d.ellipse([cx - r * 0.5, cy - r * 0.6, cx - r * 0.1, cy - r * 0.2], fill=(255, 255, 255))  # shine
    d.arc([cx - r * 0.7, cy - r * 0.3, cx + r * 0.7, cy + r], start=200, end=340, fill=(255, 255, 255), width=max(3, r // 12))


def draw_obj(d, item, cx, cy, r, idx=0):
    if item == "ball":
        draw_ball(d, cx, cy, r, color=[(70, 140, 230), (230, 70, 70), (40, 170, 90)][idx % 3])
    else:
        draw_laddoo(d, cx, cy, r)


def draw_row(d, n, item, cx, cy, r, gap=None):
    if n <= 0:
        return
    gap = gap if gap is not None else r * 0.7
    total = n * (2 * r) + (n - 1) * gap
    x = cx - total / 2 + r
    for i in range(n):
        draw_obj(d, item, x, cy, r, i)
        x += 2 * r + gap


def render(ep, slide, n, total, out, brand="KINNU"):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    bg(d)
    v = slide.get("visual") or {"scene": "bigtext", "big": (slide.get("narration", "")[:60])}
    scene = v.get("scene", "bigtext")

    # header
    d.text((60, 48), brand, font=font(40), fill=ACCENT)
    badge = f"{n:02d}/{total:02d}"
    d.text((W - 60 - d.textlength(badge, font=font(36)), 52), badge, font=font(36), fill=(170, 140, 110))

    if scene == "title":
        ctext(d, "( ^_^ )", W / 2, 250, font(150), fill=ACCENT)   # simple smiley character
        for ln_i, ln in enumerate(_wrap(d, v.get("title", ""), font(110), W - 300)):
            ctext(d, ln, W / 2, 470 + ln_i * 130, font(110))
        if v.get("subtitle"):
            ctext(d, v["subtitle"], W / 2, 760, font(54), fill=ACCENT)

    elif scene in ("count", "countnum"):
        cap = v.get("caption", "")
        ctext(d, cap, W / 2, 130, font(64))
        nobj = int(v.get("n", 1))
        r = min(110, int((W - 300) / (nobj * 2.4)))
        draw_row(d, nobj, v.get("item", "laddoo"), W / 2, 560, r)
        if scene == "countnum":
            gap = r * 0.7
            totalw = nobj * (2 * r) + (nobj - 1) * gap
            x = W / 2 - totalw / 2 + r
            for i in range(nobj):
                ctext(d, str(i + 1), x, 560 + r + 30, font(56), fill=ACCENT)
                x += 2 * r + gap
        ctext(d, f"= {nobj}", W / 2, 800, font(96), fill=GREEN)

    elif scene == "add":
        cap = v.get("caption", "")
        ctext(d, cap, W / 2, 120, font(60))
        n1, n2 = int(v["n1"]), int(v["n2"])
        item = v.get("item", "laddoo")
        r = 70
        # left group, plus, right group on one band
        gy = 470
        d.text((W / 2 - 40, gy - 60), "+", font=font(120), fill=INK)
        draw_row(d, n1, item, W / 2 - 430, gy, r)
        draw_row(d, n2, item, W / 2 + 430, gy, r)
        if "result" in v and v["result"] is not None:
            ctext(d, f"{n1} + {n2} = {v['result']}", W / 2, 720, font(110), fill=GREEN)
        elif v.get("question"):
            ctext(d, f"{n1} + {n2} = ?", W / 2, 720, font(120), fill=ACCENT)
        else:
            ctext(d, f"{n1} + {n2}", W / 2, 720, font(110), fill=INK)

    elif scene == "mistake":
        ctext(d, v.get("eq", ""), W / 2, 380, font(150), fill=RED)
        d.line([(W / 2 - 320, 470), (W / 2 + 320, 540)], fill=RED, width=14)  # cross-out
        ctext(d, "X  GALAT!", W / 2, 640, font(90), fill=RED)
        if v.get("caption"):
            ctext(d, v["caption"], W / 2, 800, font(54))

    elif scene == "cta":
        ctext(d, "( ^_^ )/", W / 2, 250, font(140), fill=ACCENT)
        for ln_i, ln in enumerate(_wrap(d, v.get("big", "Subscribe!"), font(96), W - 300)):
            ctext(d, ln, W / 2, 480 + ln_i * 120, font(96), fill=ACCENT)
        if v.get("small"):
            ctext(d, v["small"], W / 2, 760, font(48), fill=INK)

    else:  # bigtext
        big = v.get("big", "")
        lines = _wrap(d, big, font(96), W - 300)
        y = (H - len(lines) * 120) / 2 - 40
        for ln in lines:
            ctext(d, ln, W / 2, y, font(96)); y += 120
        if v.get("small"):
            ctext(d, v["small"], W / 2, y + 20, font(54), fill=ACCENT)

    img.save(out)


def _wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    ep_id = sys.argv[1]
    matches = glob.glob(f"content/**/{ep_id}/script.yaml", recursive=True) + glob.glob(f"content/{ep_id}/script.yaml")
    if not matches:
        print("episode not found:", ep_id); return
    scr = yaml.safe_load(open(matches[0], encoding="utf-8"))
    slides = scr.get("slides", [])
    brand = scr.get("brand", "KINNU")
    outdir = os.path.join("build", ep_id, "slides")
    os.makedirs(outdir, exist_ok=True)
    for i, s in enumerate(slides, 1):
        render(ep_id, s, i, len(slides), os.path.join(outdir, f"slide_{i:03d}.png"), brand=brand)
    print(f"{ep_id}: {len(slides)} kids slides -> {outdir}")


if __name__ == "__main__":
    main()
