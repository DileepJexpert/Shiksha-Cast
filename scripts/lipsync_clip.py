"""Fully-local amplitude-driven talking-character clip — no external tools.

Reads a narration WAV, measures loudness per video frame, and swaps Kinnu's mouth
(closed / half / open) to fake lip movement, composited over a background with a
gentle idle bob. Good enough for a stickman character; for phoneme-accurate visemes
Rhubarb can be slotted in later (same rig).

Rig folder must contain rig.json:
  {"character": "base.png", "mouths": {"closed":..,"half":..,"open":..},
   "mouth_anchor": [x, y]}   # mouth CENTER within the character image

Usage:
  python scripts/lipsync_clip.py --audio a.wav --rig assets/kinnu_rig_placeholder \
      --out dist/talk.mp4 [--bg bg.png] [--fps 30]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image


def rms_per_frame(wav: str, fps: int):
    audio, sr = sf.read(wav)
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    audio = np.asarray(audio, dtype="float32")
    n = len(audio)
    dur = n / sr if sr else 0.0
    nframes = max(1, int(math.ceil(dur * fps)))
    win = max(1, int(sr / fps))
    vals = []
    for i in range(nframes):
        a = i * win
        b = min(n, a + win)
        seg = audio[a:b] if b > a else audio[max(0, n - 1):n]
        vals.append(float(np.sqrt(np.mean(seg ** 2) + 1e-9)) if len(seg) else 0.0)
    v = np.asarray(vals, dtype="float32")
    # smooth (reduce flicker) then normalize to the 95th percentile
    if len(v) >= 3:
        k = np.array([0.25, 0.5, 0.25], dtype="float32")
        v = np.convolve(v, k, mode="same")
    p = float(np.percentile(v, 95)) if v.max() > 0 else 1.0
    v = np.clip(v / (p + 1e-9), 0.0, 1.0)
    return v, dur


def _shape(level: float) -> str:
    if level < 0.12:
        return "closed"
    if level < 0.45:
        return "half"
    return "open"


def _load_rig(rigdir: str):
    """Return (frames_mode, assets, anchor). Two rig kinds are supported:
      frames mode  -> rig.json has {"frames": {"closed":..,"half":..,"open":..}}
                      each is a FULL character image (ChatGPT 3-mouth host). Swapped whole.
      base+mouth   -> rig.json has {"character":.., "mouths":{...}, "mouth_anchor":[x,y]}
                      a body PNG with separate mouth overlays.
    """
    rig = json.load(open(os.path.join(rigdir, "rig.json"), encoding="utf-8"))
    if rig.get("frames"):
        states = {k: Image.open(os.path.join(rigdir, v)).convert("RGBA") for k, v in rig["frames"].items()}
        return True, states, None
    char = Image.open(os.path.join(rigdir, rig["character"])).convert("RGBA")
    mouths = {k: Image.open(os.path.join(rigdir, v)).convert("RGBA") for k, v in rig["mouths"].items()}
    return False, {"_char": char, **{f"m_{k}": v for k, v in mouths.items()}}, rig["mouth_anchor"]


def build_talking_clip(
    audio: str,
    rigdir: str,
    out: str,
    bg: str | None = None,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
    char_height_frac: float = 0.78,
    char_x_frac: float = 0.5,
) -> float:
    """Render one talking-Kinnu clip over a background. char_x_frac is the character's
    horizontal CENTER as a fraction of width (0.18 = lower-left presenter, 0.5 = center)."""
    frames_mode, assets, anchor = _load_rig(rigdir)

    def rs(im):
        return im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))))

    if frames_mode:
        base = assets.get("closed") or next(iter(assets.values()))
        scale = (height * char_height_frac) / base.size[1]
        states = {k: rs(v) for k, v in assets.items()}
        cw, ch = (states.get("closed") or next(iter(states.values()))).size
    else:
        base = assets["_char"]
        scale = (height * char_height_frac) / base.size[1]
        char = rs(base)
        mouths = {k[2:]: rs(v) for k, v in assets.items() if k.startswith("m_")}
        ax, ay = int(anchor[0] * scale), int(anchor[1] * scale)
        cw, ch = char.size

    levels, dur = rms_per_frame(audio, fps)
    clip_dur = max(min_slide_s, pad_before_s + dur + pad_after_s)
    total_frames = int(clip_dur * fps)
    speech_start = int(pad_before_s * fps)

    if bg and os.path.exists(bg):
        background = Image.open(bg).convert("RGBA").resize((width, height))
    else:
        background = Image.new("RGBA", (width, height), (188, 226, 255, 255))

    px = max(0, min(int(width * char_x_frac - cw / 2), width - cw))
    py = height - ch - int(height * 0.02)

    tmp = tempfile.mkdtemp()
    try:
        for f in range(total_frames):
            frame = background.copy()
            bob = int(6 * math.sin(f / fps * 2 * math.pi * 0.6))  # gentle idle bob
            si = f - speech_start
            shape = _shape(float(levels[si])) if 0 <= si < len(levels) else "closed"
            if frames_mode:
                img = states.get(shape) or states.get("closed") or next(iter(states.values()))
                frame.alpha_composite(img, (px, py + bob))
            else:
                frame.alpha_composite(char, (px, py + bob))
                m = mouths.get(shape) or mouths.get("closed") or next(iter(mouths.values()))
                frame.alpha_composite(m, (px + ax - m.size[0] // 2, py + bob + ay - m.size[1] // 2))
            frame.convert("RGB").save(os.path.join(tmp, f"f_{f:05d}.png"))

        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        delay = int(pad_before_s * 1000)
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-framerate", str(fps), "-i", os.path.join(tmp, "f_%05d.png"),
             "-i", audio,
             "-filter_complex", f"[1:a]adelay={delay}|{delay},apad[a]",
             "-map", "0:v", "-map", "[a]",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
             "-c:a", "aac", "-b:a", "192k", "-t", f"{clip_dur:.3f}", "-shortest",
             "-movflags", "+faststart", out],
            check=True,
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return clip_dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--rig", default="assets/kinnu_rig_placeholder")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bg", default=None)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--char-x", type=float, default=0.5, help="character center x (0..1)")
    ap.add_argument("--char-h", type=float, default=0.78, help="character height fraction")
    a = ap.parse_args()
    d = build_talking_clip(a.audio, a.rig, a.out, bg=a.bg, fps=a.fps,
                           char_x_frac=a.char_x, char_height_frac=a.char_h)
    print(f"DONE {a.out} ({d:.1f}s)")


if __name__ == "__main__":
    main()
