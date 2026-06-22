from shiksha_cast.captions import generate_srt


def test_srt_basic():
    srt = generate_srt(
        narrations=["Hello children.", "Let us count."],
        durations=[2.0, 1.5],
    )
    assert "00:00:00,300" in srt
    assert "Hello children." in srt
    assert "Let us count." in srt


def test_srt_sentence_split():
    srt = generate_srt(
        narrations=["First sentence. Second sentence."],
        durations=[4.0],
    )
    assert "First sentence." in srt
    assert "Second sentence." in srt
    lines = srt.strip().split("\n")
    cue_count = sum(1 for l in lines if l.strip().isdigit())
    assert cue_count == 2


def test_srt_hindi_split():
    srt = generate_srt(
        narrations=["नमस्ते बच्चों। आज हम सीखेंगे।"],
        durations=[4.0],
    )
    assert "नमस्ते बच्चों।" in srt
    assert "आज हम सीखेंगे।" in srt
