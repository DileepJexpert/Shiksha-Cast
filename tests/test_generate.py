import json

import pytest
import yaml

from shiksha_cast import generate
from shiksha_cast.config import GeneratorConfig, ScriptFile
from shiksha_cast.generate import (
    GeneratorUnavailable,
    _parse_script_json,
    slugify,
    write_episode,
)

CANNED = json.dumps({
    "chapter": "RO Water Purifier — Worth It?",
    "slides": [
        {"n": 1, "narration": "Welcome! Aaj hum RO water purifier review karenge.", "visual_prompt": "cartoon RO purifier on a kitchen wall"},
        {"n": 2, "narration": "RO means reverse osmosis, a membrane that filters water.", "visual_prompt": "diagram of RO membrane filtering water"},
    ],
})


def test_slugify():
    assert slugify("RO water purifier review!") == "ro-water-purifier-review"
    assert slugify("  Hello   World  ") == "hello-world"
    assert slugify("###") == "episode"


def test_parse_script_json_plain():
    d = _parse_script_json(CANNED)
    assert d["chapter"].startswith("RO Water")
    assert len(d["slides"]) == 2
    assert d["slides"][0]["n"] == 1


def test_parse_script_json_with_fences_and_prose():
    wrapped = "Here is your script:\n```json\n" + CANNED + "\n```\nThanks!"
    d = _parse_script_json(wrapped)
    assert len(d["slides"]) == 2


def test_parse_script_json_fills_missing_n():
    raw = json.dumps({"chapter": "X", "slides": [{"narration": "a"}, {"narration": "b"}]})
    d = _parse_script_json(raw)
    assert [s["n"] for s in d["slides"]] == [1, 2]


def test_parse_script_json_rejects_empty():
    with pytest.raises(GeneratorUnavailable):
        _parse_script_json(json.dumps({"chapter": "X", "slides": []}))


def test_write_episode_writes_valid_script(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "ollama_available", lambda url: True)
    monkeypatch.setattr(generate, "_ollama_generate", lambda url, model, prompt, **k: CANNED)

    cfg = GeneratorConfig()
    ep_dir, data = write_episode("RO water purifier review", tmp_path, cfg, category="general-knowledge")

    assert ep_dir == tmp_path / "content" / "general-knowledge" / "ro-water-purifier-review"
    script_path = ep_dir / "script.yaml"
    assert script_path.exists()
    # round-trips through the real loader/schema
    loaded = yaml.safe_load(script_path.read_text(encoding="utf-8"))
    ScriptFile.model_validate(loaded)
    assert len(loaded["slides"]) == 2


def test_write_episode_unique_dir_on_collision(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "ollama_available", lambda url: True)
    monkeypatch.setattr(generate, "_ollama_generate", lambda url, model, prompt, **k: CANNED)
    cfg = GeneratorConfig()
    d1, _ = write_episode("RO review", tmp_path, cfg)
    d2, _ = write_episode("RO review", tmp_path, cfg)
    assert d1 != d2
    assert d2.name.endswith("-2")


def test_generate_script_dict_raises_when_ollama_down(monkeypatch):
    monkeypatch.setattr(generate, "ollama_available", lambda url: False)
    with pytest.raises(GeneratorUnavailable):
        generate.generate_script_dict("anything", GeneratorConfig())
