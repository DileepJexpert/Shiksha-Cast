"""Generate an episode script (topic -> script.yaml) with a local LLM (Ollama).

Fully offline: talks to a local Ollama server over HTTP (no API key, no paid
API, no extra Python deps). Uses Ollama's JSON mode for reliable structured
output, validates it against the ScriptFile schema, and writes a ready-to-build
episode folder. The existing `ai-build` then turns it into a video.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import yaml

from shiksha_cast.config import GeneratorConfig, ScriptFile
from shiksha_cast.local_ai import (
    LocalAIUnavailable,
    ollama_available,
    ollama_generate_json,
)


class GeneratorUnavailable(RuntimeError):
    """The Ollama server (or model) isn't reachable/usable."""


def slugify(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].strip("-") or "episode"


def _build_prompt(topic: str, n_slides: int, audience: str, style: str) -> str:
    return f"""You are a scriptwriter for the "Katixo KhojLab" educational YouTube channel.

Write a narration script for a video about this topic:
"{topic}"

Audience: {audience}
Style: {style}

Rules:
- Exactly {n_slides} slides.
- Each "narration" is 50-80 words, spoken aloud, engaging and clear.
- Each "visual_prompt" describes ONE colourful educational illustration for that
  slide in under 25 words (e.g. "cartoon diagram of a reverse-osmosis membrane
  filtering dirty water into clean water, labelled, vibrant").
- Slide 1 = hook + intro. Last slide = quick recap + subscribe call.
- Do NOT include markdown, comments, or any text outside the JSON.

Output ONLY a JSON object with exactly this shape:
{{
  "chapter": "<short catchy episode title>",
  "slides": [
    {{"n": 1, "narration": "...", "visual_prompt": "..."}}
  ]
}}
"""


def _ollama_generate(url: str, model: str, prompt: str, timeout_s: int = 900) -> str:
    try:
        return ollama_generate_json(url, model, prompt, temperature=0.7, timeout_s=timeout_s)
    except LocalAIUnavailable as e:
        raise GeneratorUnavailable(str(e)) from e


def _parse_script_json(raw: str) -> dict:
    """Parse the model's JSON (tolerating stray prose/code fences) into a dict."""
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise GeneratorUnavailable("Model did not return JSON.")
        data = json.loads(m.group(0))
    if not isinstance(data, dict) or "slides" not in data:
        raise GeneratorUnavailable("Model JSON missing a 'slides' list.")
    slides = []
    for i, s in enumerate(data.get("slides", []), start=1):
        if not isinstance(s, dict):
            continue
        slides.append({
            "n": int(s.get("n", i)),
            "narration": str(s.get("narration", "")).strip(),
            "visual_prompt": str(s.get("visual_prompt", "")).strip() or None,
        })
    if not slides:
        raise GeneratorUnavailable("Model returned no usable slides.")
    return {"chapter": str(data.get("chapter", "Untitled")).strip(), "slides": slides}


def generate_script_dict(
    topic: str,
    cfg: GeneratorConfig,
    n_slides: Optional[int] = None,
    audience: str = "Indian students, age 11-16",
    style: str = "Hinglish (mostly English with light Hindi), curious and fun",
    model: Optional[str] = None,
) -> dict:
    """Generate and validate a script dict from a topic via Ollama."""
    n = n_slides or cfg.slides
    use_model = model or cfg.model
    if not ollama_available(cfg.url):
        raise GeneratorUnavailable(
            f"Ollama is not running at {cfg.url}. Start it (https://ollama.com) "
            f"and pull a model: ollama pull {use_model}"
        )
    prompt = _build_prompt(topic, n, audience, style)
    raw = _ollama_generate(cfg.url, use_model, prompt)
    data = _parse_script_json(raw)
    ScriptFile.model_validate(data)  # raises if malformed
    return data


def _unique_dir(base: Path, slug: str) -> Path:
    target = base / slug
    n = 2
    while target.exists():
        target = base / f"{slug}-{n}"
        n += 1
    return target


def write_episode(
    topic: str,
    project_root: Path,
    cfg: GeneratorConfig,
    category: str = "general-knowledge",
    slug: Optional[str] = None,
    n_slides: Optional[int] = None,
    audience: str = "Indian students, age 11-16",
    style: str = "Hinglish (mostly English with light Hindi), curious and fun",
    model: Optional[str] = None,
) -> tuple[Path, dict]:
    """Generate a script and write it to content/<category>/<slug>/script.yaml."""
    data = generate_script_dict(topic, cfg, n_slides, audience, style, model)

    base = project_root / "content"
    for part in category.split("/"):
        base = base / part
    base.mkdir(parents=True, exist_ok=True)

    ep_dir = _unique_dir(base, slug or slugify(topic))
    ep_dir.mkdir(parents=True, exist_ok=True)

    script_path = ep_dir / "script.yaml"
    with open(script_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=100)
    return ep_dir, data
