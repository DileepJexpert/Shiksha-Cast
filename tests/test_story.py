import json

import yaml

from shiksha_cast import story
from shiksha_cast.config import GeneratorConfig, ScriptFile
from shiksha_cast.story import (
    _parse_story_json,
    render_story_from_story,
    script_from_story,
    write_story_episode,
)


CANNED_STORY = json.dumps(
    {
        "chapter": "Kinnu and Gappu Learn Friction",
        "topic": "friction",
        "audience": "kids age 5-10",
        "style": "Hinglish, funny and warm",
        "characters": [
            {
                "id": "kinnu",
                "name": "Kinnu",
                "voice": "kavya",
                "description": "curious girl stickman",
                "rig": "assets/characters/kinnu/rig.json",
            },
            {
                "id": "gappu",
                "name": "Gappu",
                "voice": "agastya",
                "description": "playful boy stickman",
                "rig": "assets/characters/gappu/rig.json",
            },
        ],
        "scenes": [
            {
                "n": 1,
                "title": "Ball Stops",
                "background_prompt": "bright cartoon classroom floor with a rolling ball, no characters",
                "learning_point": "friction slows moving things",
                "characters": {
                    "kinnu": {"x": 0.22, "y": 0.86, "height": 0.62, "pose": "happy", "facing": "right"},
                    "gappu": {"x": 0.74, "y": 0.86, "height": 0.62, "pose": "confused", "facing": "left"},
                },
                "dialogue": [
                    {"speaker": "kinnu", "text": "Gappu, see the ball rolling!", "emotion": "happy", "action": "point"},
                    {"speaker": "gappu", "text": "Why did it stop?", "emotion": "confused", "action": "think"},
                ],
                "animation_notes": ["Ball rolls then slows down"],
            },
            {
                "n": 2,
                "title": "Friction Helps",
                "background_prompt": "playground path with shoes and a ball, no characters",
                "learning_point": "grip comes from friction",
                "characters": {
                    "kinnu": {"x": 0.22, "y": 0.86, "height": 0.62, "pose": "explaining", "facing": "right"},
                    "gappu": {"x": 0.74, "y": 0.86, "height": 0.62, "pose": "happy", "facing": "left"},
                },
                "dialogue": [
                    {"speaker": "kinnu", "text": "Friction helps our shoes grip.", "emotion": "happy", "action": "explain"},
                    {"speaker": "gappu", "text": "So slipping means less friction!", "emotion": "surprised", "action": "happy_jump"},
                ],
                "animation_notes": ["Gappu does a small jump"],
            },
        ],
        "asset_needs": ["Kinnu rig", "Gappu rig", "backgrounds without characters"],
    }
)


def test_parse_story_json_plain():
    data = _parse_story_json(CANNED_STORY)
    assert data["chapter"].startswith("Kinnu")
    assert len(data["scenes"]) == 2
    assert data["scenes"][0]["dialogue"][0]["speaker"] == "kinnu"


def test_script_from_story_uses_dialogue_tags():
    data = _parse_story_json(CANNED_STORY)
    script = script_from_story(data)
    ScriptFile.model_validate(script)
    assert script["slides"][0]["narration"].startswith("F:")
    assert "\nM:" in script["slides"][0]["narration"]
    assert "No characters" in script["slides"][0]["visual_prompt"]


def test_render_story_from_story_is_story_build_ready():
    data = _parse_story_json(CANNED_STORY)
    render_story = render_story_from_story(data, "friction-story")

    assert render_story["story_id"] == "friction-story"
    assert render_story["cast"] == {"kinnu": "kinnu_hd", "gappu": "gappu_hd"}
    assert render_story["voices"]["kinnu"] == "af_bella"
    assert render_story["background"] == "classroom_full.png"
    assert render_story["scenes"][0]["dialogue"][0] == {
        "who": "kinnu",
        "text": "Gappu, see the ball rolling!",
        "gesture": "point",
    }
    assert render_story["scenes"][1]["dialogue"][1]["gesture"] == "smile"


def test_write_story_episode_writes_story_and_script(tmp_path, monkeypatch):
    monkeypatch.setattr(story, "ollama_available", lambda url: True)
    monkeypatch.setattr(story, "ollama_generate_json", lambda url, model, prompt, **k: CANNED_STORY)

    ep_dir, story_data, script_data, render_story = write_story_episode(
        "friction story", tmp_path, GeneratorConfig(), category="stories", n_scenes=2
    )

    assert ep_dir == tmp_path / "content" / "stories" / "friction-story"
    assert (ep_dir / "story_plan.yaml").exists()
    assert (ep_dir / "story.yaml").exists()
    assert (ep_dir / "script.yaml").exists()
    assert len(story_data["scenes"]) == 2
    assert render_story["cast"] == {"kinnu": "kinnu_hd", "gappu": "gappu_hd"}
    loaded = yaml.safe_load((ep_dir / "script.yaml").read_text(encoding="utf-8"))
    ScriptFile.model_validate(loaded)
    assert loaded == script_data
    loaded_story = yaml.safe_load((ep_dir / "story.yaml").read_text(encoding="utf-8"))
    assert loaded_story == render_story
