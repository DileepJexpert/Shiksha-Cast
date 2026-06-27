from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from shiksha_cast.config import GeneratorConfig, ScriptFile
from shiksha_cast.generate import slugify
from shiksha_cast.local_ai import LocalAIUnavailable, ollama_available, ollama_generate_json


class StoryUnavailable(RuntimeError):
    """The local story planner could not generate a usable story."""


class StoryCharacter(BaseModel):
    id: str
    name: str
    voice: str = "kavya"
    description: str = ""
    rig: Optional[str] = None


class StoryPlacement(BaseModel):
    x: float = 0.5
    y: float = 0.86
    height: float = 0.62
    pose: str = "idle"
    facing: str = "front"


class StoryDialogue(BaseModel):
    speaker: str
    text: str
    emotion: str = "happy"
    action: str = "talk"


class StoryScene(BaseModel):
    n: int
    title: str
    background_prompt: str
    learning_point: Optional[str] = None
    characters: dict[str, StoryPlacement] = Field(default_factory=dict)
    dialogue: list[StoryDialogue]
    animation_notes: list[str] = Field(default_factory=list)


class StoryFile(BaseModel):
    chapter: str
    topic: str
    audience: str
    style: str
    characters: list[StoryCharacter]
    scenes: list[StoryScene]
    asset_needs: list[str] = Field(default_factory=list)


DEFAULT_CHARACTERS = [
    StoryCharacter(
        id="kinnu",
        name="Kinnu",
        voice="kavya",
        rig="assets/characters/kinnu/rig.json",
        description="curious friendly girl stickman host",
    ),
    StoryCharacter(
        id="gappu",
        name="Gappu",
        voice="agastya",
        rig="assets/characters/gappu/rig.json",
        description="cute friendly boy stickman friend, playful and asks questions",
    ),
]


def _story_prompt(topic: str, n_scenes: int, audience: str, style: str) -> str:
    characters_json = json.dumps([c.model_dump() for c in DEFAULT_CHARACTERS], ensure_ascii=False)
    return f"""You are the offline story director for a local kids YouTube animation pipeline.

The video is made from separate layers:
- background PNGs with NO characters baked in
- transparent character rigs for Kinnu and Gappu
- local TTS voices
- local mouth open/half/closed lip-sync
- Python/FFmpeg movement, camera, captions, and final MP4

Create a two-character educational story plan for this topic:
"{topic}"

Audience: {audience}
Style: {style}
Characters available:
{characters_json}

Rules:
- Exactly {n_scenes} scenes.
- Keep it wholesome, simple, funny, and useful for children.
- Every scene needs 2 to 5 short dialogue lines.
- Dialogue speaker IDs must be only "kinnu" or "gappu".
- Kinnu explains with warmth. Gappu asks questions or reacts with playful curiosity.
- Background prompts must describe the scene ONLY. Do not include Kinnu, Gappu,
  people, mascot, slide number, or character in background_prompt.
- Use reusable animation actions like: enter_left, enter_right, idle_bob, point,
  think, surprised, happy_jump, look_at_object, object_rolls, object_stops.
- Keep character x positions in 0..1: kinnu usually left around 0.22, gappu right around 0.74.
- Output JSON only. No markdown, no explanation.

Output exactly this JSON shape:
{{
  "chapter": "<short catchy video title>",
  "topic": "{topic}",
  "audience": "{audience}",
  "style": "{style}",
  "characters": [
    {{"id": "kinnu", "name": "Kinnu", "voice": "kavya", "description": "...", "rig": "assets/characters/kinnu/rig.json"}},
    {{"id": "gappu", "name": "Gappu", "voice": "agastya", "description": "...", "rig": "assets/characters/gappu/rig.json"}}
  ],
  "scenes": [
    {{
      "n": 1,
      "title": "Hook",
      "background_prompt": "bright cartoon classroom floor with a toy ball, no characters, open space at left and right",
      "learning_point": "what the scene teaches",
      "characters": {{
        "kinnu": {{"x": 0.22, "y": 0.86, "height": 0.62, "pose": "happy", "facing": "right"}},
        "gappu": {{"x": 0.74, "y": 0.86, "height": 0.62, "pose": "confused", "facing": "left"}}
      }},
      "dialogue": [
        {{"speaker": "kinnu", "text": "Gappu, look at this!", "emotion": "happy", "action": "point"}},
        {{"speaker": "gappu", "text": "Why did it stop?", "emotion": "confused", "action": "think"}}
      ],
      "animation_notes": ["Kinnu enters from left", "Gappu tilts head while listening"]
    }}
  ],
  "asset_needs": [
    "backgrounds without characters",
    "Kinnu rig with mouth states",
    "Gappu rig with mouth states"
  ]
}}
"""


