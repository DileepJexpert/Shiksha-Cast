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


def _run_ffmpeg(args: list[str], cwd: str | None = None) -> None:
    _ensure_ffmpeg()
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FFmpeg failed (exit {e.returncode}):\n{e.stderr}"
        ) from e


def probe_duration(path: Path) -> float:
    """Return a media file's duration in seconds (0.0 if it can't be probed)."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None or not Path(path).exists():
        return 0.0
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            check=True, capture_output=True, text=True,
        )
        return float(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0


def mix_music_bed(video_in: Path, music: Path, output_mp4: Path, music_db: float, sample_rate: int) -> None:
    """Loop a music bed under the video's narration at music_db (e.g. -18) and remux."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg([
        "-i", str(video_in),
        "-stream_loop", "-1", "-i", str(music),
        "-filter_complex",
        f"[1:a]volume={music_db}dB[m];"
        f"[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[mix];"
        f"[mix]loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-ac", "1",
        "-shortest", "-movflags", "+faststart",
        str(output_mp4),
    ])


def normalize_loudness(video_in: Path, output_mp4: Path, sample_rate: int) -> None:
    """Master the final audio to the YouTube target (-14 LUFS) so videos are punchy
    and consistent. Used when there is no music bed (the music path normalizes inline)."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg([
        "-i", str(video_in),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-ac", "1",
        "-movflags", "+faststart",
        str(output_mp4),
    ])


def build_slide_motion_clip(
    slide_png: Path,
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
    """Gentle, slide-SAFE Ken Burns: a slow CENTERED zoom (in or out) that keeps the
    logo, title and 'Slide N' badge fully on-screen (low zoom, no pan). We pre-upscale
    so zoompan stays smooth and crisp instead of jittering on a single image."""
    clip_dur = max(min_slide_s, pad_before_s + duration + pad_after_s)
    frames = int(clip_dur * fps)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if effect_index % 2 == 0:
        z = "min(zoom+0.0005,1.07)"                      # slow zoom IN
    else:
        z = "if(lte(zoom,1.0),1.07,max(1.0,zoom-0.0005))"  # slow zoom OUT
    vf = (
        f"scale={width * 2}:{height * 2},"
        f"zoompan=z='{z}':x='{cx}':y='{cy}':d={frames}:s={width}x{height}:fps={fps},"
        f"format=yuv420p"
    )

    _run_ffmpeg([
        "-i", str(slide_png),
        "-i", str(audio_wav),
        "-vf", vf,
        "-c:v", "libx264",
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


def mux_audio_onto_video(
    video_in: Path,
    audio_wav: Path,
    output_mp4: Path,
    clip_dur: float,
    pad_before_s: float = 0.3,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    sample_rate: int = 24000,
) -> None:
    """Mux narration audio onto a pre-rendered (silent) clip, normalizing the
    video to the standard clip params so it concatenates with slide clips."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    delay_ms = int(pad_before_s * 1000)
    # Loop the (silent) video and pad the audio so neither stream ends early;
    # -t trims both to exactly clip_dur. This tolerates DepthFlow rendering a
    # hair short without cutting the narration.
    _run_ffmpeg([
        "-stream_loop", "-1", "-i", str(video_in),
        "-i", str(audio_wav),
        "-filter_complex",
        f"[0:v]scale={width}:{height},fps={fps},format=yuv420p[v];"
        f"[1:a]adelay={delay_ms}|{delay_ms},apad[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-ac", "1",
        "-t", f"{clip_dur:.3f}",
        str(output_mp4),
    ])


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
    intro_path: Path | None = None,
    outro_path: Path | None = None,
    music_path: Path | None = None,
    music_db: float = -18.0,
    sample_rate: int = 24000,
    motion: str = "kenburns",
) -> AssembleResult:
    """Assemble per-slide clips, optional intro/outro bumpers and music bed.

    intro/outro/music are applied only when the given paths exist, so builds
    behave exactly as before when no branding assets are present.
    """
    build_dir = project_root / "build" / chapter
    clips_dir = build_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths: list[Path] = []
    total_dur = 0.0
    total = len(slide_paths)

    use_motion = (motion or "").lower() in ("kenburns", "zoom", "motion", "kb")
    for i, (slide, audio, dur) in enumerate(zip(slide_paths, audio_paths, durations)):
        clip_path = clips_dir / f"clip_{i + 1:03d}.mp4"
        print(f"[PROGRESS] Encoding clip {i + 1}/{total}...")
        if use_motion:
            clip_dur = build_slide_motion_clip(
                slide, audio, clip_path,
                duration=dur,
                effect_index=i,
                pad_before_s=pad_before_s,
                pad_after_s=pad_after_s,
                min_slide_s=min_slide_s,
                fps=fps,
            )
        else:
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

    # Wrap with intro/outro bumpers when available.
    sequence = list(clip_paths)
    if intro_path and Path(intro_path).exists():
        sequence.insert(0, Path(intro_path))
        total_dur += probe_duration(intro_path)
        print("[PROGRESS] Prepending intro bumper")
    if outro_path and Path(outro_path).exists():
        sequence.append(Path(outro_path))
        total_dur += probe_duration(outro_path)
        print("[PROGRESS] Appending outro bumper")

    print(f"[PROGRESS] Concatenating {len(sequence)} clips into final video...")
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    output_mp4 = dist_dir / f"{chapter}.mp4"

    use_music = bool(music_path and Path(music_path).exists())
    concat_target = (build_dir / "body.mp4") if use_music else (build_dir / "body.mp4")
    concat_clips(sequence, concat_target)

    if use_music:
        print("[PROGRESS] Mixing music bed under narration + mastering to -14 LUFS...")
        mix_music_bed(concat_target, Path(music_path), output_mp4, music_db, sample_rate)
    else:
        print("[PROGRESS] Mastering audio to -14 LUFS...")
        normalize_loudness(concat_target, output_mp4, sample_rate)

    return AssembleResult(
        video_path=output_mp4,
        slide_count=len(clip_paths),
        total_duration=total_dur,
    )
