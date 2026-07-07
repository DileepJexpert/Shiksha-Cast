"""story-build: turn a compact, human-authored ``story.yaml`` (a multi-character
dialogue script) into a full cutout ``scenes.yaml`` (+ YouTube metadata), for the
STORY UNIVERSE (semi-realistic adult humans; moral / funny / normal stories).

Like tutorial.py, this owns only the STRUCTURE (placing the cast, turning dialogue
into talk actions, banners) and reuses the existing 2D renderer. The story
CONTENT is authored by a human. New realistic/social characters should use
namespaced ids like `social_universe/journalist_hd`, kept separate from the Kinnu
kids cast.

Spec schema (story.yaml):

    title: The Honest Shopkeeper
    story_id: story-honest-shopkeeper          # optional (else slugified from title)
    fps: 30
    universe: social_universe                  # optional asset namespace
    background: public_office.png              # default for all scenes
    cast:                                       # story NAME -> character asset id
      papa: common_man_hd
      ravi: student_hd
    voices:                                     # story NAME -> Kokoro voice (optional)
      papa: am_michael
      ravi: am_adam
    scenes:
      - background: story_living_room.png       # optional per-scene override
        banner: "A Short Story"                 # optional title card
        place: { papa: left, ravi: right }      # optional (else auto by order)
        dialogue:
          - { who: papa, text: "Beta, come here." }
          - { who: ravi, text: "Yes, papa?" }
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

# left/right anchors (feet at y=0.99); a lone speaker stands centre
POS = {"left": [0.30, 0.99], "right": [0.70, 0.99],
       "center": [0.50, 0.99], "mid_left": [0.40, 0.99], "mid_right": [0.60, 0.99]}
DEFAULT_BG = "story_living_room.png"
DEFAULT_VOICES = ["am_michael", "am_adam", "af_heart", "am_adam"]
CHAR_SCALE = 0.78  # adult rigs (832x1216) sized to fit two in a room


def _namespace_asset(universe: str | None, asset_id: str | Path) -> str:
    """Prefix a bare asset id with the story universe namespace.

    Explicit paths and already-namespaced ids are left alone so old story configs
    and one-off absolute assets keep working.
    """
    asset = str(asset_id)
    if not universe:
        return asset
    if "/" in asset or "\\" in asset or asset.startswith("assets/") or asset.startswith("assets\\"):
        return asset
    if re.match(r"^[a-zA-Z]:", asset):
        return asset
    return f"{universe}/{asset}"


def slugify(*parts: str) -> str:
    s = "-".join(str(p) for p in parts if p)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def load_spec(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def story_id(spec: dict) -> str:
    return spec.get("story_id") or slugify("story", spec.get("title", "untitled"))


def _auto_voices(cast: dict, given: dict | None) -> dict:
    given = given or {}
    voices = {}
    for i, name in enumerate(cast):
        voices[name] = given.get(name, DEFAULT_VOICES[i % len(DEFAULT_VOICES)])
    return voices


def _default_slots(cast: dict, raw_scenes: list) -> dict:
    """Pin each cast member to a stable side across the whole story."""
    slots = {}
    for sc in raw_scenes:
        for name, slot in (sc.get("place") or {}).items():
            if name in cast and name not in slots:
                slots[name] = slot
    fallback = ["left", "right", "mid_left", "mid_right"]
    for idx, name in enumerate(cast):
        if name in slots:
            continue
        slots[name] = "center" if len(cast) == 1 else fallback[min(idx, len(fallback) - 1)]
    return slots


def _slot_for(name: str, names: list, place: dict, pinned: dict) -> str:
    """Where this character stands: scene override, else pinned story position."""
    if name in place:
        return place[name]
    if name in pinned:
        return pinned[name]
    if len(names) == 1:
        return "center"
    return "left" if names.index(name) == 0 else "right"


def build_scenes(spec: dict) -> dict:
    universe = spec.get("universe")
    tts_provider = spec.get("tts_provider")
    if not tts_provider and universe == "social_universe":
        tts_provider = "veena"
    cast = {name: _namespace_asset(universe, asset)
            for name, asset in spec.get("cast", {}).items()}  # name -> asset id
    voices = _auto_voices(cast, spec.get("voices"))
    default_bg = _namespace_asset(universe, spec.get("background", DEFAULT_BG))
    fps = int(spec.get("fps", 30))
    scale = float(spec.get("scale", CHAR_SCALE))

    cast_assets = {asset: voices[name] for name, asset in cast.items()}

    raw_scenes = spec.get("scenes", [])
    pinned = _default_slots(cast, raw_scenes)

    scenes: list = []
    for idx, sc in enumerate(raw_scenes, start=1):
        dialogue = sc.get("dialogue", [])
        place = sc.get("place", {})
        # which story-names actually appear in this scene (from dialogue + place)
        names = []
        for d in dialogue:
            if d.get("who") and d["who"] not in names:
                names.append(d["who"])
        for n in place:
            if n not in names:
                names.append(n)
        if not names:
            names = list(cast)[: min(2, len(cast))]

        characters = []
        for name in names:
            slot = _slot_for(name, names, place, pinned)
            pos = POS.get(slot, POS["center"])
            facing = "right" if pos[0] < 0.5 else ("left" if pos[0] > 0.5 else "right")
            characters.append({"id": cast[name], "pos": list(pos),
                               "scale": scale, "facing": facing})

        actions = []
        for d in dialogue:
            asset = cast.get(d.get("who"))
            if not asset or not d.get("text"):
                continue
            action = {"who": asset, "do": d.get("do", "talk"), "text": str(d["text"])}
            if d.get("gesture"):
                action["gesture"] = d["gesture"]
            actions.append(action)

        overlays = []
        if sc.get("banner"):
            overlays.append({"type": "banner", "text": str(sc["banner"]),
                             "start": 0.0, "end": 3.5, "color": sc.get("banner_color", "yellow")})

        scene = {"id": sc.get("id", f"s{idx}"),
                 "background": _namespace_asset(universe, sc.get("background", default_bg)),
                 "transition": {"in": 0.3, "out": 0.3},
                 "characters": characters, "actions": actions}
        if overlays:
            scene["overlays"] = overlays
        scenes.append(scene)

    out = {"episode": story_id(spec), "title": spec.get("title", "A Short Story"),
           "fps": fps, "cast": cast_assets, "scenes": scenes}
    if tts_provider:
        out["tts_provider"] = tts_provider
    if spec.get("default_voice"):
        out["default_voice"] = spec["default_voice"]
    return out


def upload_metadata(spec: dict) -> str:
    title = spec.get("title", "A Short Story")
    desc = spec.get("description") or (
        f"{title} - a short animated story with a good message. Watch the full story "
        "and tell us what you learned in the comments!"
    )
    tags = ["story", "moral story", "animated story", "hindi story", "short story",
            "kahani", "story for kids", title.lower()]
    return (
        f"Title:\n{title}\n\n"
        f"Description:\n{desc}\n\n"
        "👍 Like, share and subscribe for a new story every day.\n\n"
        f"Hashtags:\n#story #moralstory #animatedstory #kahani #shortstory\n\n"
        f"Tags:\n{', '.join(t for t in tags if t.strip())}\n"
    )


def generate(spec_path: str | Path) -> dict:
    spec_path = Path(spec_path)
    spec = load_spec(spec_path)
    out_dir = spec_path.parent
    scenes = build_scenes(spec)
    scenes_path = out_dir / "scenes.yaml"
    scenes_path.write_text(
        yaml.dump(scenes, Dumper=_NoAliasDumper, sort_keys=False,
                  allow_unicode=True, width=100),
        encoding="utf-8",
    )
    meta_path = out_dir / "UPLOAD_METADATA.md"
    meta_path.write_text(upload_metadata(spec), encoding="utf-8")
    return {"episode": scenes["episode"], "scenes_path": scenes_path,
            "metadata_path": meta_path, "n_scenes": len(scenes["scenes"])}
