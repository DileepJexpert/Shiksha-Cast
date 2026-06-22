from pathlib import Path

from shiksha_cast.config import ChannelConfig, ScriptFile, SlideScript
from shiksha_cast.speak import speak_chapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _make_script() -> ScriptFile:
    return ScriptFile(
        chapter="test",
        slides=[
            SlideScript(n=1, narration="Hello children, today we learn counting."),
            SlideScript(n=2, narration="One two three four five."),
        ],
    )


def _make_config() -> ChannelConfig:
    return ChannelConfig.model_validate({"voice": {"provider": "stub"}})


def test_speak_produces_wavs(tmp_path: Path):
    (tmp_path / "content" / "test").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    result = speak_chapter("test", tmp_path, _make_script(), _make_config())
    assert len(result.audio_paths) == 2
    assert result.synthesized_count == 2
    for p in result.audio_paths:
        assert p.exists()
        assert p.suffix == ".wav"


def test_speak_cache(tmp_path: Path):
    (tmp_path / "content" / "test").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    script = _make_script()
    cfg = _make_config()
    speak_chapter("test", tmp_path, script, cfg)
    r2 = speak_chapter("test", tmp_path, script, cfg)
    assert r2.cached_count == 2
    assert r2.synthesized_count == 0
