"""Advanced skeletal cutout character: 2-bone FK arms (upper_arm+forearm) and legs
(thigh+shin), a head that nods, swappable eyebrows/eyes and lip-sync mouth visemes.

Geometry (skeleton joints, pivots, per-part scale, etc.) is read from each character's
rig2.json when present, falling back to the defaults below (tuned for kinnu_hd). This lets
differently-proportioned characters (e.g. a chibi 3D-render Kinnu) define their own rig.

Pose dict:
  {"arm_left": (upper_deg, fore_deg), "arm_right": (...),
   "leg_left": (thigh_deg, shin_deg), "leg_right": (...),
   "head": deg, "brows": "...", "eyes": "...", "mouth": "A".."X", "bob": px}
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

# ---- defaults (kinnu_hd) ----
SPACE = (760, 1060)
FEET_Y = 1015
CX = 380
JOINTS = {
    "neck": (380, 452),
    "shoulder_left": (296, 516), "shoulder_right": (464, 516),
    "hip_left": (352, 648), "hip_right": (408, 648),
}
FACE = {"brows": (380, 250), "eyes": (380, 300), "mouth": (380, 372)}
PIVOT = {
    "torso": (0.5, 0.5), "head": (0.5, 0.95),
    "upper_arm": (0.5, 0.06), "forearm": (0.5, 0.13),
    "thigh": (0.5, 0.06), "shin": (0.5, 0.13),
}
BONE = {"upper_arm": 0.88, "forearm": 0.0, "thigh": 0.90, "shin": 0.0}
NECK_RAISE = 30
INK = (35, 32, 40, 255)


def _category(name: str) -> str:
    for suf in ("_left", "_right"):
        if name.endswith(suf):
            name = name[: -len(suf)]
    for pre in ("mouth", "eyes", "brows"):
        if name.startswith(pre):
            return pre
    return name


class SkeletalCharacter:
    def __init__(self, parts_dir: str | Path):
        self.dir = Path(parts_dir)
        self._cache: dict[str, Image.Image] = {}
        cfg = {}
        meta = self.dir / "rig2.json"
        if meta.exists():
            cfg = json.loads(meta.read_text())
        self.scale_self = float(cfg.get("scale", 1.0))
        self.space = tuple(cfg.get("space", SPACE))
        self.feet_y = float(cfg.get("feet_y", FEET_Y))
        self.cx = float(cfg.get("cx", CX))
        self.joints = {k: tuple(v) for k, v in cfg.get("joints", JOINTS).items()}
        self.face = {k: tuple(v) for k, v in cfg.get("face", FACE).items()}
        self.pivot = {k: tuple(v) for k, v in cfg.get("pivot", PIVOT).items()}
        self.bone = dict(cfg.get("bone", BONE))
        self.neck_raise = float(cfg.get("neck_raise", NECK_RAISE))
        self.part_scale = dict(cfg.get("part_scale", {}))
        self.overlay_only = bool(cfg.get("overlay_only", False))  # head has baked eyes/brows
        self.neck_stub = bool(cfg.get("neck_stub", True))
        self.torso_dy = float(cfg.get("torso_dy", -8))  # torso vertical nudge from neck

    def _img(self, name: str) -> Image.Image:
        im = self._cache.get(name)
        if im is None:
            im = Image.open(self.dir / f"{name}.png").convert("RGBA")
            s = self.part_scale.get(_category(name))
            if s and s != 1.0:
                im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
            self._cache[name] = im
        return im

    @staticmethod
    def _place_rot(canvas, img, pivot_xy, world_xy, angle_deg):
        m = max(img.size) + 8
        C = (m, m)
        tmp = Image.new("RGBA", (2 * m, 2 * m), (0, 0, 0, 0))
        tmp.alpha_composite(img, (int(C[0] - pivot_xy[0]), int(C[1] - pivot_xy[1])))
        if abs(angle_deg) > 0.05:
            tmp = tmp.rotate(-angle_deg, resample=Image.BICUBIC, center=C)
        canvas.alpha_composite(tmp, (int(world_xy[0] - C[0]), int(world_xy[1] - C[1])))

    def _skin(self):
        if getattr(self, "_skin_rgba", None) is None:
            im = self._img("upper_arm_left"); w, h = im.size
            self._skin_rgba = (250, 221, 184, 255)
            for y in range(h // 3, h):
                px = im.getpixel((w // 2, y))
                if len(px) == 4 and px[3] > 200:
                    self._skin_rgba = (px[0], px[1], px[2], 255); break
        return self._skin_rgba

    def _pv(self, name, key):
        im = self._img(name)
        fx, fy = self.pivot.get(key, PIVOT.get(key, (0.5, 0.06)))
        return (im.width * fx, im.height * fy)

    def _limb(self, canvas, upper_name, fore_name, shoulder, a_upper, a_fore, ukey, fkey):
        up = self._img(upper_name)
        upper_len = up.height * self.bone.get(ukey, 0.9)
        self._place_rot(canvas, up, self._pv(upper_name, ukey), shoulder, a_upper)
        rad = math.radians(a_upper)
        elbow = (shoulder[0] - math.sin(rad) * upper_len, shoulder[1] + math.cos(rad) * upper_len)
        self._place_rot(canvas, self._img(fore_name), self._pv(fore_name, fkey), elbow, a_upper + a_fore)

    def _has(self, name):
        return (self.dir / f"{name}.png").exists()

    def compose(self, pose: dict) -> Image.Image:
        c = Image.new("RGBA", self.space, (0, 0, 0, 0))
        al = pose.get("arm_left", (0, 0)); ar = pose.get("arm_right", (0, 0))
        ll = pose.get("leg_left", (0, 0)); lr = pose.get("leg_right", (0, 0))
        J = self.joints
        self._limb(c, "upper_arm_left", "forearm_left", J["shoulder_left"], al[0], al[1], "upper_arm", "forearm")
        self._limb(c, "thigh_left", "shin_left", J["hip_left"], ll[0], ll[1], "thigh", "shin")
        self._limb(c, "thigh_right", "shin_right", J["hip_right"], lr[0], lr[1], "thigh", "shin")
        nx, ny = J["neck"]
        nr = self.neck_raise
        if self.neck_stub:
            ImageDraw.Draw(c).rounded_rectangle(
                [nx - 24, ny - nr - 6, nx + 24, ny + 14], radius=12,
                fill=self._skin(), outline=INK, width=5)
        self._place_rot(c, self._img("torso"), self._pv("torso", "torso"),
                        (self.cx, ny + self._img("torso").height * 0.5 + self.torso_dy), 0)
        ha = pose.get("head", 0.0)
        self._place_rot(c, self._img("head"), self._pv("head", "head"), (nx, ny - nr), ha)
        # face overlays
        if self.overlay_only:
            layers = (("mouth_" + pose.get("mouth", "X"), "mouth"),)
        else:
            layers = (("brows_" + pose.get("brows", "neutral"), "brows"),
                      ("eyes_" + pose.get("eyes", "open"), "eyes"),
                      ("mouth_" + pose.get("mouth", "X"), "mouth"))
        for layer, key in layers:
            if not self._has(layer) or key not in self.face:
                continue
            im = self._img(layer)
            self._place_rot(c, im, (im.width / 2, im.height / 2),
                            (self.face[key][0], self.face[key][1] - nr), ha)
        self._limb(c, "upper_arm_right", "forearm_right", J["shoulder_right"], ar[0], ar[1], "upper_arm", "forearm")
        return c

    def place(self, frame, pose, x_frac, ground_y, char_h_px, facing="right", bob=0.0):
        canvas = self.compose(pose)
        feetx, feety = self.cx, self.feet_y
        if facing == "left":
            canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
            feetx = self.space[0] - feetx
        s = (char_h_px * self.scale_self) / self.space[1]
        canvas = canvas.resize((max(1, int(self.space[0] * s)), max(1, int(self.space[1] * s))), Image.LANCZOS)
        px = int(x_frac * frame.width - feetx * s)
        py = int(ground_y - feety * s - bob)
        frame.alpha_composite(canvas, (px, py))


if __name__ == "__main__":
    import sys
    ROOT = Path(__file__).resolve().parents[3]
    cdir = sys.argv[2] if len(sys.argv) > 2 else "assets/cartoon/characters/kinnu_hd"
    ch = SkeletalCharacter(ROOT / cdir)
    pose = {"arm_left": (4, 3), "arm_right": (-4, -3), "mouth": "X"}
    bg = Image.new("RGBA", (900, 1100), (175, 222, 255, 255))
    ch.place(bg, pose, 0.5, 1060, 1000)
    out = ROOT / "dist" / "rig2_test.png"
    bg.convert("RGB").save(out); print("saved", out)
