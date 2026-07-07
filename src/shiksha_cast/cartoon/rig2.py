"""Advanced skeletal cutout character: 2-bone FK arms (upper_arm+forearm) and legs
(thigh+shin), a head that nods, swappable eyebrows/eyes and lip-sync mouth visemes.

Geometry (skeleton joints, pivots, per-part scale, etc.) is read from each character's
rig2.json when present, falling back to the defaults below (tuned for kinnu_hd). This lets
differently-proportioned characters (e.g. a chibi 3D-render Kinnu) define their own rig.

Pose dict:
  {"arm_left": (upper_deg, fore_deg), "arm_right": (...),
   "leg_left": (thigh_deg, shin_deg), "leg_right": (...),
   "head": deg, "head_turn": "center|left|right|back",
   "tail": deg, "brows": "...", "eyes": "...", "mouth": "A".."X", "bob": px}
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
    "tail": (0.12, 0.78),
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
        self.joint_caps = {
            "shoulder": True,
            "elbow": True,
            "knee": True,
            **dict(cfg.get("joint_caps", {})),
        }
        self.joint_cap_min_bend = {
            "knee": 18.0,
            **{k: float(v) for k, v in dict(cfg.get("joint_cap_min_bend", {})).items()},
        }
        # Extra transparent canvas around the rig prevents hands/props from being
        # clipped when arms point sideways or cheer overhead.
        self.render_padding = int(cfg.get("render_padding", 220))

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

    def _joint_trimmed_img(self, name: str, key: str) -> Image.Image:
        """Hide overlap bands so lower limbs read as connected at the joint.

        Shin/forearm artwork has a rounded top that is useful for bent poses, but
        it visibly stacks over the upper limb in straight or side-point poses. We
        keep the same pivot and placement, then soften only the hidden top band.
        """
        im = self._img(name)
        if key not in ("shin", "forearm"):
            return im
        cache_key = f"{name}__joint_trimmed"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        out = im.copy()
        pivot_y = int(self._pv(name, key)[1])
        trim_to = max(0, pivot_y - (4 if key == "shin" else 3))
        fade = 8 if key == "shin" else 7
        alpha = out.getchannel("A")
        for y in range(min(out.height, trim_to + fade)):
            if y < trim_to:
                factor = 0.0
            else:
                factor = (y - trim_to + 1) / fade
            if factor >= 1.0:
                continue
            for x in range(out.width):
                alpha.putpixel((x, y), int(alpha.getpixel((x, y)) * factor))
        out.putalpha(alpha)
        self._cache[cache_key] = out
        return out

    def _limb(self, canvas, upper_name, fore_name, shoulder, a_upper, a_fore, ukey, fkey):
        up = self._img(upper_name)
        upper_len = up.height * self.bone.get(ukey, 0.9)
        self._place_rot(canvas, up, self._pv(upper_name, ukey), shoulder, a_upper)
        if ukey == "upper_arm" and self.joint_caps.get("shoulder", True):
            self._place_shoulder_cap(canvas, shoulder)
        rad = math.radians(a_upper)
        elbow = (shoulder[0] - math.sin(rad) * upper_len, shoulder[1] + math.cos(rad) * upper_len)
        self._place_rot(
            canvas,
            self._joint_trimmed_img(fore_name, fkey),
            self._pv(fore_name, fkey),
            elbow,
            a_upper + a_fore,
        )
        if (
            fkey == "shin"
            and self.joint_caps.get("knee", True)
            and abs(float(a_fore)) >= self.joint_cap_min_bend.get("knee", 18.0)
        ):
            side = "left" if fore_name.endswith("_left") else "right"
            self._place_knee_cap(canvas, side, elbow, a_upper + a_fore * 0.5)
        elif fkey == "forearm" and self.joint_caps.get("elbow", True):
            side = "left" if fore_name.endswith("_left") else "right"
            self._place_elbow_cap(canvas, side, elbow, a_upper + a_fore * 0.5)

    def _place_shoulder_cap(self, canvas, shoulder):
        x, y = shoulder
        draw = ImageDraw.Draw(canvas)
        draw.ellipse(
            [x - 17, y - 17, x + 17, y + 17],
            fill=self._skin(),
        )

    def _place_elbow_cap(self, canvas, side, elbow, angle_deg):
        name = f"elbow_{side}"
        if self._has(name):
            im = self._img(name)
            self._place_rot(canvas, im, (im.width / 2, im.height / 2), elbow, angle_deg)
            return
        x, y = elbow
        draw = ImageDraw.Draw(canvas)
        draw.ellipse(
            [x - 18, y - 18, x + 18, y + 18],
            fill=self._skin(),
        )

    def _place_knee_cap(self, canvas, side, knee, angle_deg):
        name = f"knee_{side}"
        if self._has(name):
            im = self._img(name)
            self._place_rot(canvas, im, (im.width / 2, im.height / 2), knee, angle_deg)
            return
        x, y = knee
        ImageDraw.Draw(canvas).rounded_rectangle(
            [x - 22, y - 12, x + 22, y + 18],
            radius=15,
            fill=self._skin(),
        )

    def _has(self, name):
        return (self.dir / f"{name}.png").exists()

    def _head_asset_name(self, turn: str) -> str:
        if turn != "center" and self._has(f"head_{turn}"):
            return f"head_{turn}"
        return "head"

    @staticmethod
    def _face_shift(turn: str) -> int:
        if turn == "left":
            return -48
        if turn == "right":
            return 48
        return 0

    def _place_tail(self, canvas, joint, angle_deg):
        if not self._has("tail"):
            return
        im = self._img("tail")
        self._place_rot(canvas, im, self._pv("tail", "tail"), joint, angle_deg)

    def compose(self, pose: dict, padding: int = 0) -> Image.Image:
        c = Image.new(
            "RGBA",
            (int(self.space[0] + padding * 2), int(self.space[1] + padding * 2)),
            (0, 0, 0, 0),
        )
        def off(point):
            return (point[0] + padding, point[1] + padding)

        al = pose.get("arm_left", (0, 0)); ar = pose.get("arm_right", (0, 0))
        ll = pose.get("leg_left", (0, 0)); lr = pose.get("leg_right", (0, 0))
        J = self.joints
        if "tail" in J:
            self._place_tail(c, off(J["tail"]), pose.get("tail", 0.0))
        self._limb(
            c, "upper_arm_left", "forearm_left",
            off(J["shoulder_left"]), al[0], al[1], "upper_arm", "forearm",
        )
        self._limb(
            c, "thigh_left", "shin_left",
            off(J["hip_left"]), ll[0], ll[1], "thigh", "shin",
        )
        self._limb(
            c, "thigh_right", "shin_right",
            off(J["hip_right"]), lr[0], lr[1], "thigh", "shin",
        )
        nx, ny = off(J["neck"])
        nr = self.neck_raise
        if self.neck_stub:
            ImageDraw.Draw(c).rounded_rectangle(
                [nx - 24, ny - nr - 6, nx + 24, ny + 14], radius=12,
                fill=self._skin(), outline=INK, width=5)
        self._place_rot(c, self._img("torso"), self._pv("torso", "torso"),
                        (self.cx + padding, ny + self._img("torso").height * 0.5 + self.torso_dy), 0)
        ha = pose.get("head", 0.0)
        head_turn = str(pose.get("head_turn", "center") or "center")
        head_name = self._head_asset_name(head_turn)
        self._place_rot(c, self._img(head_name), self._pv(head_name, "head"), (nx, ny - nr), ha)
        # face overlays
        if head_turn == "back":
            layers = ()
        elif self.overlay_only:
            layers = (("mouth_" + pose.get("mouth", "X"), "mouth"),)
        else:
            layers = (("brows_" + pose.get("brows", "neutral"), "brows"),
                      ("eyes_" + pose.get("eyes", "open"), "eyes"),
                      ("mouth_" + pose.get("mouth", "X"), "mouth"))
        face_shift_x = self._face_shift(head_turn)
        for layer, key in layers:
            if not self._has(layer) or key not in self.face:
                continue
            im = self._img(layer)
            self._place_rot(c, im, (im.width / 2, im.height / 2),
                            (self.face[key][0] + face_shift_x + padding,
                             self.face[key][1] + padding - nr), ha)
        if pose.get("tears"):
            self._draw_tears(c, padding, nr)
        self._limb(
            c, "upper_arm_right", "forearm_right",
            off(J["shoulder_right"]), ar[0], ar[1], "upper_arm", "forearm",
        )
        return c

    def _draw_tears(self, canvas, padding, neck_raise):
        draw = ImageDraw.Draw(canvas)
        ex, ey = self.face.get("eyes", FACE["eyes"])
        blue = (80, 185, 255, 225)
        outline = (35, 120, 190, 180)
        for dx in (-46, 46):
            x = ex + padding + dx
            y = ey + padding - neck_raise + 34
            points = [(x, y - 14), (x - 8, y + 4), (x, y + 14), (x + 8, y + 4)]
            draw.polygon(points, fill=blue)
            draw.line(points + [points[0]], fill=outline, width=2)

    def _water_wash(self, canvas):
        alpha = canvas.getchannel("A")
        wash = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(wash)
        for y in range(canvas.height):
            strength = int(32 + 52 * (y / max(1, canvas.height - 1)))
            draw.line((0, y, canvas.width, y), fill=(65, 180, 225, strength))
        canvas = Image.alpha_composite(canvas, wash)
        canvas.putalpha(alpha)
        return canvas

    def _draw_swim_ripples(self, frame, px, py, width, height):
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        cx = px + width * 0.47
        cy = py + height * 0.62
        base_w = width * 0.82
        base_h = height * 0.24
        for i, alpha in enumerate((155, 105, 70)):
            grow = 1.0 + i * 0.18
            bbox = (
                int(cx - base_w * grow / 2),
                int(cy - base_h * grow / 2),
                int(cx + base_w * grow / 2),
                int(cy + base_h * grow / 2),
            )
            draw.ellipse(bbox, outline=(225, 255, 255, alpha), width=4)
        frame.alpha_composite(overlay)

    def _place_side_sprite(self, frame, sprite_name, x_frac, ground_y, char_h_px, facing="right", bob=0.0):
        if not self._has(sprite_name):
            return False
        sprite = self._img(sprite_name)
        s = (char_h_px * self.scale_self) / self.space[1]
        sprite = sprite.resize(
            (max(1, int(sprite.width * s)), max(1, int(sprite.height * s))),
            Image.LANCZOS,
        )
        if facing == "left":
            sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)
        px = int(x_frac * frame.width - sprite.width * 0.5)
        py = int(ground_y - sprite.height - bob)
        frame.alpha_composite(sprite, (px, py))
        return True

    def place(self, frame, pose, x_frac, ground_y, char_h_px, facing="right", bob=0.0):
        side_sprite = pose.get("side_sprite")
        if side_sprite and self._place_side_sprite(
            frame,
            str(side_sprite),
            x_frac,
            ground_y,
            char_h_px,
            facing=facing,
            bob=bob,
        ):
            return
        padding = self.render_padding
        canvas = self.compose(pose, padding=padding)
        feetx, feety = self.cx + padding, self.feet_y + padding
        if facing == "left":
            canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
            feetx = canvas.width - feetx
        s = (char_h_px * self.scale_self) / self.space[1]
        canvas = canvas.resize(
            (max(1, int(canvas.width * s)), max(1, int(canvas.height * s))),
            Image.LANCZOS,
        )
        body_angle = float(pose.get("body_angle", 0.0) or 0.0)
        if abs(body_angle) > 0.05:
            canvas = canvas.rotate(body_angle, resample=Image.BICUBIC, expand=True)
            bbox = canvas.getchannel("A").getbbox()
            if bbox is not None:
                canvas = canvas.crop(bbox)
            if pose.get("water_tint"):
                canvas = self._water_wash(canvas)
            px = int(x_frac * frame.width - canvas.width * 0.5)
            anchor = 0.5 if pose.get("body_anchor") == "center" else 0.55
            py = int(ground_y - canvas.height * anchor - bob)
            frame.alpha_composite(canvas, (px, py))
            if pose.get("water_tint"):
                self._draw_swim_ripples(frame, px, py, canvas.width, canvas.height)
            return
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
