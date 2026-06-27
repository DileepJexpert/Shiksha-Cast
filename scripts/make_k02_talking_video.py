from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

from make_k02_talking_assets import BG_OUT, HOST_OUT, W, H, main as make_assets


ROOT = Path(__file__).resolve().parents[1]
EP = "k02-star-bridge-counting"
AUDIO_DIR = ROOT / "build" / EP / "audio"
CLIP_DIR = ROOT / "build" / EP / "talking_clips"
PREVIEW_DIR = ROOT / "build" / EP / "talking_preview"
OUT = ROOT / "dist" / f"{EP}.talking.mp4"


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    if width == 1:
        audio = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        audio = (audio - 128.0) / 128.0
    elif width == 2:
        audio = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    elif width == 4:
        audio = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {width}")

    if channels > 1:
        audio = audio.reshape((-1, channels)).mean(axis=1)
    return audio, sr


def audio_levels(path: Path, fps: int) -> tuple[np.ndarray, float]:
    audio, sr = read_wav_mono(path)
    dur = len(audio) / sr if sr else 0.0
    total = max(1, int(math.ceil(dur * fps)))
    win = max(1, int(sr / fps))
    vals = np.zeros(total, dtype=np.float32)
    for i in range(total):
        start = i * win
        end = min(len(audio), start + win)
        seg = audio[start:end]
        vals[i] = float(np.sqrt(np.mean(seg * seg) + 1e-9)) if len(seg) else 0.0

    if len(vals) >= 5:
        vals = np.convolve(vals, np.array([0.12, 0.24, 0.28, 0.24, 0.12], dtype=np.float32), mode="same")
    peak = float(np.percentile(vals, 93)) if vals.max() > 0 else 1.0
    vals = np.clip(vals / (peak + 1e-9), 0, 1)
    return vals, dur


def mouth_name(level: float) -> str:
    if level < 0.13:
        return "closed"
    if level < 0.48:
        return "half"
    return "open"


def scaled_host_images(height: int) -> dict[str, Image.Image]:
    states = {}
    for name in ["closed", "half", "open"]:
        img = Image.open(HOST_OUT / f"{name}.png").convert("RGBA")
        scale = height / img.height
        states[name] = img.resize((int(img.width * scale), height), Image.Resampling.LANCZOS)
    return states


def ken_burns(bg: Image.Image, frame: int, total: int, slide_n: int) -> Image.Image:
    t = frame / max(1, total - 1)
    zoom = 1.045 + 0.012 * math.sin((t + slide_n * 0.13) * math.pi)
    sw, sh = int(W * zoom), int(H * zoom)
    big = bg.resize((sw, sh), Image.Resampling.BICUBIC)
    max_x = sw - W
    max_y = sh - H
    x = int(max_x * (0.35 + 0.25 * math.sin(t * math.pi * 2 + slide_n)))
    y = int(max_y * (0.38 + 0.18 * math.cos(t * math.pi * 2 + slide_n * 0.7)))
    return big.crop((x, y, x + W, y + H))


def character_position(slide_n: int, frame: int, fps: int, total: int, host: Image.Image) -> tuple[int, int, float]:
    t = frame / fps
    slide_in = min(1.0, frame / max(1, int(fps * 0.55)))
    ease = 1 - (1 - slide_in) ** 3
    base_x = 275 + int(18 * math.sin(t * 2.2 + slide_n))
    x = int(-host.width * 0.65 + (base_x + host.width * 0.65) * ease)
    bob = int(13 * math.sin(t * 2 * math.pi * 0.75 + slide_n * 0.4))
    y = H - host.height - 12 + bob
    if slide_n in {3, 5, 6}:
        y += int(18 * math.sin(t * 2 * math.pi * 1.25))
    sway = 2.2 * math.sin(t * 2 * math.pi * 0.55 + slide_n)
    if frame > total - fps:
        x -= int((frame - (total - fps)) / fps * 45)
    return x, y, sway


def paste_rotated(frame: Image.Image, host: Image.Image, x: int, y: int, angle: float):
    rotated = host.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    frame.alpha_composite(rotated, (x - (rotated.width - host.width) // 2, y - (rotated.height - host.height) // 2))


def render_clip(slide_n: int, fps: int, host_height: int, keep_frames: bool) -> Path:
    audio = AUDIO_DIR / f"slide_{slide_n:03d}.wav"
    if not audio.exists():
        raise FileNotFoundError(f"Missing audio: {audio}")

    levels, speech_dur = audio_levels(audio, fps)
    duration = max(4.0, speech_dur + 0.75)
    total = int(math.ceil(duration * fps))
    bg = Image.open(BG_OUT / f"bg_{slide_n:03d}.png").convert("RGBA")
    hosts = scaled_host_images(host_height)

    work = Path(tempfile.mkdtemp(prefix=f"k02_talking_{slide_n:03d}_"))
    frame_dir = work / "frames"
    frame_dir.mkdir(parents=True)
    try:
        for f in range(total):
            frame = ken_burns(bg, f, total, slide_n)
            level = float(levels[f]) if f < len(levels) else 0.0
            state = mouth_name(level)
            host = hosts[state]
            x, y, angle = character_position(slide_n, f, fps, total, host)
            paste_rotated(frame, host, x, y, angle)
            frame.convert("RGB").save(frame_dir / f"frame_{f:05d}.jpg", quality=91, subsampling=1)

        CLIP_DIR.mkdir(parents=True, exist_ok=True)
        out = CLIP_DIR / f"clip_{slide_n:03d}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                str(fps),
                "-i",
                str(frame_dir / "frame_%05d.jpg"),
                "-i",
                str(audio),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{duration:.3f}",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
        )

        if keep_frames and slide_n == 1:
            PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
            preview_frame = frame_dir / f"frame_{min(total - 1, fps):05d}.jpg"
            shutil.copy2(preview_frame, PREVIEW_DIR / "preview_frame_slide_001.jpg")
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)


def concat_clips(clips: list[Path], out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    list_file = CLIP_DIR / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in clips),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(out),
        ],
        check=True,
    )


def build(slides: int, fps: int, host_height: int, out: Path):
    make_assets()
    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    clips = [render_clip(n, fps=fps, host_height=host_height, keep_frames=True) for n in range(1, slides + 1)]
    concat_clips(clips, out)
    print(f"Wrote talking K02 video: {out}")
    print(f"Wrote preview frame: {PREVIEW_DIR / 'preview_frame_slide_001.jpg'}")


def main():
    parser = argparse.ArgumentParser(description="Render K02 as a moving talking-Kinnu video.")
    parser.add_argument("--slides", type=int, default=8)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--host-height", type=int, default=640)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    build(args.slides, args.fps, args.host_height, args.out)


if __name__ == "__main__":
    main()
