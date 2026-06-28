"""Advanced skeletal cutout character: 2-bone FK arms (upper_arm+forearm) and legs
(thigh+shin), a head that nods, swappable eyebrows (4), eyes (3) and 9 lip-sync
visemes. Built from the sliced rig-sheet parts in a character folder.

Pose dict:
  {
    "arm_left":  (upper_deg, fore_deg), "arm_right": (...),
    "leg_left":  (thigh_deg, shin_deg), "leg_right": (...),
    "head": deg, "brows": "neutral|happy|sad|surprised",
    "eyes": "open|closed|happy", "mouth": "A".."H"|"X", "bob": px,
  }
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

# Skeleton in the rig's own coordinate space (scaled at place()-time).
SPACE = (760, 1060)
FEET_Y = 1015
CX = 380
JOINTS = {
    "neck": (380, 452),
    "shoulder_left": (296, 516), "shoulder_right": (464, 516),
    "hip_left": (352, 648), "hip_right": (408, 648),
}
# face anchors (centre points) relative to the rig space; tuned to the head art
FACE = {"brows": (380, 250), "eyes": (380, 300), "mouth": (380, 372)}
PIVOT = {  # (fx, fy) fraction of each part image = its joint/rotation point (measured)
    "torso": (0.5, 0.5), "head": (0.5, 0.95),
    "upper_arm": (0.5, 0.03), "forearm": (0.5, 0.03),
    "thigh": (0.5, 0.03), "shin": (0.5, 0.03),
}
BONE = {"upper_arm": 0.97, "forearm": 0.0, "thigh": 0.97, "shin": 0.0}  # elbow/knee at ~97% of segment


class SkeletalCharacter:
    def __init__(self, parts_dir: str | Path):
        self.dir = Path(parts_dir)
        self._cache: dict[str, Image.Image] = {}
        self.scale_self = 1.0
        meta = self.dir / "rig2.json"
        if meta.exists():
            self.scale_self = float(json.loads(meta.read_text()).get("scale", 1.0))

    def _img(self, name: str) -> Image.Image:
        im = self._cache.get(name)
        if im is None:
            im = Image.open(self.dir / f"{name}.png").convert("RGBA")
            self._cache[name] = im
        return im

    @staticmethod
    def _place_rot(canvas, img, pivot_xy, world_xy, angle_deg):
        """Rotate img about its pivot and composite so the pivot lands at world_xy."""
        m = max(img.size) + 8
        C = (m, m)
        tmp = Image.new("RGBA", (2 * m, 2 * m), (0, 0, 0, 0))
        tmp.alpha_composite(img, (int(C[0] - pivot_xy[0]), int(C[1] - pivot_xy[1])))
        if abs(angle_deg) > 0.05:
            tmp = tmp.rotate(-angle_deg, resample=Image.BICUBIC, center=C)
        canvas.alpha_composite(tmp, (int(world_xy[0] - C[0]), int(world_xy[1] - C[1])))

    def _pv(self, name, key):
        im = self._img(name)
        fx, fy = PIVOT[key]
        return (im.width * fx, im.height * fy)

    def _limb(self, canvas, upper_name, fore_name, shoulder, a_upper, a_fore, ukey, fkey):
        up = self._img(upper_name)
        upper_len = up.height * BONE[ukey]
        # upper bone
        self._place_rot(canvas, up, self._pv(upper_name, ukey), shoulder, a_upper)
        # elbow = shoulder + R(a_upper) * (0, upper_len)   (down is +y)
        rad = math.radians(a_upper)
        elbow = (shoulder[0] + math.sin(rad) * upper_len, shoulder[1] + math.cos(rad) * upper_len)
        self._place_rot(canvas, self._img(fore_name), self._pv(fore_name, fkey), elbow, a_upper + a_fore)

    def compose(self, pose: dict) -> Image.Image:
        c = Image.new("RGBA", SPACE, (0, 0, 0, 0))
        al = pose.get("arm_left", (0, 0)); ar = pose.get("arm_right", (0, 0))
        ll = pose.get("leg_left", (0, 0)); lr = pose.get("leg_right", (0, 0))
        # back limbs (left)
        self._limb(c, "upper_arm_left", "forearm_left", JOINTS["shoulder_left"], al[0], al[1], "upper_arm", "forearm")
        self._limb(c, "thigh_left", "shin_left", JOINTS["hip_left"], ll[0], ll[1], "thigh", "shin")
        # front leg (right) behind torso too
        self._limb(c, "thigh_right", "shin_right", JOINTS["hip_right"], lr[0], lr[1], "thigh", "shin")
        # torso
        self._place_rot(c, self._img("torso"), self._pv("torso", "torso"),
                        (CX, JOINTS["neck"][1] + self._img("torso").height * 0.5 - 8), 0)
        # head + face (nods together)
        ha = pose.get("head", 0.0)
        self._place_rot(c, self._img("head"), self._pv("head", "head"), JOINTS["neck"], ha)
        for layer, key in (("brows_" + pose.get("brows", "neutral"), "brows"),
                           ("eyes_" + pose.get("eyes", "open"), "eyes"),
                           ("mouth_" + pose.get("mouth", "X"), "mouth")):
            im = self._img(layer)
            self._place_rot(c, im, (im.width / 2, im.height / 2), FACE[key], ha)
        # front arm (right) over torso
        self._limb(c, "upper_arm_right", "forearm_right", JOINTS["shoulder_right"], ar[0], ar[1], "upper_arm", "forearm")
        return c

    def place(self, frame, pose, x_frac, ground_y, char_h_px, facing="right", bob=0.0):
        canvas = self.compose(pose)
        feetx, feety = CX, FEET_Y
        if facing == "left":
            canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
            feetx = SPACE[0] - feetx
        s = (char_h_px * self.scale_self) / SPACE[1]
        canvas = canvas.resize((max(1, int(SPACE[0] * s)), max(1, int(SPACE[1] * s))), Image.LANCZOS)
        px = int(x_frac * frame.width - feetx * s)
        py = int(ground_y - feety * s - bob)
        frame.alpha_composite(canvas, (px, py))


if __name__ == "__main__":  # quick visual test
    import sys
    ROOT = Path(__file__).resolve().parents[3]
    parts = ROOT / "assets" / "cartoon" / "source" / "parts"
    ch = SkeletalCharacter(parts)
    poses = {
        "stand": {"eyes": "open", "mouth": "X", "brows": "neutral"},
        "wave": {"arm_right": (140, -42), "eyes": "happy", "mouth": "D", "brows": "happy"},
        "walk": {"leg_left": (22, -18), "leg_right": (-22, -5), "arm_left": (-18, -10),
                 "arm_right": (18, -10), "mouth": "C", "bob": 8},
    }
    name = sys.argv[1] if len(sys.argv) > 1 else "stand"
    bg = Image.new("RGBA", (900, 1100), (175, 222, 255, 255))
    ch.place(bg, poses[name], 0.5, 1060, 1000, bob=poses[name].get("bob", 0))
    out = ROOT / "dist" / f"rig2_{name}.png"
    bg.convert("RGB").save(out)
    print("saved", out)
