---
name: kinnu-cartoon
description: How to build Kinnu kids cartoon videos in this repo — the pipelines, commands, the quality bar, and every hard-won gotcha (spring, clipping, two-mouth, duration, IP-Adapter). Read this before touching the cartoon/3D/imagegen code or rendering an episode.
---

# Kinnu Cartoon Pipeline — working notes & lessons

Channel: **Kinnu** (@KinnuLearning, "A Katixo channel"). Original Indian kids cartoon,
fully **local & free** (no paid APIs). Kinnu is a **girl**. Canonical cast (exactly 5):
Kinnu, Gappu, Vibhu, Anshu, Prinshu. **k01 is already uploaded — never rebuild it.**

## Pipelines (all coexist — don't drop any)

| Track | Command | Character | Use |
|---|---|---|---|
| 2D cutout | `cartoon-build -c <ep>` | `kinnu_hd` (skeletal rig2) | Default. Reliable, fast, no GPU at runtime. |
| 3D-look hybrid | `cartoon-build -c <ep>` | `kinnu_3d` (sliced Pixar render) | Best-looking stills, flat motion. Mouth is a fixed baked smile. |
| Real 3D | `cartoon-build-3d -c <ep>` | VRoid `.vrm` + Blender | True 3D motion + real lip-sync. Needs a VRM export. |
| Art factory | `scripts/make_kinnu_stills.py` | IP-Adapter remix | Stills/thumbnails/parts only — NOT animation (flickers per frame). |

Envs: render + imagegen + upscale use **`.venv-veena`** (PIL, diffusers 0.31, spandrel,
torch **cu124 = GPU**). Kokoro TTS runs out-of-process in **`.venv-kokoro`** which is
**torch CPU-only** (its misaki/spacy deps are pinned there — do NOT install GPU torch
into it). Blender portable at `C:\Users\dileepkm\BlenderPortable`. ffmpeg on PATH.

**RTX 4060 (8 GB) usage map** — what actually runs on the GPU:
- Image gen: SDXL (`imagegen/sdxl.py`, turbo) + IP-Adapter (`imagegen/ipadapter.py`, base). ✅ GPU
- Upscaling: Real-ESRGAN anime 4x (`imagegen/upscale.py`, spandrel, tiled). ✅ GPU.
  `scripts/upscale_image.py in out [--1080]`; or `make_cartoon_backgrounds.py … --upscale`.
- 3D render: Blender (needs a VRM). ✅ GPU. Cutout animation render: CPU (fine).
- TTS (Kokoro): CPU (small/fast). ffmpeg assembly: CPU.
We do NOT use ComfyUI (our Python SDXL covers it) or AI video models (too weak at 8 GB —
use the cutout/3D motion instead).

## The quality bar (what makes a video good — learned from comparison)

A finished episode should have, not just "character on a background":
1. **An overlay layer** — title banners per section + callout graphics (arrows, "OOPS!",
   speech bubbles, signs, simple diagrams). This is the single biggest quality lever.
2. **Per-episode themed backgrounds** — generate topic-specific SDXL backgrounds
   (`make_cartoon_backgrounds.py`), don't reuse the 6 generic ones for everything.
3. **A story arc** — hook → why → examples → recap → outro. Teach a concept, not a list.
4. **Real target duration** — see the duration gotcha below.
5. Props that visualize the words (shapes/balloons/numerals in `assets/cartoon/props/`).

## Gotchas (each cost real time — check before repeating)

- **Springy/dangling hands**: the resting arm must be **locked to 0** on the shoulder
  (`al=(0,2)`, `ar=(0,-2)` in `build.py:_adv_pose`; `idle()` arms 0 in `motion.py`).
  Even ±1° shoulder drift reads as a spring because the hand is far from the pivot.
  Breathing goes in the **vertical bob only**.
- **Hands clipped at frame edge** when pointing sideways / cheering overhead: `rig2.py`
  composes onto a padded canvas (`render_padding`, default 220). Keep the regression
  test `tests/test_cartoon_rig2.py` green.
- **Two mouths** on `kinnu_3d`: the baked 3D head already has a smile; overlaying a flat
  viseme doubles it, and erasing the baked one smudges shaded skin. Fix = keep the clean
  baked head + disable the overlay (`face: {}` in its `rig2.json`). Real lip-sync belongs
  to the VRoid 3D track, not the baked cutout.
- **Duration ≠ episode name**: Kokoro speaks faster than the scene estimates. A "10-min"
  script can render to ~4 min. **Always `ffprobe` the real duration** and add scenes/lines
  to hit the target. ~10 min ≈ 100–120 talk lines.
- **IP-Adapter crashes with `'tuple' has no attribute 'shape'`**: `enable_attention_slicing()`
  replaces the UNet attn processors and clobbers the IP-Adapter ones. **Don't enable it**
  with IP-Adapter (CPU offload + VAE slicing are fine; torch 2.x SDPA is already efficient).
- **IP-Adapter duplicates the subject / bleeds color**: SDXL-**Turbo** runs at guidance 0,
  so **negative prompts are ignored**. Use **SDXL base** (CFG ~6, ~28 steps) for control,
  use portrait 832×1216. ViT-H adapter needs its encoder loaded explicitly.
- **IP-Adapter makes Kinnu off-brand (rainbow dress / wrong pose)**: at `ip_scale` 0.6 the
  outfit drifts; ~**0.8** keeps the solid yellow dress + single subject. Say "plain SOLID
  yellow dress" (the word "vibrant" in the style → rainbow dress) and put
  "multicolor/rainbow/patterned/striped dress" in the NEGATIVE. Defaults in `ipadapter.py`
  are now tuned for this. **Limitation:** IP-Adapter is great for thumbnails / "Kinnu in a
  scene" stills, but it does NOT faithfully reproduce exact poses or every outfit detail
  (bow/shoe color may drift). For exact poses use the 2D cutout rig; for exact brand
  fidelity, composite the cutout or train a LoRA.

## Character canon & assets
- Kinnu: warm brown skin, black ponytail + **pink** bow, big brown eyes, **yellow** dress,
  **blue** shoes, gold earrings. Reference: `assets/cartoon/source/kinnu_3d_ref.png`.
- Per-character rig geometry lives in each `assets/cartoon/characters/<id>/rig2.json`
  (joints, pivots, bone lengths, part_scale, padding). `rig2.py` reads it.

## Repo hygiene
- `build/`, `dist/`, `*.mp4`, `*.wav` are gitignored. Loose root UUID pngs / zips / `tmp/`
  are gitignored too — never commit them.
- Commit/push **only when asked**. End commits with the Co-Authored-By trailer.

## Backlog / open
- Add the **overlay/graphics layer** to `build.py` as a first-class scene feature.
- Finish the IP-Adapter stills factory (SDXL base) → thumbnails + nicer cutout parts.
- User will export the final VRoid Kinnu VRM → then re-render the real-3D track.

> Keep this file updated: when something surprises you or you fix a non-obvious bug,
> add a one-line lesson here so we don't relearn it.
