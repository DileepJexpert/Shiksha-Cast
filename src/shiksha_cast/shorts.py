"""Generate vertical (9:16) YouTube Shorts from a rendered episode video.

Takes a window of dist/<ep>.mp4, reframes it onto a 1080x1920 canvas with a
blurred fill background, burns in big captions (re-timed from dist/<ep>.srt),
and adds a hook text strip at the top. Output: dist/shorts/<ep>_short<N>.mp4.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from shiksha_cast.assemble import _run_ffmpeg, probe_duration
from shiksha_cast.config import find_chapter_dir, load_script

W, H = 1080, 1920  # vertical Short
DEFAULT_DURATION = 45.0

_TIME = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def _parse_time(s: str) -> float:
    h, m, sec, ms = _TIME.match(s).groups()
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def _fmt_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(text: str) -> list[tuple[float, float, str]]:
    """Parse an SRT into (start_s, end_s, text) cues."""
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        tl = next((ln for ln in lines if "-->" in ln), None)
        if not tl:
            continue
        a, b = tl.split("-->")
        start, end = _parse_time(a.strip()), _parse_time(b.strip())
        body = " ".join(lines[lines.index(tl) + 1:]).strip()
        if body:
            cues.append((start, end, body))
    return cues


def shifted_srt(cues: list[tuple[float, float, str]], start: float, end: float) -> str:
    """Keep cues overlapping [start, end], shift to a 0-based window timeline."""
    out, i = [], 1
    for cs, ce, body in cues:
        if ce <= start or cs >= end:
            continue
        ns = max(0.0, cs - start)
        ne = min(end - start, ce - start)
        out += [str(i), f"{_fmt_time(ns)} --> {_fmt_time(ne)}", body, ""]
        i += 1
    return "\n".join(out)


def _sanitize_hook(text: str) -> str:
    """Drop emoji / non-BMP glyphs the heading font can't render (avoids tofu boxes)."""
    return "".join(c for c in text if ord(c) < 0x2190 or 0x900 <= ord(c) <= 0x97F).strip()


def build_short(
    chapter: str,
    project_root: Path,
    start_s: float = 0.0,
    duration_s: float = DEFAULT_DURATION,
    hook_text: str | None = None,
    index: int = 1,
) -> Path:
    chapter_dir = find_chapter_dir(project_root, chapter)
    ep = chapter_dir.name
    video = project_root / "dist" / f"{ep}.mp4"
    if not video.exists():
        raise FileNotFoundError(f"No video to clip from: {video}. Build the episode first.")

    total = probe_duration(video) or (start_s + duration_s)
    start_s = max(0.0, min(start_s, max(0.0, total - 5)))
    duration_s = min(duration_s, total - start_s)
    end_s = start_s + duration_s

    if hook_text is None:
        from shiksha_cast.thumbnail import _clean_title  # reuse the prefix stripper
        hook_text = _clean_title(load_script(chapter_dir).chapter)

    shorts_dir = project_root / "dist" / "shorts"
    shorts_dir.mkdir(parents=True, exist_ok=True)
    out = shorts_dir / f"{ep}_short{index}.mp4"

    srt = project_root / "dist" / f"{ep}.srt"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # We run ffmpeg with cwd=tdp and reference the subtitle/hook files by their
        # bare names. Relative paths sidestep the libass Windows drive-colon escaping
        # bug that silently drops burned-in captions.
        sub_filter = ""
        if srt.exists():
            (tdp / "short.srt").write_text(
                shifted_srt(parse_srt(srt.read_text(encoding="utf-8")), start_s, end_s),
                encoding="utf-8",
            )
            # NOTE: libass measures Fontsize/MarginV in a virtual ~288px-tall space,
            # not pixels — keep MarginV small or captions land off-screen.
            style = ("Alignment=2,Bold=1,Fontsize=15,PrimaryColour=&H00FFFFFF,"
                     "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=70")
            sub_filter = f",subtitles=short.srt:force_style='{style}'"

        (tdp / "hook.txt").write_text(_sanitize_hook(hook_text)[:80], encoding="utf-8")
        # fontfile still needs the escaped absolute path (drawtext handles it fine).
        hookfont = "C\\:/Windows/Fonts/seguibl.ttf"
        drawhook = (
            f"drawtext=fontfile='{hookfont}':textfile=hook.txt"
            ":fontsize=58:fontcolor=white:box=1:boxcolor=0x000000AA:boxborderw=22"
            ":line_spacing=8:x=(w-text_w)/2:y=150"
        )

        vf = (
            "[0:v]split=2[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=26:2,eq=brightness=-0.12[bgb];"
            "[fg]scale=1080:-2[fgs];"
            "[bgb][fgs]overlay=(W-w)/2:(H-h)/2[base];"
            f"[base]{drawhook}{sub_filter}[v]"
        )

        _run_ffmpeg([
            "-ss", f"{start_s:.3f}", "-t", f"{duration_s:.3f}", "-i", str(video),
            "-filter_complex", vf,
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration_s:.3f}", "-movflags", "+faststart",
            str(out),
        ], cwd=str(tdp))
    return out
