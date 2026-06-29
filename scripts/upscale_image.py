"""Upscale image(s) on the GPU with Real-ESRGAN (cartoon model).

Usage:
  python scripts/upscale_image.py in.png                  # -> in.up.png (4x)
  python scripts/upscale_image.py in.png out.png          # 4x to out.png
  python scripts/upscale_image.py in.png out.png --1080   # 4x then fit to 1920x1080
  python scripts/upscale_image.py assets/cartoon/backgrounds  # whole folder -> *.up.png
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiksha_cast.imagegen.upscale import Upscaler  # noqa: E402

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def main():
    args = [a for a in sys.argv[1:]]
    to_1080 = "--1080" in args
    args = [a for a in args if a != "--1080"]
    if not args:
        print(__doc__)
        return
    src = Path(args[0])
    to_size = (1920, 1080) if to_1080 else None
    up = Upscaler()
    if src.is_dir():
        files = [p for p in sorted(src.iterdir()) if p.suffix.lower() in EXTS and ".up" not in p.suffixes]
        for p in files:
            up.upscale_file(p, p.with_suffix(".up.png"), to_size=to_size)
            print("upscaled", p.name)
    else:
        out = Path(args[1]) if len(args) > 1 else src.with_suffix(".up.png")
        up.upscale_file(src, out, to_size=to_size)
        print("saved", out)
    up.unload()


if __name__ == "__main__":
    main()
