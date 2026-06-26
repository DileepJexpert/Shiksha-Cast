"""Turn an episode's slides + YOUR recorded audio into a video — no TTS, no AI.

Record one clip per slide (any format: wav/mp3/m4a), name them in order
(01, 02, 03 … or slide-01, slide-02 …), drop them in the episode's audio/
folder, and run this. Each slide shows for exactly the length of its clip,
so picture and voice stay in sync automatically.

Usage:
  python make_video.py episodes/ep01_how-does-ai-work
  python make_video.py episodes/ep01_how-does-ai-work --audio path/to/clips --out my.mp4

Slides are read from <episode>/png/slide-*.png (rendered by render.sh).
Output defaults to <episode>/video.mp4.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# reuse the project's tested ffmpeg helpers
from shiksha_cast.assemble import _run_ffmpeg, concat_clips, probe_duration

AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus")
W, H = 1920, 1080  # standard 1080p (slides are 16:9; libx264 needs even dims)


def build_clip(slide_png, audio, out_mp4, clip_dur, pad_before_s, fps):
    """One slide held for clip_dur with the audio (scaled to even 1080p)."""
    delay_ms = int(pad_before_s * 1000)
    _run_ffmpeg([
        "-loop", "1", "-i", str(slide_png),
        "-i", str(audio),
        "-vf", f"scale={W}:{H},format=yuv420p",
        "-c:v", "libx264", "-tune", "stillimage", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-af", f"adelay={delay_ms}|{delay_ms},apad",
        "-t", f"{clip_dur:.3f}", "-shortest", "-pix_fmt", "yuv420p",
        str(out_mp4),
    ])


def find_audio(audio_dir: Path) -> list[Path]:
    files = [p for p in audio_dir.iterdir() if p.suffix.lower() in AUDIO_EXTS]
    return sorted(files, key=lambda p: p.name.lower())


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a video from slides + your recorded audio.")
    ap.add_argument("episode", help="episode folder, e.g. episodes/ep01_how-does-ai-work")
    ap.add_argument("--audio", help="folder with your per-slide clips (default: <episode>/audio)")
    ap.add_argument("--out", help="output mp4 (default: <episode>/video.mp4)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--pad-before", type=float, default=0.25, help="silence before each clip (s)")
    ap.add_argument("--pad-after", type=float, default=0.6, help="silence after each clip (s)")
    args = ap.parse_args()

    ep = Path(args.episode).resolve()  # absolute, so concat list resolves clips correctly
    slides = sorted((ep / "png").glob("slide-*.png"))
    audio_dir = (Path(args.audio).resolve() if args.audio else ep / "audio")
    out = (Path(args.out).resolve() if args.out else ep / "video.mp4")

    if not slides:
        sys.exit(f"No slides found in {ep/'png'} — run render.sh first.")
    if not audio_dir.is_dir():
        sys.exit(f"No audio folder: {audio_dir}\nRecord one clip per slide and put them there "
                 f"(named 01, 02, … in order).")

    clips_audio = find_audio(audio_dir)
    if not clips_audio:
        sys.exit(f"No audio files in {audio_dir} (looked for {', '.join(AUDIO_EXTS)}).")

    if len(clips_audio) != len(slides):
        print(f"[warn] {len(slides)} slides but {len(clips_audio)} audio clips — "
              f"pairing the first {min(len(slides), len(clips_audio))} in order.")

    work = ep / "_clips"
    work.mkdir(exist_ok=True)
    n = min(len(slides), len(clips_audio))
    clip_paths: list[Path] = []
    total = 0.0
    for i in range(n):
        slide, aud = slides[i], clips_audio[i]
        dur = probe_duration(aud)
        clip_dur = max(1.0, args.pad_before + dur + args.pad_after)
        clip = work / f"clip_{i+1:03d}.mp4"
        print(f"  slide {i+1:02d}: {slide.name}  +  {aud.name}  ({dur:.1f}s)")
        build_clip(slide, aud, clip, clip_dur, args.pad_before, args.fps)
        clip_paths.append(clip)
        total += clip_dur

    print(f"[assemble] {n} clips -> {out}")
    concat_clips(clip_paths, out)
    # tidy temp clips
    for c in clip_paths:
        c.unlink(missing_ok=True)
    try:
        work.rmdir()
    except OSError:
        pass
    print(f"[done] {out}  ({total:.0f}s, {n} slides)")


if __name__ == "__main__":
    main()
