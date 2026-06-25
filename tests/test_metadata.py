from pathlib import Path

from shiksha_cast.captions import generate_srt
from shiksha_cast.metadata import (
    Chapter,
    _clean_title,
    _fmt_ts,
    _short_label,
    build_metadata,
    build_title_variants,
    validate_chapters,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_title_variants_three_angles_within_limit():
    v = build_title_variants("S05 — Why Is the Sky Blue?", "Why Is the Sky Blue?")
    assert set(v) == {"searchable", "curiosity", "hinglish"}
    assert all(len(x) <= 100 for x in v.values())
    assert "Surprise" in v["curiosity"]  # question -> curiosity hook


def test_validate_chapters_rules():
    # good: 3 chapters, 0:00 start, >=10s apart
    good = [Chapter(0, "A"), Chapter(15, "B"), Chapter(40, "C")]
    assert validate_chapters(good) == []
    # bad: too few, not starting at 0, too close
    bad = [Chapter(3, "A"), Chapter(8, "B")]
    problems = validate_chapters(bad)
    assert any("at least 3" in p for p in problems)
    assert any("0:00" in p for p in problems)
    assert any(">= 10s" in p for p in problems)


def test_clean_title_strips_internal_prefix():
    assert _clean_title("S06 — Yawning Kyun Hota Hai?") == "Yawning Kyun Hota Hai?"
    assert _clean_title("Ch 3 - Double Century") == "Double Century"
    assert _clean_title("Why Is the Sky Blue?") == "Why Is the Sky Blue?"


def test_fmt_ts():
    assert _fmt_ts(0) == "0:00"
    assert _fmt_ts(65) == "1:05"
    assert _fmt_ts(3725) == "1:02:05"


def test_short_label_trims_and_caps():
    label = _short_label("This is a very long overlay sentence. Second part here.")
    assert "Second part" not in label  # only first sentence
    assert len(label) <= 48


def test_build_metadata_for_real_episode():
    m = build_metadata("s06-yawning", PROJECT_ROOT)
    assert m.chapter_id == "s06-yawning"
    assert m.title.endswith("| Katixo Shiksha")
    assert "Katixo" not in _clean_title(m.title.replace(" | Katixo Shiksha", ""))
    assert len(m.title) <= 100  # YouTube hard limit
    assert len(m.chapters) >= 3  # enough for YouTube chapter markers
    # first chapter must start at 0:00
    assert m.chapters[0].start_s == 0.0
    # chapters strictly increase
    starts = [c.start_s for c in m.chapters]
    assert starts == sorted(starts)
    assert "Human Body" in m.description  # category playlist surfaced
    assert "yawning" in m.tags


def test_generate_srt_start_offset_shifts_first_cue():
    base = generate_srt(["Hello world."], [2.0], start_offset_s=0.0)
    shifted = generate_srt(["Hello world."], [2.0], start_offset_s=3.0)
    # first cue timestamp line is the 2nd line of the SRT block;
    # base starts at the pad (~0.3s), shifted at offset + pad (~3.3s)
    assert base.splitlines()[1].startswith("00:00:00,")
    assert shifted.splitlines()[1].startswith("00:00:03,")
