from shiksha_cast.cartoon import rhubarb

CUES = [(0.0, 0.10, "X"), (0.10, 0.22, "B"), (0.22, 0.40, "D"),
        (0.40, 0.55, "F"), (0.55, 0.70, "A")]


def test_viseme_at_picks_active_cue():
    assert [rhubarb.viseme_at(CUES, t) for t in (0.05, 0.15, 0.30, 0.50, 0.60)] == \
        ["X", "B", "D", "F", "A"]


def test_viseme_at_past_end_is_rest():
    assert rhubarb.viseme_at(CUES, 5.0) == "X"
    assert rhubarb.viseme_at([], 0.1) == "X"


def test_simple_at_collapses_to_three_shapes():
    assert [rhubarb.simple_at(CUES, t) for t in (0.05, 0.15, 0.30, 0.50, 0.60)] == \
        ["closed", "half", "open", "open", "closed"]


def test_disabled_via_env(monkeypatch):
    monkeypatch.setenv("SHIKSHA_RHUBARB", "0")
    assert rhubarb.rhubarb_binary() is None
    assert rhubarb.available() is False


def test_missing_binary_returns_empty(monkeypatch, tmp_path):
    # point at a path that doesn't exist -> treated as unavailable, no crash
    monkeypatch.setenv("SHIKSHA_RHUBARB", str(tmp_path / "nope"))
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"RIFF")  # content irrelevant; binary is missing
    assert rhubarb.visemes_for_wav(wav) == []


def test_valid_shapes_are_the_kinnu_set():
    # rhubarb output letters must match the mouth_* parts the rig draws
    assert rhubarb._VALID == {"A", "B", "C", "D", "E", "F", "G", "H", "X"}
    for shape in rhubarb._VALID:
        assert rhubarb._TO_SIMPLE[shape] in {"closed", "half", "open"}
