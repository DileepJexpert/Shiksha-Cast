"""Generate CHARACTER-FREE, no-label, English backgrounds for the k03 talking video,
by reusing Codex's friction art (make_k03_friction_slides) with the in-scene Kinnu,
the "Slide N of 8" badge and the corner logo disabled, and the two Hinglish titles
translated to English (the talking Kinnu is overlaid by build_talking_episode.py).

Output: build/k03-friction/backgrounds/bg_001..008.png
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import make_k03_friction_slides as m  # noqa: E402

BG = ROOT / "build" / "k03-friction" / "backgrounds"


def _save(img, n):
    BG.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(BG / f"bg_{n:03d}.png", quality=95)


# Strip everything that belongs on a full slide but not on a clean background.
m.save = _save
m.draw_badge = lambda *a, **k: None          # remove "Slide N of 8" label
m.draw_logo = lambda *a, **k: None           # remove corner logo (host carries the brand)
m.draw_falling_kinnu = lambda *a, **k: None  # remove in-scene character
m.draw_wobbling_kinnu = lambda *a, **k: None
m.place = lambda *a, **k: None               # remove pose placements

_orig_title = m.draw_title
TITLE_MAP = {
    "Kinnu phisal gayi! — Friction kya hai?": "Why did Kinnu slip? What is friction?",
    "Gili-chikni floor = phisalna!": "Smooth wet floor means slipping!",
}


def _english_title(d, text, *a, **k):
    return _orig_title(d, TITLE_MAP.get(text, text), *a, **k)


m.draw_title = _english_title

m.main()
print("k03 backgrounds ->", BG)
