"""Export a presenter kit per episode so you can record yourself explaining slides.

For every episode it creates decks/<ep>/:
  <ep>.pdf        - all slides as a PDF deck (open & present/record over it)
  <ep>.html       - scrollable deck: each slide image + its narration as notes
  slides/         - the slide PNGs
  narration.md    - the full narration script, per slide (what to say)

Run after make_slides.py.  Usage: python scripts/export_decks.py [episode-id]
"""
import glob
import html as _html
import os
import shutil
import sys

import yaml

OUT = "decks"


def episodes():
    eps = [os.path.dirname(p) for p in glob.glob("content/**/script.yaml", recursive=True)]
    return sorted(
        e for e in eps
        if not any(part.startswith((".", "_")) for part in os.path.relpath(e, "content").split(os.sep))
    )


def export(ep_dir):
    ep = os.path.basename(ep_dir)
    pngs = sorted(glob.glob(os.path.join("build", ep, "slides", "slide_*.png")))
    if not pngs:
        return False
    dst = os.path.join(OUT, ep)
    os.makedirs(os.path.join(dst, "slides"), exist_ok=True)

    scr = yaml.safe_load(open(os.path.join(ep_dir, "script.yaml"), encoding="utf-8")) or {}
    title = scr.get("chapter", ep)
    narr = {s["n"]: s.get("narration", "") for s in scr.get("slides", [])}

    # copy PNGs
    copied = []
    for p in pngs:
        d = os.path.join(dst, "slides", os.path.basename(p))
        shutil.copy2(p, d)
        copied.append(d)

    # PDF deck — lossless via img2pdf (no Pillow JPEG dependency)
    import img2pdf

    with open(os.path.join(dst, f"{ep}.pdf"), "wb") as f:
        f.write(img2pdf.convert(copied))

    # narration.md (presenter script)
    with open(os.path.join(dst, "narration.md"), "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n_Read / explain each slide using these notes._\n\n")
        for i in range(1, len(pngs) + 1):
            f.write(f"## Slide {i}\n\n{narr.get(i, '')}\n\n")

    # HTML deck: slide image + narration note under each
    rows = []
    for i, p in enumerate(pngs, 1):
        note = _html.escape(narr.get(i, ""))
        rows.append(
            f'<section><img src="slides/{os.path.basename(p)}" alt="slide {i}">'
            f'<div class="note"><span class="n">Slide {i}</span>{note}</div></section>'
        )
    page = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<title>{_html.escape(title)}</title><style>"
        "body{background:#0a0e1a;color:#e8ecf5;font-family:'Segoe UI',Arial,sans-serif;margin:0}"
        "h1{padding:24px 28px;font-size:26px}"
        "section{max-width:1280px;margin:0 auto 44px;padding:0 16px}"
        "img{width:100%;border-radius:10px;display:block;box-shadow:0 6px 24px rgba(0,0,0,.4)}"
        ".note{background:#161c2e;padding:16px 20px;border-radius:0 0 10px 10px;line-height:1.65;font-size:18px}"
        ".n{display:block;color:#39e0ff;font-weight:700;margin-bottom:6px}"
        "</style></head><body>"
        f"<h1>{_html.escape(title)}</h1>{''.join(rows)}</body></html>"
    )
    open(os.path.join(dst, f"{ep}.html"), "w", encoding="utf-8").write(page)
    return True


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    done = skipped = 0
    for ed in episodes():
        if only and os.path.basename(ed) != only:
            continue
        if export(ed):
            done += 1
            print(f"  {os.path.basename(ed)}")
        else:
            skipped += 1
            print(f"  [no slides] {os.path.basename(ed)}")
    print(f"DONE: {done} decks exported to {OUT}/ ({skipped} skipped - no slides)")


if __name__ == "__main__":
    main()
