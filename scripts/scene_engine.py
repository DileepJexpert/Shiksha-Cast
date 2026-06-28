"""Multi-character story -> video engine (fully local).

Renders a scene YAML into a narrated, captioned MP4 where a CAST of characters can
appear alone or together, each with their OWN voice, take turns speaking (lip-synced),
and enter from the sides. Characters live in assets/characters/<name>/ (rig.json +
closed/half/open PNGs). Backgrounds are plain scene images (no character baked in).

Scene YAML:
  title: "Kinnu and Gappu Learn Addition"
  cast: { kinnu: af_heart, gappu: am_michael }     # name -> Kokoro voice
  fps: 30
  scenes:
    - bg: build/k02-star-bridge-counting/backgrounds/bg_001.png
      place: { kinnu: 0.25, gappu: 0.75 }          # who is on screen + x (0..1)
      enter: { gappu: right }                       # optional: glide in from a side
      lines:
        - { who: kinnu, text: "Hi Gappu! Let's count." }
        - { who: gappu, text: "Yay, I love numbers!" }

Usage: python scripts/scene_engine.py content/scenes/<id>/scene.yaml [--out dist/<id>.mp4]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from shiksha_cast.assemble import concat_clips, mix_music_bed, normalize_loudness  # noqa: E402
from shiksha_cast.config import load_channel_config  # noqa: E402
from shiksha_cast.tts.kokoro import KokoroTTSProvider  # noqa: E402

from lipsync_clip import _load_rig, _shape, rms_per_frame  # noqa: E402

CHARS = ROOT / "assets" / "characters"


def _load_char(name: str):
    rigdir = CHARS / name
    frames_mode, assets, _ = _load_rig(str(rigdir))
    if not frames_mode:
        raise ValueError(f"Character {name} must be a frames-mode rig (closed/half/open).")
    rig = json.loads((rigdir / "rig.json").read_text(encoding="utf-8"))
    scale = float(rig.get("scale", 1.0))  # per-character height (e.g. 0.72 = toddler)
    return assets, scale  # ({closed, half, open} PIL RGBA, scale)


def _scaled(assets, char_h_px):
    base = assets.get("closed") or next(iter(assets.values()))
    scale = char_h_px / base.size[1]
    return {k: v.resize((max(1, int(v.size[0] * scale)), max(1, int(v.size[1] * scale)))) for k, v in assets.items()}


def _srt_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def render(scene_path: str, out: str | None = None):
    spec = yaml.safe_load(open(scene_path, encoding="utf-8"))
    cfg = load_channel_config(ROOT)
    W, H = cfg.resolution
    fps = int(spec.get("fps", cfg.fps))
    pad_b = cfg.timing.pad_before_ms / 1000
    pad_a = cfg.timing.pad_after_ms / 1000
    min_s = max(2.0, cfg.timing.min_slide_s - 1)
    char_h_px = int(H * float(spec.get("char_height", 0.62)))

    sid = Path(scene_path).parent.name
    work = ROOT / "build" / f"scene-{sid}"
    (work / "audio").mkdir(parents=True, exist_ok=True)
    clips_dir = work / "clips"; clips_dir.mkdir(parents=True, exist_ok=True)

    cast = spec.get("cast", {})
    char_assets = {}
    for name in cast:
        assets, cscale = _load_char(name)
        char_assets[name] = _scaled(assets, int(char_h_px * cscale))

    tts = KokoroTTSProvider()
    clip_paths = []
    captions = []  # (text, start, end)
    t_cursor = 0.0
    li = 0

    for scene in spec.get("scenes", []):
        bg_path = scene["bg"]
        bg = Image.open(bg_path).convert("RGBA").resize((W, H))
        place = scene.get("place", {})
        if not place:  # default: spread placed characters evenly
            names = [ln["who"] for ln in scene.get("lines", [])]
            uniq = list(dict.fromkeys(names))
            place = {n: (i + 1) / (len(uniq) + 1) for i, n in enumerate(uniq)}

        present = [{"name": n, "x": float(x), "phase": i * 1.3}
                   for i, (n, x) in enumerate(place.items())]

        # optional entrance glide
        enter = scene.get("enter", {})
        if enter:
            li += 1
            clip = clips_dir / f"clip_{li:03d}.mp4"
            _render_enter(bg, present, enter, char_assets, clip, fps, W, H)
            clip_paths.append(clip)
            t_cursor += 0.8

        for ln in scene.get("lines", []):
            who = ln["who"]; text = ln["text"]
            voice = cast.get(who, "af_heart")
            li += 1
            wav = work / "audio" / f"line_{li:03d}.wav"
            tts.set_speaker(voice)
            tts.synthesize(text, "", wav)
            clip = clips_dir / f"clip_{li:03d}.mp4"
            dur = _render_line(bg, present, who, str(wav), char_assets, clip,
                               fps, W, H, pad_b, pad_a, min_s)
            clip_paths.append(clip)
            captions.append((f"{who.title()}: {text}", t_cursor + pad_b, t_cursor + dur - pad_a))
            t_cursor += dur

    close = getattr(tts, "close", None)
    if close:
        close()

    out_path = Path(out) if out else (ROOT / "dist" / f"scene-{sid}.mp4")
    body = work / "body.mp4"
    print("[stage] concatenating...")
    concat_clips(clip_paths, body)

    music = (ROOT / cfg.music.bed) if cfg.music.bed else None
    if music and music.exists():
        print("[stage] music + -14 LUFS master...")
        mix_music_bed(body, music, out_path, cfg.music.duck_db, cfg.voice.sample_rate)
    else:
        normalize_loudness(body, out_path, cfg.voice.sample_rate)

    srt = out_path.with_suffix(".srt")
    with open(srt, "w", encoding="utf-8") as f:
        for i, (txt, a, b) in enumerate(captions, 1):
            f.write(f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{txt}\n\n")
    print(f"DONE -> {out_path}  (+ {srt.name})")


def _compose(bg, present, char_assets, shape_for, bob_for, W, H):
    frame = bg.copy()
    for ch in present:
        imgs = char_assets[ch["name"]]
        shape = shape_for(ch)
        img = imgs.get(shape) or imgs["closed"]
        px = max(0, min(int(W * ch["x"] - img.size[0] / 2), W - img.size[0]))
        py = H - img.size[1] - int(H * 0.02) + bob_for(ch)
        frame.alpha_composite(img, (px, py))
    return frame


def _encode(tmp, audio, out, clip_dur, fps, pad_before=0.3):
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(fps), "-i", str(Path(tmp) / "f_%05d.png")]
    if audio:
        delay = int(pad_before * 1000)
        args += ["-i", audio, "-filter_complex", f"[1:a]adelay={delay}|{delay},apad[a]",
                 "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        args += ["-f", "lavfi", "-t", f"{clip_dur:.3f}", "-i", "anullsrc=r=24000:cl=mono",
                 "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
    args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
             "-t", f"{clip_dur:.3f}", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(args, check=True)


def _render_line(bg, present, speaker, audio, char_assets, out, fps, W, H, pad_b, pad_a, min_s):
    levels, dur = rms_per_frame(audio, fps)
    clip_dur = max(min_s, pad_b + dur + pad_a)
    total = int(clip_dur * fps); speech_start = int(pad_b * fps)
    tmp = tempfile.mkdtemp()
    try:
        for f in range(total):
            def shape_for(ch, _f=f):
                if ch["name"] != speaker:
                    return "closed"
                si = _f - speech_start
                return _shape(float(levels[si])) if 0 <= si < len(levels) else "closed"

            def bob_for(ch, _f=f):
                return int(5 * math.sin(_f / fps * 2 * math.pi * 0.6 + ch["phase"]))

            _compose(bg, present, char_assets, shape_for, bob_for, W, H).convert("RGB").save(
                Path(tmp) / f"f_{f:05d}.png")
        _encode(tmp, audio, out, clip_dur, fps, pad_b)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return clip_dur


def _render_enter(bg, present, enter, char_assets, out, fps, W, H, dur=0.8):
    total = int(dur * fps)
    tmp = tempfile.mkdtemp()
    try:
        for f in range(total):
            prog = f / max(1, total - 1)
            def shape_for(_ch):
                return "closed"
            def bob_for(_ch, _f=f):
                return int(7 * math.sin(_f / fps * 2 * math.pi * 1.6))  # quicker bob = "stepping"

            frame = bg.copy()
            for ch in present:
                imgs = char_assets[ch["name"]]
                img = imgs["closed"]
                side = enter.get(ch["name"])
                if side == "left":
                    x = -0.2 + (ch["x"] + 0.2) * prog
                elif side == "right":
                    x = 1.2 - (1.2 - ch["x"]) * prog
                else:
                    x = ch["x"]
                px = int(W * x - img.size[0] / 2)
                py = H - img.size[1] - int(H * 0.02) + bob_for(ch)
                frame.alpha_composite(img, (px, py))
            frame.convert("RGB").save(Path(tmp) / f"f_{f:05d}.png")
        _encode(tmp, None, out, dur, fps)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    render(a.scene, a.out)


if __name__ == "__main__":
    main()
