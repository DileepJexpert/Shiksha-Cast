from __future__ import annotations

from pathlib import Path


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _split_sentences(text: str) -> list[str]:
    """Split narration into sentence-level cues."""
    import re
    parts = re.split(r"(?<=[।.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def generate_srt(
    narrations: list[str],
    durations: list[float],
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
) -> str:
    """Generate SRT subtitle content from narration text and audio durations."""
    lines: list[str] = []
    cue_index = 1
    timeline = 0.0

    for narration, audio_dur in zip(narrations, durations):
        slide_dur = max(min_slide_s, pad_before_s + audio_dur + pad_after_s)
        caption_start = timeline + pad_before_s
        caption_end = timeline + pad_before_s + audio_dur

        sentences = _split_sentences(narration)
        if not sentences:
            sentences = [narration]

        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            timeline += slide_dur
            continue

        sent_start = caption_start
        for sent in sentences:
            frac = len(sent) / total_chars
            sent_dur = frac * audio_dur
            sent_end = min(sent_start + sent_dur, caption_end)

            lines.append(str(cue_index))
            lines.append(f"{_format_srt_time(sent_start)} --> {_format_srt_time(sent_end)}")
            lines.append(sent)
            lines.append("")
            cue_index += 1
            sent_start = sent_end

        timeline += slide_dur

    return "\n".join(lines)


def write_captions(
    chapter: str,
    project_root: Path,
    narrations: list[str],
    durations: list[float],
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
) -> Path:
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    srt_path = dist_dir / f"{chapter}.srt"

    content = generate_srt(narrations, durations, pad_before_s, pad_after_s, min_slide_s)
    srt_path.write_text(content, encoding="utf-8")
    return srt_path
