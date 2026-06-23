from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AssembleResult:
    video_path: Path
    slide_count: int
    total_duration: float


class FFmpegNotFoundError(RuntimeError):
    """Raised when the ffmpeg binary cannot be found on PATH."""


def _ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise FFmpegNotFoundError(
            "FFmpeg was not found on your PATH. Install it and try again:\n"
            "  Windows: winget install --id Gyan.FFmpeg  (then restart the terminal)\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt install ffmpeg\n"
            "Verify with: ffmpeg -version"
        )


def _run_ffmpeg(args: list[str]) -> None:
    _ensure_ffmpeg()
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FFmpeg failed (exit {e.returncode}):\n{e.stderr}"
        ) from e


def build_slide_clip(
    slide_png: Path,
    audio_wav: Path,
    output_mp4: Path,
    duration: float,
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
    fps: int = 30,
) -> float:
    """Create a single slide video clip (image + audio)."""
    clip_dur = max(min_slide_s, pad_before_s + duration + pad_after_s)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    _run_ffmpeg([
        "-loop", "1",
        "-i", str(slide_png),
        "-i", str(audio_wav),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-t", f"{clip_dur:.3f}",
        "-af", f"adelay={int(pad_before_s * 1000)}|{int(pad_before_s * 1000)},apad",
        "-shortest",
        str(output_mp4),
    ])
    return clip_dur


def build_kenburns_clip(
    image_png: Path,
    audio_wav: Path,
    output_mp4: Path,
    duration: float,
    effect_index: int = 0,
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> float:
    """Create a video clip with Ken Burns zoom/pan animation on the image."""
    clip_dur = max(min_slide_s, pad_before_s + duration + pad_after_s)
    frames = int(clip_dur * fps)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    effects = [
        f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:s={width}x{height}:fps={fps}",
        f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0008))':d={frames}:s={width}x{height}:fps={fps}",
        f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}",
        f"zoompan=z='1.15':x='if(lte(on,1),0,x+1)':d={frames}:s={width}x{height}:fps={fps}",
    ]
    vf = effects[effect_index % len(effects)]

    _run_ffmpeg([
        "-i", str(image_png),
        "-i", str(audio_wav),
        "-vf", vf,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{clip_dur:.3f}",
        "-af", f"adelay={int(pad_before_s * 1000)}|{int(pad_before_s * 1000)},apad",
        "-shortest",
        str(output_mp4),
    ])
    return clip_dur


def concat_clips(clip_paths: list[Path], output_mp4: Path) -> None:
    """Concatenate per-slide clips into a single video."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, dir=str(output_mp4.parent)
    ) as f:
        for clip in clip_paths:
            f.write(f"file '{clip}'\n")
        concat_list = f.name

    try:
        _run_ffmpeg([
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_mp4),
        ])
    finally:
        Path(concat_list).unlink(missing_ok=True)


def assemble_chapter(
    chapter: str,
    project_root: Path,
    slide_paths: list[Path],
    audio_paths: list[Path],
    durations: list[float],
    fps: int = 30,
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
) -> AssembleResult:
    """Assemble per-slide clips and concatenate into final video."""
    build_dir = project_root / "build" / chapter
    clips_dir = build_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths: list[Path] = []
    total_dur = 0.0
    total = len(slide_paths)

    for i, (slide, audio, dur) in enumerate(zip(slide_paths, audio_paths, durations)):
        clip_path = clips_dir / f"clip_{i + 1:03d}.mp4"
        print(f"[PROGRESS] Encoding clip {i + 1}/{total}...")
        clip_dur = build_slide_clip(
            slide, audio, clip_path,
            duration=dur,
            pad_before_s=pad_before_s,
            pad_after_s=pad_after_s,
            min_slide_s=min_slide_s,
            fps=fps,
        )
        clip_paths.append(clip_path)
        total_dur += clip_dur

    print(f"[PROGRESS] Concatenating {total} clips into final video...")
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    output_mp4 = dist_dir / f"{chapter}.mp4"

    concat_clips(clip_paths, output_mp4)

    return AssembleResult(
        video_path=output_mp4,
        slide_count=len(clip_paths),
        total_duration=total_dur,
    )