def _parse_story_json(raw: str) -> dict:
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise StoryUnavailable("Model did not return JSON.")
        data = json.loads(m.group(0))

    if not isinstance(data, dict) or "scenes" not in data:
        raise StoryUnavailable("Model JSON missing a 'scenes' list.")

    scenes = data.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        raise StoryUnavailable("Model returned no usable scenes.")

    data.setdefault("topic", data.get("chapter", "Untitled"))
    data.setdefault("audience", "kids")
    data.setdefault("style", "friendly animated explainer")
    data.setdefault("characters", [c.model_dump() for c in DEFAULT_CHARACTERS])
    data.setdefault("asset_needs", [])
    return StoryFile.model_validate(data).model_dump(exclude_none=True)


def generate_story_dict(
    topic: str,
    cfg: GeneratorConfig,
    n_scenes: int = 6,
    audience: str = "kids age 5-10",
    style: str = "Hinglish, funny and warm, like a playful science cartoon",
    model: Optional[str] = None,
) -> dict:
    use_model = model or cfg.model
    if not ollama_available(cfg.url):
        raise StoryUnavailable(
            f"Ollama is not running at {cfg.url}. Start it and pull a model: ollama pull {use_model}"
        )
    prompt = _story_prompt(topic, n_scenes, audience, style)
    try:
        raw = ollama_generate_json(cfg.url, use_model, prompt, temperature=0.55)
    except LocalAIUnavailable as e:
        raise StoryUnavailable(str(e)) from e
    data = _parse_story_json(raw)
    if len(data["scenes"]) != n_scenes:
        raise StoryUnavailable(f"Expected {n_scenes} scenes, got {len(data['scenes'])}. Try again.")
    return data


def script_from_story(story: dict) -> dict:
    """Convert a rich story plan into the current script.yaml format.

    This keeps the existing local TTS/build pipeline useful today. The richer
    story.yaml remains available for a future multi-character renderer.
    """
    speaker_tags = {"kinnu": "F", "gappu": "M"}
    slides = []
    for i, scene in enumerate(story.get("scenes", []), start=1):
        lines = []
        for dialogue in scene.get("dialogue", []):
            speaker = str(dialogue.get("speaker", "")).lower()
            tag = speaker_tags.get(speaker, "N")
            text = str(dialogue.get("text", "")).strip()
            if text:
                lines.append(f"{tag}: {text}")
        narration = "\n".join(lines).strip()
        visual_prompt = str(scene.get("background_prompt", "")).strip()
        if visual_prompt:
            visual_prompt = f"{visual_prompt}. No characters, no people, no mascot, leave space for overlays."
        slides.append(
            {
                "n": int(scene.get("n", i)),
                "narration": narration,
                "visual_prompt": visual_prompt or None,
                "motion": "kenburns",
            }
        )
    script = {"chapter": story.get("chapter", story.get("topic", "Untitled Story")), "slides": slides}
    ScriptFile.model_validate(script)
    return script


def _unique_dir(base: Path, slug: str) -> Path:
    target = base / slug
    n = 2
    while target.exists():
        target = base / f"{slug}-{n}"
        n += 1
    return target


def write_story_episode(
    topic: str,
    project_root: Path,
    cfg: GeneratorConfig,
    category: str = "stories",
    slug: Optional[str] = None,
    n_scenes: int = 6,
    audience: str = "kids age 5-10",
    style: str = "Hinglish, funny and warm, like a playful science cartoon",
    model: Optional[str] = None,
) -> tuple[Path, dict, dict]:
    story = generate_story_dict(topic, cfg, n_scenes, audience, style, model)
    script = script_from_story(story)

    base = project_root / "content"
    for part in category.split("/"):
        base = base / part
    base.mkdir(parents=True, exist_ok=True)

    ep_dir = _unique_dir(base, slug or slugify(topic))
    ep_dir.mkdir(parents=True, exist_ok=True)

    with open(ep_dir / "story.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(story, f, allow_unicode=True, sort_keys=False, width=100)
    with open(ep_dir / "script.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(script, f, allow_unicode=True, sort_keys=False, width=100)

    return ep_dir, story, script
