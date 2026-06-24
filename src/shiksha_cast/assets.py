"""Generate the channel's branding assets: intro clip, outro clip, music bed.

These fill the paths referenced by config/channel.yaml (branding.intro,
branding.outro, music.bed). They are generated to match the per-slide clip
encoding (1920x1080, libx264/yuv420p, 30fps, AAC mono @ the channel sample
rate) so they concatenate cleanly with the narrated slides.

The music bed is a simple synthesized placeholder — swap assets/music/
gentle_learning.mp3 for a licensed track whenever you like.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import ImageDraw

from shiksha_cast.assemble import _run_ffmpeg
from shiksha_cast.branding import (
    ACCENTS,
    CHANNEL_NAME,
    SUB_YELLOW,
    TEXT_LIGHT,
    TEXT_MUTED,
    font,
    new_canvas,
)
from shiksha_cast.config import load_channel_config

W, H = 1920, 1080
INTRO_S = 3.0
OUTRO_S = 4.5
MUSIC_S = 60.0


def _center_text(d: ImageDraw.ImageDraw, text: str, fnt, y: float, fill) -> None:
    d.text(((W - d.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)


def _render_intro_card(path: Path) -> None:
    img, d = new_canvas(W, H)
    accent = ACCENTS[0]
    d.rectangle([(W - 520) / 2, 372, (W + 520) / 2, 380], fill=accent)
    _center_text(d, CHANNEL_NAME, font("seguibl.ttf", 130), 410, TEXT_LIGHT)
    _center_text(d, "Curiosity-driven science • Hinglish", font("segoeui.ttf", 50), 580, SUB_YELLOW)
    d.rectangle([(W - 520) / 2, 700, (W + 520) / 2, 708], fill=accent)
    img.save(path)


def _render_outro_card(path: Path) -> None:
    img, d = new_canvas(W, H)
    accent = ACCENTS[2]
    _center_text(d, "Thanks for watching!", font("seguibl.ttf", 110), 300, TEXT_LIGHT)
    _center_text(d, "👍  LIKE    🔔  SUBSCRIBE    💬  COMMENT", font("segoeuib.ttf", 56), 500, accent)
    _center_text(d, "New episode every week", font("segoeui.ttf", 48), 620, TEXT_MUTED)
    _center_text(d, CHANNEL_NAME, font("segoeuib.ttf", 44), 760, SUB_YELLOW)
    img.save(path)


def _image_to_clip(card_png: Path, out_mp4: Path, duration: float, sample_rate: int, freq: int) -> None:
    """Encode a still card + a soft chime into a clip matching slide-clip params."""
    _run_ffmpeg([
        "-loop", "1",
        "-i", str(card_png),
        "-f", "lavfi",
        "-i", f"sine=frequency={freq}:duration={duration}",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", str(sample_rate),
        "-ac", "1",
        "-af", f"volume=0.18,afade=t=in:st=0:d=0.4,afade=t=out:st={duration - 0.6:.2f}:d=0.6",
        "-t", f"{duration:.3f}",
        str(out_mp4),
    ])


def _make_music_bed(out_mp3: Path, duration: float) -> None:
    """Synthesize a soft, loopable ambient pad as a placeholder bed."""
    _run_ffmpeg([
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=329.63:duration={duration}",
        "-filter_complex",
        "[0][1]amix=inputs=2,tremolo=f=0.18:d=0.5,lowpass=f=1100,"
        "aecho=0.8:0.7:80:0.3,volume=0.6,"
        f"afade=t=in:st=0:d=2,afade=t=out:st={duration - 3:.2f}:d=3[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame", "-q:a", "4",
        str(out_mp3),
    ])


def generate_branding_assets(project_root: Path, force: bool = False) -> list[tuple[str, Path]]:
    cfg = load_channel_config(project_root)
    sr = cfg.voice.sample_rate or 24000

    assets = project_root / "assets"
    music_dir = assets / "music"
    assets.mkdir(parents=True, exist_ok=True)
    music_dir.mkdir(parents=True, exist_ok=True)

    intro = assets / "intro.mp4"
    outro = assets / "outro.mp4"
    music = music_dir / "gentle_learning.mp3"

    created: list[tuple[str, Path]] = []
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        if force or not intro.exists():
            card = tdp / "intro_card.png"
            _render_intro_card(card)
            _image_to_clip(card, intro, INTRO_S, sr, freq=528)
            created.append(("intro", intro))
        if force or not outro.exists():
            card = tdp / "outro_card.png"
            _render_outro_card(card)
            _image_to_clip(card, outro, OUTRO_S, sr, freq=440)
            created.append(("outro", outro))
        if force or not music.exists():
            _make_music_bed(music, MUSIC_S)
            created.append(("music bed", music))

    return created
