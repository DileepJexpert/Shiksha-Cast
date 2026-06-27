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
    char_height_frac: float = 0.8,
) -> float:
    rig = json.load(open(os.path.join(rigdir, "rig.json"), encoding="utf-8"))
    char = Image.open(os.path.join(rigdir, rig["character"])).convert("RGBA")
    mouths = {k: Image.open(os.path.join(rigdir, v)).convert("RGBA") for k, v in rig["mouths"].items()}
    anchor = rig["mouth_anchor"]

    levels, dur = rms_per_frame(audio, fps)
    clip_dur = max(min_slide_s, pad_before_s + dur + pad_after_s)
    total_frames = int(clip_dur * fps)
    speech_start = int(pad_before_s * fps)

    if bg and os.path.exists(bg):
        background = Image.open(bg).convert("RGBA").resize((width, height))
    else:
        # soft sky gradient placeholder
        background = Image.new("RGBA", (width, height), (188, 226, 255, 255))

    scale = (height * char_height_frac) / char.size[1]
    cs = char.resize((int(char.size[0] * scale), int(char.size[1] * scale)))
    mouths_s = {k: m.resize((max(1, int(m.size[0] * scale)), max(1, int(m.size[1] * scale)))) for k, m in mouths.items()}
    ax, ay = int(anchor[0] * scale), int(anchor[1] * scale)
    px = (width - cs.size[0]) // 2
    py = height - cs.size[1] - int(height * 0.02)

    tmp = tempfile.mkdtemp()
    try:
        for f in range(total_frames):
            frame = background.copy()
            bob = int(6 * math.sin(f / fps * 2 * math.pi * 0.6))  # gentle idle bob
            si = f - speech_start
            shape = _shape(float(levels[si])) if 0 <= si < len(levels) else "closed"
            frame.alpha_composite(cs, (px, py + bob))
            m = mouths_s.get(shape) or mouths_s["closed"]
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
    a = ap.parse_args()
    d = build_talking_clip(a.audio, a.rig, a.out, bg=a.bg, fps=a.fps)
    print(f"DONE {a.out} ({d:.1f}s)")


if __name__ == "__main__":
    main()
