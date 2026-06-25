from shiksha_cast.shorts import _sanitize_hook, parse_srt, shifted_srt

SRT = """1
00:00:00,300 --> 00:00:02,000
Hello there

2
00:00:05,000 --> 00:00:09,000
Second line here

3
00:00:40,000 --> 00:00:44,000
Way past the window
"""


def test_parse_srt():
    cues = parse_srt(SRT)
    assert len(cues) == 3
    assert cues[0] == (0.3, 2.0, "Hello there")
    assert cues[1][2] == "Second line here"


def test_shifted_srt_filters_and_reztimes_window():
    cues = parse_srt(SRT)
    out = shifted_srt(cues, start=4.0, end=30.0)
    # only cue 2 overlaps [4,30]; it shifts back by 4s (5.0->1.0, 9.0->5.0)
    assert "Second line here" in out
    assert "Hello there" not in out
    assert "Way past the window" not in out
    assert "00:00:01,000 --> 00:00:05,000" in out


def test_sanitize_hook_strips_emoji_keeps_devanagari():
    assert _sanitize_hook("RO Water: Worth It? 🤔") == "RO Water: Worth It?"
    # Emoji dropped; Devanagari (U+0900-097F) and ASCII kept.
    cleaned = _sanitize_hook("पानी 💧 साफ")
    assert "💧" not in cleaned
    assert "पानी" in cleaned and "साफ" in cleaned
