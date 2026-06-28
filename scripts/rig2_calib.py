"""Render a grid of rig2 poses for visual calibration of the advanced Kinnu."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from shiksha_cast.cartoon.rig2 import SkeletalCharacter  # noqa: E402

ch = SkeletalCharacter(ROOT / "assets" / "cartoon" / "source" / "parts")

POSES = {
    "stand": {},
    "wave": {"arm_right": (120, 28), "eyes": "happy", "mouth": "D", "brows": "happy"},
    "point_up": {"arm_right": (150, 8), "mouth": "C"},
    "point_side": {"arm_right": (95, 6), "mouth": "B", "brows": "surprised"},
    "count": {"arm_right": (120, 30), "arm_left": (-120, -30), "mouth": "D", "eyes": "happy"},
    "walk_a": {"leg_left": (24, -20), "leg_right": (-22, -4), "arm_left": (-16, -8),
               "arm_right": (16, -8), "mouth": "C", "bob": 8},
    "walk_b": {"leg_left": (-22, -4), "leg_right": (24, -20), "arm_left": (16, -8),
               "arm_right": (-16, -8), "mouth": "C", "bob": 8},
}

cell = 460
names = list(POSES)
cols = 4
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * cell, rows * cell), (180, 222, 255, 255))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    tile = Image.new("RGBA", (cell, cell), (180, 222, 255, 255))
    ch.place(tile, POSES[n], 0.5, cell - 12, int(cell * 0.92), bob=POSES[n].get("bob", 0))
    sheet.alpha_composite(tile, ((i % cols) * cell, (i // cols) * cell))
    d.text(((i % cols) * cell + 8, (i // cols) * cell + 8), n, fill=(20, 20, 40))
sheet.convert("RGB").save(ROOT / "dist" / "rig2_calib.png")
print("saved dist/rig2_calib.png")
