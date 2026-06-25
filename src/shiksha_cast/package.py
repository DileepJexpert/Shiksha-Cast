"""Assemble a ready-to-upload package folder for an episode.

dist/packages/<ep>/
    video.mp4
    captions.srt
    thumbnail.png            (+ thumbnails/<style>.png variants)
    title.txt                (chosen title)
    titles.txt               (A/B variants)
    description.txt
    tags.txt
    pinned-comment.txt
    short1.mp4               (optional vertical Short)
    README.txt               (chapter-rule warnings, upload checklist)

Everything is derived from already-generated assets + metadata, so this just
collects them into one folder you can hand to an uploader (manual or automated).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from shiksha_cast.config import find_chapter_dir
from shiksha_cast.metadata import build_metadata
from shiksha_cast.thumbnail import write_thumbnail_variants


def build_package(
    chapter: str,
    project_root: Path,
    include_short: bool = True,
    short_duration: float = 45.0,
) -> Path:
    chapter_dir = find_chapter_dir(project_root, chapter)
    ep = chapter_dir.name
    dist = project_root / "dist"
    pkg = dist / "packages" / ep
    (pkg / "thumbnails").mkdir(parents=True, exist_ok=True)

    meta = build_metadata(chapter, project_root)

    # --- text assets ---
    (pkg / "title.txt").write_text(meta.title, encoding="utf-8")
    (pkg / "titles.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in meta.title_variants.items()), encoding="utf-8"
    )
    (pkg / "description.txt").write_text(meta.description, encoding="utf-8")
    (pkg / "tags.txt").write_text(", ".join(meta.tags), encoding="utf-8")
    (pkg / "pinned-comment.txt").write_text(meta.pinned_comment, encoding="utf-8")

    # --- media assets (copy what exists) ---
    notes: list[str] = []
    video = dist / f"{ep}.mp4"
    if video.exists():
        shutil.copy2(video, pkg / "video.mp4")
    else:
        notes.append("video.mp4 MISSING — build the episode first (ai-build / build).")

    srt = dist / f"{ep}.srt"
    if srt.exists():
        shutil.copy2(srt, pkg / "captions.srt")
    else:
        notes.append("captions.srt missing.")

    # thumbnail variants (also (re)writes the canonical dist/<ep>.thumb.png)
    for v in write_thumbnail_variants(chapter, project_root):
        shutil.copy2(v, pkg / "thumbnails" / v.name.replace(f"{ep}.thumb.", ""))
    default_thumb = dist / f"{ep}.thumb.png"
    if default_thumb.exists():
        shutil.copy2(default_thumb, pkg / "thumbnail.png")

    # optional Short (needs the rendered video)
    if include_short and video.exists():
        from shiksha_cast.shorts import build_short
        short = build_short(chapter, project_root, start_s=0.0, duration_s=short_duration, index=1)
        shutil.copy2(short, pkg / "short1.mp4")
    elif include_short:
        notes.append("short1.mp4 skipped — no video to clip from.")

    # --- README / checklist ---
    readme = [
        f"UPLOAD PACKAGE — {ep}",
        "=" * (16 + len(ep)),
        "",
        f"Title:   {meta.title}",
        f"Chapters: {len(meta.chapters)}",
        "",
        "Files:",
        "  video.mp4            -> upload as the main video",
        "  thumbnail.png        -> set as custom thumbnail (thumbnails/ has 4 styles)",
        "  captions.srt         -> upload as subtitles (English/Hinglish)",
        "  title.txt            -> video title (see titles.txt for A/B options)",
        "  description.txt      -> video description (includes chapters)",
        "  tags.txt             -> tags",
        "  pinned-comment.txt   -> post & pin after upload",
        "  short1.mp4           -> upload as a separate YouTube Short",
        "",
    ]
    if meta.chapter_warnings:
        readme += ["CHAPTER WARNINGS (YouTube rules):"]
        readme += [f"  - {w}" for w in meta.chapter_warnings] + [""]
    if notes:
        readme += ["NOTES:"] + [f"  - {n}" for n in notes] + [""]
    (pkg / "README.txt").write_text("\n".join(readme), encoding="utf-8")

    return pkg
