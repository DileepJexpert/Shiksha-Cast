"""Character rig loader + pose compositor for the cutout cartoon engine.

A rig is a folder with rig.json describing separated PART PNGs (each drawn on a
full space-sized transparent canvas) plus their joint PIVOTS, and eye/mouth state
images. A POSE rotates parts about their pivots and picks an eye + mouth state.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


class Character:
    def __init__(self, rigdir: str | Path):
        self.dir = Path(rigdir)
        self.rig = json.loads((self.dir / "rig.json").read_text(encoding="utf-8"))
        self.space = tuple(self.rig["space"])
        self.feet = tuple(self.rig.get("feet", [self.space[0] // 2, self.space[1]]))
        self.scale_self = float(self.rig.get("scale", 1.0))
        self._cache: dict[str, Image.Image] = {}

    def _img(self, fn: str) -> Image.Image:
        im = self._cache.get(fn)
        if im is None:
            im = Image.open(self.dir / fn).convert("RGBA")
            self._cache[fn] = im
        return im

    def _posed_part(self, part: dict, angle_deg: float) -> Image.Image:
        im = self._img(part["img"])
        if abs(angle_deg) < 0.05:
            return im
        # positive angle => clockwise swing (PIL rotate is CCW, so negate)
        return im.rotate(-angle_deg, resample=Image.BICUBIC, center=tuple(part["pivot"]))

    def compose(self, pose: dict) -> Image.Image:
        """Render the character at `pose` into a space-sized RGBA image.
        pose = {angles:{part:deg}, mouth:'closed'|'half'|'open', eye:'open'|'closed'}"""
        out = Image.new("RGBA", self.space, (0, 0, 0, 0))
        angles = pose.get("angles", {})
        layers = [(p["z"], self._posed_part(p, float(angles.get(p["name"], 0.0)))) for p in self.rig["parts"]]
        eye = self.rig.get("eyes")
        if eye:
            layers.append((eye["z"], self._img(eye[pose.get("eye", "open")])))
        mouth = self.rig.get("mouths")
        if mouth:
            layers.append((mouth["z"], self._img(mouth[pose.get("mouth", "closed")])))
        for _z, im in sorted(layers, key=lambda t: t[0]):
            out.alpha_composite(im)
        return out

    def place(self, frame: Image.Image, pose: dict, x_frac: float, ground_y: float,
              char_h_px: float, facing: str = "right", bob: float = 0.0) -> None:
        """Composite the posed character onto `frame` (RGBA) at a screen position.
        x_frac is the feet x as a fraction of frame width; ground_y is feet baseline."""
        canvas = self.compose(pose)
        feetx, feety = self.feet
        if facing == "left":
            canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
            feetx = self.space[0] - feetx
        s = (char_h_px * self.scale_self) / self.space[1]
        canvas = canvas.resize((max(1, int(self.space[0] * s)), max(1, int(self.space[1] * s))), Image.LANCZOS)
        px = int(x_frac * frame.width - feetx * s)
        py = int(ground_y - feety * s - bob)
        frame.alpha_composite(canvas, (px, py))
