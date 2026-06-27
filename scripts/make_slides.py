"""Auto-generate 1920x1080 PNG slides for episodes (no Canva needed).

Reads each episode's script.yaml (slide count + title) and SLIDES.md (per-slide
"Text overlay" text) and renders dark-neon themed slides into build/<ep>/slides/.

Usage:
  python scripts/make_slides.py              # all content/s* episodes
  python scripts/make_slides.py s06-yawning  # one episode
"""
import glob
import os
import re
import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FONTS = "C:/Windows/Fonts/"
ACCENTS = [(0, 229, 255), (124, 108, 255), (0, 230, 150), (255, 92, 122), (255, 193, 7)]


def font(name, size):
    for n in (name, "seguibl.ttf", "segoeuib.ttf", "arialbd.ttf", "arial.ttf"):
        p = FONTS + n
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def gradient(draw):
    top, bot = (10, 14, 30), (22, 30, 58)
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))


def wrap(draw, text, fnt, maxw):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=fnt) <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def parse_overlays(path):
    """Return list of slide text-overlays in order (one per '## Slide N' section)."""
    txt = open(path, encoding="utf-8").read()
    secs = re.split(r"\n##\s+Slide\s+\d+", txt)[1:]
    out = []
    for sec in secs:
        m = re.search(r"Text overlay:\*\*\s*[\"“]([^\"”]+)[\"”]", sec)
        if m:
            out.append(m.group(1).strip())
        else:
            head = sec.split("\n", 1)[0].lstrip(" —-").strip()
            out.append(head)
    return out


def render(ep_id, text, n, total, accent, out, is_title=False, brand="KATIXO SHIKSHA"):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    gradient(d)
    d.rectangle([0, 0, 18, H], fill=accent)  # left accent bar

    badge = ep_id.split("-")[0].upper()
    d.text((70, 58), brand, font=font("segoeuib.ttf", 34), fill=accent)
    bf = font("segoeuib.ttf", 34)
    d.text((W - 70 - d.textlength(badge, font=bf), 58), badge, font=bf, fill=(180, 190, 210))

    parts = [p.strip() for p in text.split("|")]
    main = parts[0] if parts else text
    sub = parts[1] if len(parts) > 1 else ""

    fsize = 104 if is_title else 80
    tf = font("seguibl.ttf", fsize)
    lines = wrap(d, main, tf, W - 320)
    line_h = fsize * 1.18
    block_h = len(lines) * line_h + (90 if sub else 0)
    y = (H - block_h) / 2
    for ln in lines:
        d.text(((W - d.textlength(ln, font=tf)) / 2, y), ln, font=tf, fill=(242, 246, 255))
        y += line_h

    uw = 420
    d.rectangle([(W - uw) / 2, y + 12, (W + uw) / 2, y + 20], fill=accent)
    y += 46
    if sub:
        sf = font("segoeui.ttf", 46)
        for ln in wrap(d, sub, sf, W - 380):
            d.text(((W - d.textlength(ln, font=sf)) / 2, y), ln, font=sf, fill=(255, 214, 110))
            y += sf.size * 1.3

    foot = f"{n:02d} / {total:02d}"
    d.text((W - 70 - d.textlength(foot, font=bf), H - 84), foot, font=bf, fill=(150, 160, 185))
    if is_title:
        d.text((70, H - 84), "EP " + badge, font=bf, fill=accent)

    img.save(out)


def build(ep_dir):
    ep = os.path.basename(ep_dir)
    scr = yaml.safe_load(open(os.path.join(ep_dir, "script.yaml"), encoding="utf-8"))
    slides = scr.get("slides", [])
    total = len(slides)
    ep_title = scr.get("chapter", ep)
    brand = scr.get("brand", "KATIXO SHIKSHA")
    smd = os.path.join(ep_dir, "SLIDES.md")
    overlays = parse_overlays(smd) if os.path.exists(smd) else []
    outdir = os.path.join("build", ep, "slides")
    os.makedirs(outdir, exist_ok=True)
    for i in range(total):
        n = i + 1
        accent = ACCENTS[i % len(ACCENTS)]
        if i == 0:
            text = overlays[0] if overlays else (ep_title.split("—", 1)[-1].strip())
            render(ep, text, n, total, accent, os.path.join(outdir, f"slide_{n:03d}.png"), is_title=True, brand=brand)
        else:
            text = overlays[i] if i < len(overlays) and overlays[i] else f"Slide {n}"
            render(ep, text, n, total, accent, os.path.join(outdir, f"slide_{n:03d}.png"), brand=brand)
    # remove the placeholder note if present
    note = os.path.join(outdir, "_PUT_SLIDES_HERE.txt")
    if os.path.exists(note):
        os.remove(note)
    return total


def discover_episodes():
    """All episode dirs (containing script.yaml) anywhere under content/,
    skipping archive/hidden folders. Handles the category subfolders."""
    eps = []
    for path in glob.glob("content/**/script.yaml", recursive=True):
        rel = os.path.relpath(path, "content")
        if any(part.startswith((".", "_")) for part in rel.split(os.sep)):
            continue
        eps.append(os.path.dirname(path))
    return sorted(eps)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    eps = discover_episodes()
    done = 0
    for d in eps:
        if only and os.path.basename(d) != only:
            continue
        n = build(d)
        done += 1
        print(f"{os.path.basename(d)}: {n} slides")
    print(f"DONE: {done} episode(s)")


if __name__ == "__main__":
    main()
