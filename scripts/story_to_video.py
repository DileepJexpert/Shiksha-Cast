"""Story -> video, fully local and Claude-free.

Turn a freeform story/topic into a multi-character animated video: a local Ollama
model writes the scene plan (characters, scenes, dialogue), then the multi-character
engine renders it (cast each with their own voice, lip-sync, captions, music bed,
-14 LUFS). Backgrounds are auto-generated (simple themed scenes) so nothing manual
is needed; drop nicer backgrounds into build/scene-<id>/backgrounds/ to upgrade.

Usage:
  python scripts/story_to_video.py "Kinnu and Gappu learn why the sky is blue" --scenes 5
  python scripts/story_to_video.py --story-json mystory.json        # skip Ollama (testing)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from shiksha_cast.config import load_channel_config  # noqa: E402

import scene_engine  # noqa: E402

CHARS = ROOT / "assets" / "characters"

# Map legacy Veena voice names to Kokoro voices (pass through real Kokoro ids).
VOICE_MAP = {
    "kavya": "af_heart", "maitri": "af_bella", "vinaya": "af_nicole",
    "agastya": "am_michael", "host": "af_heart",
}
THEMES = [
    ((26, 36, 92), (74, 60, 140)), ((18, 64, 92), (40, 124, 150)),
    ((92, 46, 60), (150, 90, 70)), ((28, 78, 56), (60, 150, 110)),
    ((70, 50, 96), (140, 96, 170)), ((90, 70, 30), (170, 140, 70)),
]


def kokoro_voice(v: str) -> str:
    if not v:
        return "af_heart"
    return v if "_" in v else VOICE_MAP.get(v.lower(), "af_heart")


def _font(size):
    for n in ("seguibl.ttf", "arialbd.ttf", "arial.ttf"):
        p = f"C:/Windows/Fonts/{n}"
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_bg(title: str, idx: int, out: Path, W: int, H: int):
    top, bot = THEMES[idx % len(THEMES)]
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    # decorative dots
    for i in range(60):
        x = (i * 137) % W
        yy = (i * 89) % H
        r = 2 + (i % 3)
        d.ellipse([x, yy, x + r, yy + r], fill=(255, 255, 255))
    if title:
        f = _font(64)
        w = d.textlength(title, font=f)
        d.text(((W - w) / 2, 46), title, font=f, fill=(255, 255, 255),
               stroke_width=5, stroke_fill=(40, 60, 150))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "story"


def bridge(story: dict, sid: str, W: int, H: int) -> dict:
    """Convert a StoryFile-style dict into a scene_engine scene spec."""
    registry = {p.name for p in CHARS.iterdir() if (p / "rig.json").exists()}
    cast = {}
    for c in story.get("characters", []):
        cid = (c.get("id") or c.get("name", "")).lower()
        if cid in registry:
            cast[cid] = kokoro_voice(c.get("voice"))
    if not cast:  # fall back to Kinnu
        cast = {"kinnu": "af_heart"}
    default_id = next(iter(cast))

    bgdir = ROOT / "build" / f"scene-{sid}" / "backgrounds"
    scenes = []
    for i, sc in enumerate(story.get("scenes", []), 1):
        bg = bgdir / f"bg_{i:03d}.png"
        make_bg(str(sc.get("title", "")), i, bg, W, H)
        lines = []
        for dlg in sc.get("dialogue", []):
            who = str(dlg.get("speaker", "")).lower()
            if who not in cast:
                who = default_id
            text = str(dlg.get("text", "")).strip()
            if text:
                lines.append({"who": who, "text": text})
        place = {}
        for cid, pl in (sc.get("characters", {}) or {}).items():
            if cid.lower() in cast:
                place[cid.lower()] = float(pl.get("x", 0.5)) if isinstance(pl, dict) else 0.5
        if not place:
            uniq = list(dict.fromkeys(ln["who"] for ln in lines))
            place = {n: (j + 1) / (len(uniq) + 1) for j, n in enumerate(uniq)}
        scenes.append({"bg": str(bg), "place": place, "lines": lines})

    return {"title": story.get("chapter", story.get("topic", "Story")),
            "cast": cast, "char_height": 0.6, "scenes": scenes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", nargs="?", help="story or topic (uses local Ollama)")
    ap.add_argument("--story-json", default=None, help="pre-made story dict (skips Ollama)")
    ap.add_argument("--scenes", type=int, default=5)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cfg = load_channel_config(ROOT)
    W, H = cfg.resolution

    if a.story_json:
        story = json.load(open(a.story_json, encoding="utf-8"))
        sid = slugify(story.get("chapter") or story.get("topic") or Path(a.story_json).stem)
    elif a.topic:
        from shiksha_cast.story import generate_story_dict
        print("[stage] asking local Ollama to write the story plan...")
        story = generate_story_dict(a.topic, cfg.generator, n_scenes=a.scenes)
        sid = slugify(story.get("chapter") or a.topic)
    else:
        ap.error("Provide a topic, or --story-json")

    print(f"[stage] bridging story -> scene ({sid})...")
    spec = bridge(story, sid, W, H)
    scene_dir = ROOT / "content" / "scenes" / sid
    scene_dir.mkdir(parents=True, exist_ok=True)
    scene_path = scene_dir / "scene.yaml"
    yaml.safe_dump(spec, open(scene_path, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    print(f"[stage] scene written -> {scene_path}")

    out = a.out or str(ROOT / "dist" / f"{sid}.mp4")
    scene_engine.render(str(scene_path), out)


if __name__ == "__main__":
    main()
