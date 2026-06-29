from pathlib import Path

from shiksha_cast.config import (
    ChannelConfig,
    SlideScript,
    VoiceConfig,
    find_chapter_dir,
    load_channel_config,
    load_script,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_channel_config_defaults():
    cfg = ChannelConfig()
    assert cfg.resolution == (1920, 1080)
    assert cfg.fps == 30
    assert cfg.voice.provider == "parler"


def test_load_channel_config():
    cfg = load_channel_config(PROJECT_ROOT)
    assert cfg.channel == "Katixo KhojLab"
    assert cfg.resolution == (1920, 1080)
    assert cfg.timing.pad_before_ms == 300


def test_load_script():
    script = load_script(PROJECT_ROOT / "content" / "_archive" / "ch03")
    assert script.chapter == "Ch 3 — Double Century"
    assert len(script.slides) == 3
    assert script.slides[0].n == 1


def test_find_chapter_dir_resolves_nested_episode():
    # Episodes live in category subfolders, e.g.
    # content/how-it-works/technology/s02-wifi — find them by name alone.
    d = find_chapter_dir(PROJECT_ROOT, "s02-wifi")
    assert d.name == "s02-wifi"
    assert (d / "script.yaml").exists()
    assert d.parent.name == "technology"


def test_slide_script_optional_fields():
    s = SlideScript(n=1, narration="hello")
    assert s.voice_description is None
    assert s.min_slide_s is None


def test_voice_config_from_dict():
    v = VoiceConfig.model_validate({"provider": "google_cloud", "sample_rate": 22050})
    assert v.provider == "google_cloud"
    assert v.sample_rate == 22050
