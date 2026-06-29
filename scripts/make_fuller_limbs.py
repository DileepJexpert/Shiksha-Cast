"""Make a 2D cutout character's limbs fuller/chunkier (less 'stick figure') by widening
the limb part PNGs horizontally about their center. Joint pivots are fractional (fx=0.5),
so center-widening keeps the rig aligned.

Upper arm / thigh are plain bars -> widen more. Forearm / shin contain hand/foot -> widen
less so hands don't look bloated.

Usage:
  python scripts/make_fuller_limbs.py <src_char> <out_char> [bar_factor] [hand_factor]
  e.g. python scripts/make_fuller_limbs.py kinnu_hd kinnu_fuller 1.32 1.14
"""
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CHARS = ROOT / "assets" / "cartoon" / "characters"

BAR = {"upper_arm_left", "upper_arm_right", "thigh_left", "thigh_right"}
HAND = {"forearm_left", "forearm_right", "shin_left", "shin_right"}


def widen(im, fx):
    w, h = im.size
    nw = max(1, int(round(w * fx)))
    big = im.resize((nw, h), Image.LANCZOS)
    # keep canvas centered so the part's center x (pivot fx=0.5) is preserved
    out = Image.new("RGBA", (max(w, nw), h), (0, 0, 0, 0))
    out.alpha_composite(big, ((out.width - nw) // 2, 0))
    return out


def main():
    if len(sys.argv) < 3:
        print("usage: make_fuller_limbs.py <src_char> <out_char> [bar_factor] [hand_factor]")
        return
    src = CHARS / sys.argv[1]
    out = CHARS / sys.argv[2]
    bar_f = float(sys.argv[3]) if len(sys.argv) > 3 else 1.32
    hand_f = float(sys.argv[4]) if len(sys.argv) > 4 else 1.14
    out.mkdir(parents=True, exist_ok=True)
    for p in src.glob("*.png"):
        im = Image.open(p).convert("RGBA")
        if p.stem in BAR:
            im = widen(im, bar_f)
        elif p.stem in HAND:
            im = widen(im, hand_f)
        im.save(out / p.name)
    meta = src / "rig2.json"
    if meta.exists():
        shutil.copy(meta, out / "rig2.json")
    print(f"{sys.argv[2]}: limbs widened (bar x{bar_f}, hand x{hand_f}) -> {out}")


if __name__ == "__main__":
    main()
