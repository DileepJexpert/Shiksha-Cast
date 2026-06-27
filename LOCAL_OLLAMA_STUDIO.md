# Local Ollama Studio Plan

Goal: Shiksha-Cast should create YouTube videos locally without Codex, Claude, or paid APIs.

## Roles

- Ollama model: writes drafts, story plans, scene directions, dialogue, metadata ideas.
- Python renderer: creates deterministic assets, movement, lip-sync, captions, final MP4.
- Local TTS: generates character voices.
- FFmpeg: assembles and masters video/audio.

## Commands

Check Ollama:
```powershell
python -m shiksha_cast ollama-check
```

Generate normal episode draft:
```powershell
python -m shiksha_cast new-episode "why friction slows things" --slides 8
```

Generate two-character story plan:
```powershell
python -m shiksha_cast new-story "friction story with Kinnu and Gappu" --scenes 6
```

## File Flow

`new-story` writes:

- `story.yaml`: source of truth for animated story direction.
- `script.yaml`: current build-compatible narration/dialogue.

Later renderer should read `story.yaml` directly:

```text
story.yaml
  -> local TTS per dialogue line
  -> lip-sync active speaker
  -> Kinnu/Gappu rig overlays
  -> background parallax
  -> moving props
  -> captions
  -> final MP4
```

## Asset Rule

Never bake characters into backgrounds for story episodes.

Use:

- `assets/characters/kinnu/rig.json`
- `assets/characters/gappu/rig.json`
- `assets/backgrounds/<scene>.png`
- `assets/props/<object>.png`

## Next Engineering Step

Build `scripts/render_story_video.py` to consume `story.yaml` and support two active rigs:

- speaking character mouth changes
- listening character blinks/reactions
- enter/exit/point/jump/think actions
- prop movement from `animation_notes`
