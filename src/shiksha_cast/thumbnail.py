"""Render a 1280x720 YouTube thumbnail for an episode.

Pulls the episode title from script.yaml, picks an accent from its subject
category, and renders a punchy branded thumbnail to dist/<id>.thumb.png.
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw

from shiksha_cast.branding import (
    CHANNEL_NAME,
    SUB_YELLOW,
    TEXT_LIGHT,
    TEXT_MUTED,
    accent_for,
    font,
    new_canvas,
    wrap,
)
from shiksha_cast.config import find_chapter_dir, load_script

W, H = 1280, 720

# Opening word -> big background hook word.
_HOOKS = {
    "why": "WHY?",
    "how": "HOW?",
    "what": "WHAT?",
    "kyun": "KYUN?",
    "kya": "KYA?",
    "kaise": "KAISE?",
}

# Thumbnail styles — each yields a visually distinct option for the same episode.
# accent=None means "use the subject-category accent".
STYLES = {
    "curiosity": {"accent": None, "tagline": "Hinglish Science • Class 6–10", "hook": True},
    "exam": {"accent": (60, 170, 255), "tagline": "Exam-Ready • NCERT Class 6–10", "hook": False},
    "kids": {"accent": (255, 193, 7), "tagline": "Fun Science for Curious Kids! 🎉", "hook": True},
    "hinglish": {"accent": (0, 230, 150), "tagline": "Hindi + English • Aasaan Bhasha Mein", "hook": True},
}


def _clean_title(raw: str) -> str:
    t = re.sub(r"^\s*(?:s|ch)\s*\d+\s*[—\-:.]\s*", "", raw, flags=re.IGNORECASE)
    return t.strip() or raw.strip()


def _hook_word(title: str) -> str | None:
    first = re.findall(r"[A-Za-z]+", title)
    if not first:
        return None
    return _HOOKS.get(first[0].lower())


def build_thumbnail(
    chapter: str,
    project_root: Path,
    style: str = "curiosity",
    title: str | None = None,
) -> Image.Image:
    chapter_dir = find_chapter_dir(project_root, chapter)
    script = load_script(chapter_dir)
    parts = chapter_dir.relative_to(project_root / "content").parts[:-1]
    category_key = parts[-1] if parts else ""

    spec = STYLES.get(style, STYLES["curiosity"])
    accent = spec["accent"] or accent_for(category_key)

    title = title or _clean_title(script.chapter)
    badge = chapter_dir.name.split("-")[0].upper()  # e.g. S06

    img, d = new_canvas(W, H)

    # Giant faded hook word in the background for visual punch (some styles skip it).
    hook = _hook_word(title) if spec["hook"] else None
    if hook:
        hf = font("seguibl.ttf", 360)
        hw = d.textlength(hook, font=hf)
        ghost = Image.new("RGB", (W, H))
        gd = ImageDraw.Draw(ghost)
        gd.text(((W - hw) / 2, H / 2 - 230), hook, font=hf, fill=accent)
        img = Image.blend(img, ghost, 0.12)
        d = ImageDraw.Draw(img)

    # Left accent bar + top channel strip.
    d.rectangle([0, 0, 14, H], fill=accent)
    d.text((54, 40), CHANNEL_NAME, font=font("segoeuib.ttf", 34), fill=accent)
    bf = font("segoeuib.ttf", 34)
    d.text((W - 54 - d.textlength(badge, font=bf), 40), badge, font=bf, fill=TEXT_MUTED)

    # Main title — fit by shrinking until <= 4 lines.
    size = 96
    while size > 52:
        tf = font("seguibl.ttf", size)
        lines = wrap(d, title, tf, W - 150)
        if len(lines) <= 4:
            break
        size -= 8
    tf = font("seguibl.ttf", size)
    lines = wrap(d, title, tf, W - 150)
    line_h = size * 1.16
    block_h = len(lines) * line_h
    y = (H - block_h) / 2 + 20
    for ln in lines:
        # subtle shadow for legibility over the ghost word
        d.text((75 + 3, y + 3), ln, font=tf, fill=(0, 0, 0))
        d.text((75, y), ln, font=tf, fill=TEXT_LIGHT)
        y += line_h

    # Accent underline + bottom tagline.
    d.rectangle([75, y + 10, 75 + 360, y + 20], fill=accent)
    d.text((75, H - 78), spec["tagline"], font=font("segoeui.ttf", 38), fill=SUB_YELLOW)

    return img


def write_thumbnail(chapter: str, project_root: Path) -> Path:
    img = build_thumbnail(chapter, project_root)
    chapter_dir = find_chapter_dir(project_root, chapter)
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    out_path = dist_dir / f"{chapter_dir.name}.thumb.png"
    img.save(out_path)
    return out_path


def write_thumbnail_variants(
    chapter: str, project_root: Path, styles: list[str] | None = None
) -> list[Path]:
    """Render one thumbnail per style -> dist/<id>.thumb.<style>.png.

    Also (re)writes the default dist/<id>.thumb.png as the 'curiosity' style.
    """
    from shiksha_cast.metadata import build_title_variants

    chapter_dir = find_chapter_dir(project_root, chapter)
    script = load_script(chapter_dir)
    clean = _clean_title(script.chapter)
    hinglish_title = build_title_variants(script.chapter, clean).get("hinglish")

    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    ep = chapter_dir.name

    out_paths: list[Path] = []
    for style in (styles or list(STYLES.keys())):
        # The hinglish style shows the Hinglish title text.
        title = hinglish_title if style == "hinglish" else None
        img = build_thumbnail(chapter, project_root, style=style, title=title)
        out = dist_dir / f"{ep}.thumb.{style}.png"
        img.save(out)
        out_paths.append(out)
        if style == "curiosity":  # keep the canonical default name in sync
            img.save(dist_dir / f"{ep}.thumb.png")
    return out_paths
