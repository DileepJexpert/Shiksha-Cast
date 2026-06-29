"""Generate consistent Kinnu STILLS in new poses/scenes from one reference image, using
the local IP-Adapter remixer (no training, 8 GB-safe). Asset/stills factory: thumbnails,
posters, "Kinnu in a scene", nicer cutout source art.

Usage:
  python scripts/make_kinnu_stills.py                      # all presets
  python scripts/make_kinnu_stills.py wave point cheer     # selected presets
  python scripts/make_kinnu_stills.py "Kinnu riding a bicycle in the park"   # custom prompt
  python scripts/make_kinnu_stills.py --ref path/to/ref.png --scale 0.85

Output: assets/cartoon/kinnu_stills/<name>.png  (+ a montage in dist/_kinnu_stills.png)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402
from shiksha_cast.imagegen.ipadapter import KinnuRemixer  # noqa: E402

OUT = ROOT / "assets" / "cartoon" / "kinnu_stills"
DEFAULT_REF = ROOT / "assets" / "cartoon" / "source" / "kinnu_3d_ref.png"

# name -> (prompt, width, height). Square for poses; wide for thumbnails.
PRESETS = {
    "wave":        ("Kinnu the toddler girl waving hello and smiling, standing", 832, 1216),
    "point":       ("Kinnu the toddler girl pointing to the side with one hand, happy", 832, 1216),
    "cheer":       ("Kinnu the toddler girl cheering with both arms raised up, excited and happy", 832, 1216),
    "read":        ("Kinnu the toddler girl holding and reading a colorful picture book", 832, 1216),
    "think":       ("Kinnu the toddler girl with a thoughtful curious expression, finger on chin", 832, 1216),
    "count":       ("Kinnu the toddler girl counting on her fingers, looking at her hand", 832, 1216),
    "sit":         ("Kinnu the toddler girl sitting cross-legged on the floor, smiling", 832, 1216),
    "clap":        ("Kinnu the toddler girl clapping her hands, joyful", 832, 1216),
    "garden":      ("Kinnu the toddler girl standing in a sunny flower garden with butterflies", 832, 1216),
    "classroom":   ("Kinnu the toddler girl in a bright preschool classroom by a chalkboard", 832, 1216),
    "thumb_hero":  ("Kinnu the toddler girl smiling and waving, big friendly pose, bright background", 1216, 832),
    "thumb_count": ("Kinnu the toddler girl pointing at floating numbers one two three, excited", 1216, 832),
}


def main():
    args = sys.argv[1:]
    ref = DEFAULT_REF
    scale = 0.8
    # parse simple flags
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--ref" and i + 1 < len(args):
            ref = Path(args[i + 1]); i += 2
        elif args[i] == "--scale" and i + 1 < len(args):
            scale = float(args[i + 1]); i += 2
        else:
            rest.append(args[i]); i += 1

    # decide jobs: custom prompt (has spaces) vs preset names vs all
    jobs = []  # (name, prompt, w, h)
    if rest and any(" " in a for a in rest):
        for k, a in enumerate(rest):
            jobs.append((f"custom_{k+1}", a, 832, 1216))
    elif rest:
        for nm in rest:
            if nm in PRESETS:
                p, w, h = PRESETS[nm]; jobs.append((nm, p, w, h))
            else:
                print(f"[skip] unknown preset '{nm}' (known: {', '.join(PRESETS)})")
    else:
        jobs = [(nm, p, w, h) for nm, (p, w, h) in PRESETS.items()]

    if not jobs:
        print("nothing to do"); return
    if not ref.exists():
        print(f"[error] reference image not found: {ref}"); return

    OUT.mkdir(parents=True, exist_ok=True)
    rx = KinnuRemixer()
    made = []
    for nm, prompt, w, h in jobs:
        out = OUT / f"{nm}.png"
        print(f"[gen] {nm}: {prompt[:60]}...")
        rx.generate(str(ref), prompt, out, ip_scale=scale, width=w, height=h)
        made.append(out)
    rx.unload()

    # montage for quick review
    if made:
        cols = 4
        cw = 320
        rows = (len(made) + cols - 1) // cols
        m = Image.new("RGB", (cols * cw, rows * cw), (235, 238, 242))
        for k, p in enumerate(made):
            im = Image.open(p).convert("RGB"); im.thumbnail((cw - 10, cw - 10))
            x = (k % cols) * cw + 5; y = (k // cols) * cw + 5
            m.paste(im, (x, y))
        (ROOT / "dist").mkdir(exist_ok=True)
        m.save(ROOT / "dist" / "_kinnu_stills.png")
        print(f"made {len(made)} stills -> {OUT}")
        print("montage -> dist/_kinnu_stills.png")


if __name__ == "__main__":
    main()
