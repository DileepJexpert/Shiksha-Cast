"""Generate YouTube publishing metadata for an episode.

Produces a copy-paste-ready title, description (with auto chapter timestamps),
and tags from the episode's script.yaml + SLIDES.md. No TTS required: slide
durations are estimated from narration length using the same timeline logic the
captions/assembler use, so timestamps line up closely with the rendered video.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from shiksha_cast.config import (
    ChannelConfig,
    find_chapter_dir,
    load_channel_config,
    load_script,
)

# Words spoken per second (Hinglish, Veena TTS) — used only to *estimate*
# per-slide length for chapter timestamps when audio hasn't been rendered yet.
WORDS_PER_SEC = 2.6
MIN_CHAPTER_S = 11.0  # YouTube requires chapters >= 10s apart; keep a margin.

CATEGORY_PLAYLIST = {
    "how-it-works": "How It Works",
    "human-body": "Human Body & Brain",
    "space": "Space & Universe",
    "technology": "Technology & Gadgets",
    "physics": "Physics Explained",
    "chemistry": "Everyday Chemistry",
    "earth-nature": "Earth & Nature",
    "class-chapter": "Class-wise Lessons",
    "general-knowledge": "General Knowledge",
}

BASE_TAGS = [
    "Katixo KhojLab",
    "science for kids",
    "hinglish science",
    "class 6 to 10",
    "ncert science",
    "science explained",
    "educational",
    "why and how",
    "indian education",
    "study with fun",
]


@dataclass
class Chapter:
    start_s: float
    label: str


@dataclass
class EpisodeMetadata:
    chapter_id: str
    title: str
    description: str
    tags: list[str]
    chapters: list[Chapter] = field(default_factory=list)
    title_variants: dict = field(default_factory=dict)
    pinned_comment: str = ""
    chapter_warnings: list[str] = field(default_factory=list)


def build_title_variants(raw_title: str, clean: str) -> dict:
    """Three title angles for A/B testing: searchable, curiosity, hinglish."""
    base = clean.rstrip("?！.। ").strip()
    has_q = clean.rstrip().endswith("?")

    searchable = f"{base} — Simple Science Explained (Class 6–10)"
    curiosity = (
        f"{base}? The Answer Will Surprise You 🤯" if has_q
        else f"The Real Truth About {base} 🤯"
    )
    # Many episode titles are already Hinglish; keep that. Otherwise add a hook.
    looks_hinglish = bool(re.search(r"[ऀ-ॿ]", raw_title)) or raw_title.strip() != clean
    hinglish = _clean_title(raw_title) if looks_hinglish else f"{base} — Hindi Mein Samjho!"

    def _cap(s: str) -> str:
        return s if len(s) <= 100 else s[:99]

    return {
        "searchable": _cap(searchable),
        "curiosity": _cap(curiosity),
        "hinglish": _cap(hinglish),
    }


def build_pinned_comment(clean: str, playlist: str) -> str:
    """A pinned-comment with an engagement question + CTA."""
    q = clean.rstrip("?").strip()
    return (
        f"🤔 Quick question: {q}? — comment your answer below! 👇\n\n"
        f"📚 More like this in our '{playlist}' playlist.\n"
        "🔔 Subscribe + hit the bell for a new 'why & how' every week!"
    )


def validate_chapters(chapters: list[Chapter]) -> list[str]:
    """Check YouTube's chapter rules; return a list of human-readable problems.

    Rules: first chapter at 0:00, at least 3 chapters, each >= 10s after the
    previous. https://support.google.com/youtube/answer/9884579
    """
    problems: list[str] = []
    if len(chapters) < 3:
        problems.append(f"Only {len(chapters)} chapters — YouTube needs at least 3.")
    if chapters and chapters[0].start_s != 0.0:
        problems.append(f"First chapter starts at {chapters[0].start_s:.0f}s, must be 0:00.")
    for a, b in zip(chapters, chapters[1:]):
        if b.start_s - a.start_s < 10.0:
            problems.append(
                f"Chapters '{a.label}' and '{b.label}' are "
                f"{b.start_s - a.start_s:.0f}s apart — must be >= 10s."
            )
    return problems


def _clean_title(raw: str) -> str:
    """Strip the internal 'S06 —'/'Ch 3 -' prefix and tidy whitespace."""
    t = re.sub(r"^\s*(?:s|ch)\s*\d+\s*[—\-:.]\s*", "", raw, flags=re.IGNORECASE)
    return t.strip() or raw.strip()


def _parse_overlays(slides_md: Path) -> list[str]:
    """Per-slide short overlay text from SLIDES.md ('## Slide N' sections)."""
    if not slides_md.exists():
        return []
    txt = slides_md.read_text(encoding="utf-8")
    out = []
    for sec in re.split(r"\n##\s+Slide\s+\d+", txt)[1:]:
        m = re.search(r"Text overlay:\*\*\s*[\"“]([^\"”]+)[\"”]", sec)
        out.append(m.group(1).strip() if m else "")
    return out


def _short_label(text: str, max_words: int = 6) -> str:
    """A concise chapter label from overlay or narration text."""
    text = re.split(r"[।.!?]", text.strip())[0]
    text = text.split("|")[0].strip()
    words = text.split()
    label = " ".join(words[:max_words])
    return label[:48].strip(" ,—-")


def _fmt_ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def _estimate_slide_duration(narration: str, cfg: ChannelConfig) -> float:
    words = len(narration.split())
    audio = words / WORDS_PER_SEC
    return max(
        cfg.timing.min_slide_s,
        cfg.timing.pad_before_ms / 1000 + audio + cfg.timing.pad_after_ms / 1000,
    )


def _build_chapters(slides, overlays, cfg: ChannelConfig) -> list[Chapter]:
    """Group slides into YouTube chapters, each >= MIN_CHAPTER_S long."""
    chapters: list[Chapter] = []
    timeline = 0.0
    group_start = 0.0
    group_label = ""
    group_len = 0.0
    for i, slide in enumerate(slides):
        if not group_label:
            label_src = overlays[i] if i < len(overlays) and overlays[i] else slide.narration
            group_label = _short_label(label_src)
            group_start = timeline
        dur = _estimate_slide_duration(slide.narration, cfg)
        timeline += dur
        group_len += dur
        if group_len >= MIN_CHAPTER_S:
            chapters.append(Chapter(group_start, group_label or f"Part {len(chapters) + 1}"))
            group_label, group_len = "", 0.0
    if group_label:  # trailing slides shorter than a chapter -> fold into last
        if chapters:
            pass  # they already belong to the running video; skip a sub-10s tail
        else:
            chapters.append(Chapter(group_start, group_label))
    if chapters:
        chapters[0] = Chapter(0.0, chapters[0].label)  # YouTube requires 0:00 first
    return chapters


def _intro_offset(project_root: Path, cfg: ChannelConfig) -> float:
    """Duration of the configured intro bumper, if it exists (else 0). Best-effort."""
    rel = cfg.branding.intro
    if not rel:
        return 0.0
    p = Path(rel)
    if not p.is_absolute():
        p = project_root / p
    if not p.exists():
        return 0.0
    try:
        from shiksha_cast.assemble import probe_duration
        return probe_duration(p)
    except Exception:
        return 0.0


def build_metadata(chapter: str, project_root: Path) -> EpisodeMetadata:
    cfg = load_channel_config(project_root)
    chapter_dir = find_chapter_dir(project_root, chapter)
    script = load_script(chapter_dir)
    overlays = _parse_overlays(chapter_dir / "SLIDES.md")

    parts = chapter_dir.relative_to(project_root / "content").parts[:-1]
    category_key = parts[-1] if parts else ""
    playlist = CATEGORY_PLAYLIST.get(category_key, "Katixo KhojLab")

    clean = _clean_title(script.chapter)
    title = f"{clean} | Katixo KhojLab"
    if len(title) > 95:  # YouTube hard limit is 100 chars
        title = clean[:95]

    chapters = _build_chapters(script.slides, overlays, cfg)

    # If an intro bumper is configured, content shifts later; label 0:00 "Intro".
    intro_offset = _intro_offset(project_root, cfg)
    if intro_offset > 0 and chapters:
        chapters = [Chapter(c.start_s + intro_offset, c.label) for c in chapters]
        chapters.insert(0, Chapter(0.0, "Intro"))

    # ---- Description ----
    lines: list[str] = []
    lines.append(f"Ever wondered — {clean.rstrip('?')}? 🤔")
    lines.append("")
    lines.append(
        "In this Katixo KhojLab episode we break it down in simple Hinglish, "
        "with clear visuals, for curious students of Class 6–10. Easy to follow, "
        "fun to watch, and exam-friendly!"
    )
    lines.append("")
    if chapters:
        lines.append("⏱️ Chapters")
        for ch in chapters:
            lines.append(f"{_fmt_ts(ch.start_s)} {ch.label}")
        lines.append("")
    lines.append(f"📚 Playlist: {playlist}")
    lines.append("🎯 Made for Class 6–10 (Age 11–16) | Hinglish science explainers")
    lines.append("")
    lines.append("👉 Subscribe for a new 'why & how' every week!")
    lines.append("🔔 Hit the bell so you never miss an episode.")
    lines.append("")
    lines.append("#KatixoKhojLab #ScienceForKids #Hinglish #Class10 #LearnWithFun")
    description = "\n".join(lines)

    # ---- Tags ----
    topic_words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", clean)]
    seen, tags = set(), []
    for t in [*topic_words, category_key.replace("-", " "), playlist.lower(), *BASE_TAGS]:
        t = t.strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            tags.append(t)
    tags = tags[:25]

    return EpisodeMetadata(
        chapter_id=chapter_dir.name,
        title=title,
        description=description,
        tags=tags,
        chapters=chapters,
        title_variants=build_title_variants(script.chapter, clean),
        pinned_comment=build_pinned_comment(clean, playlist),
        chapter_warnings=validate_chapters(chapters),
    )


def render_metadata_file(meta: EpisodeMetadata) -> str:
    """Format an EpisodeMetadata as a copy-paste-friendly markdown file."""
    out = [
        f"# YouTube metadata — {meta.chapter_id}",
        "",
        "## Title",
        "",
        meta.title,
        "",
        "## Title variants (A/B ideas)",
        "",
        f"- Searchable: {meta.title_variants.get('searchable', '')}",
        f"- Curiosity:  {meta.title_variants.get('curiosity', '')}",
        f"- Hinglish:   {meta.title_variants.get('hinglish', '')}",
        "",
        "## Description",
        "",
        meta.description,
        "",
        "## Tags (comma-separated)",
        "",
        ", ".join(meta.tags),
        "",
        "## Pinned comment",
        "",
        meta.pinned_comment,
        "",
    ]
    if meta.chapter_warnings:
        out += ["## ⚠️ Chapter warnings", ""]
        out += [f"- {w}" for w in meta.chapter_warnings]
        out += [""]
    return "\n".join(out)


def write_metadata(chapter: str, project_root: Path) -> Path:
    meta = build_metadata(chapter, project_root)
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    out_path = dist_dir / f"{meta.chapter_id}.youtube.md"
    out_path.write_text(render_metadata_file(meta), encoding="utf-8")
    return out_path
