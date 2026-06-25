# Shiksha-Cast — How to run locally (no Claude needed)

Turn a slide deck (PDF) + a narration script into a narrated, captioned MP4 — fully
**local and offline**. All models run on your own GPU; nothing is sent to a paid API.

---

## 0. First-time setup (run once)

Double-click **`setup.bat`** (or run it in a terminal). It installs the Python package,
the dashboard, and the Veena (Hinglish) environment, then checks CUDA + FFmpeg.

Prerequisites it expects:
- **Python 3.11+** with CUDA PyTorch (RTX 4060 8 GB here)
- **FFmpeg** on PATH (`ffmpeg -version`)
- **Node.js** (`node -v`)

---

## 1. Start the app (every session)

- Double-click **`run-backend.bat`**  → API on http://localhost:8000
- Double-click **`run-frontend.bat`** → it prints a URL like **http://localhost:5173** — open it.

Keep both windows open. Close them (Ctrl+C) to stop.

---

## 2. Make a video from the dashboard

1. Click the **chapter card** (e.g. `ch06`).
2. Review/edit the **narration** per slide.
   - For **Hinglish**, write Hindi in Devanagari with English terms inline, e.g.
     `आज हम place value सीखेंगे, और expanded form भी।` — the voice speaks exactly what you type.
   - Click **Save** after editing.
3. **Model Selector** → pick a voice:
   - **Veena — Kavya (Hinglish, female)** ← best Hindi-English mix (also Maitri / Agastya / Vinaya)
   - **Parler-TTS Mini/Large** → English
   - **Test Tone** → silent placeholder (pipeline test, no GPU)
4. Click **Build Video**, watch the live logs.
5. Click **Download** when done. Output is also saved at `dist\<chapter>.mp4` (+ `.srt`).

### Command-line alternative (more reliable for long builds)
```
build-video.bat ch06
```
Uses the voice in `config\channel.yaml`. Output: `dist\ch06.mp4` + `dist\ch06.srt`.

---

## 3a. Topic → video (generate a script with local AI)

Give a topic and let a **local LLM (Ollama)** write the script — fully offline,
no API key, no cost.

**One-time:** install [Ollama](https://ollama.com), then pull a model:
```
ollama pull llama3.1:latest
```

**Generate an episode from a topic:**
```
python -m shiksha_cast new-episode "RO water purifier review — is it worth buying?" ^
    --category general-knowledge --slides 8
```
This writes `content\general-knowledge\<slug>\script.yaml` (narration +
`visual_prompt` per slide). Review/edit the narration, then make the video:
```
python -m shiksha_cast ai-build -c <slug>     # SDXL images + motion + narration
python -m shiksha_cast thumb -c <slug>        # thumbnail
python -m shiksha_cast meta  -c <slug>        # title/description/tags
```
Add `--build` to `new-episode` to render the video immediately after generating.

**Batch everything:** `build-all.bat` (slides) and `build-all-ai.bat` (AI images)
build every episode that has no video yet, and now also emit each episode's
**thumbnail + YouTube metadata** (`dist\<ep>.thumb.png`, `dist\<ep>.youtube.md`).
Both are resumable — already-built/already-generated files are skipped.

Useful flags: `--category how-it-works/technology`, `--slug my-name`,
`--model qwen2.5:7b`, `--audience "..."`, `--style "..."`. Defaults live under
`generator:` in `config\channel.yaml`.

> The local model writes a usable **draft** — always skim and tweak the
> narration (and fill any empty `visual_prompt`) before building. For top
> quality you can still hand-write or use Claude Chat via
> `content\SCRIPT_PROMPT_TEMPLATE.md`.

---

## 3. Make a NEW chapter

1. Put the slide PDF at `content\chNN\chNN.pdf` (or upload PDF/PNG slides in the dashboard).
2. Write the narration:
   - In the dashboard slide editor (then **Save**), or
   - Edit `content\chNN\chNN.yaml` (copy `content\ch06\ch06.yaml` as a template).
3. Pick the voice → **Build Video** → **Download**.

---

## 4. Voices / TTS models (all local, open-source)

| Model | Language | License | Notes |
|-------|----------|---------|-------|
| **Veena** (kavya/maitri/agastya/vinaya) | **Hinglish** (Hindi+English) | Apache-2.0 | Best for this channel. Runs in `.venv-veena` (4-bit, ~2 GB VRAM). |
| Parler-TTS Mini v1 | English | Apache-2.0 | Fast, fits 8 GB. |
| Parler-TTS Large v1 | English | Apache-2.0 | Higher quality; **too big for 8 GB** (OOMs) — avoid on this GPU. |
| indic-parler-tts | Hindi/Hinglish | Apache-2.0 | Alternative Hinglish voice. |
| Test Tone (stub) | — | — | Silent; pipeline test only. |

Default voice lives in `config\channel.yaml` (`voice.provider` + `voice.model`).
Current default: `provider: veena`, `model: maitri`.

---

## 4b. Publishing assets (thumbnail, YouTube metadata, intro/outro/music)

The pipeline can generate everything you need to upload, not just the MP4.

**One-time — make the channel branding assets:**
```
python -m shiksha_cast make-assets
```
Creates `assets\intro.mp4` (3s bumper), `assets\outro.mp4` (subscribe card), and
`assets\music\gentle_learning.mp3` (a soft placeholder bed — swap it for a licensed
track anytime). Once these exist, **every build automatically** prepends the intro,
appends the outro, and mixes the music bed under the narration (captions/chapters are
auto-shifted to stay in sync). Re-run with `--force` to regenerate.

**Per episode — thumbnail + metadata:**
```
python -m shiksha_cast thumb -c s06-yawning   # -> dist\s06-yawning.thumb.png  (1280x720)
python -m shiksha_cast meta  -c s06-yawning   # -> dist\s06-yawning.youtube.md
```
- **thumb** renders a branded 1280×720 thumbnail (accent colour follows the episode's
  subject; "WHY?/HOW?" hook word in the background).
- **meta** writes a copy-paste-ready **title**, **description** (with auto chapter
  timestamps from the script), and **tags** — open the `.md`, paste into YouTube.

Episode IDs are just the folder name (e.g. `s06-yawning`), found anywhere under
`content/`. Build-cache and outputs continue to use that id.

### Shorts, thumbnail/title variants, and one-folder upload package

```
python -m shiksha_cast shorts  -c <ep> [--start 0 --duration 45 --hook "..." --count 1]
python -m shiksha_cast thumbs  -c <ep>     # 4 thumbnail styles: curiosity/exam/kids/hinglish
python -m shiksha_cast package -c <ep>     # bundles EVERYTHING into dist\packages\<ep>\
```

- **shorts** → vertical 9:16 clip(s) in `dist\shorts\` with a blurred fill
  background, your video centered, big burned-in captions, and a hook strip on top.
- **thumbs** → `dist\<ep>.thumb.<style>.png` × 4 distinct styles to A/B test.
- **package** → one upload-ready folder per episode:
  `video.mp4`, `thumbnail.png` (+ 4 styles in `thumbnails\`), `captions.srt`,
  `title.txt`, `titles.txt` (searchable/curiosity/Hinglish A/B ideas),
  `description.txt`, `tags.txt`, `pinned-comment.txt`, `short1.mp4`, and a
  `README.txt` checklist. The `meta`/package step also **validates chapters**
  against YouTube's rules (first at 0:00, ≥3 chapters, ≥10s apart) and lists any
  problems.

---

## 4c. Animated video (AI images + 2.5D parallax)

Instead of static slides, `ai-build` generates an image per slide (SDXL-Turbo,
fits 8 GB) and animates it. Choose the motion in `config\channel.yaml` →
`imagegen.motion`:

| motion | What it does | Needs |
|--------|--------------|-------|
| `kenburns` (default) | ffmpeg zoom/pan on the image | nothing extra |
| `parallax` | **DepthFlow** 2.5D depth animation — the image moves in 3D | `pip install depthflow` |
| `static` | no motion | nothing |

**Enable parallax (3D-looking motion, ~secs/clip on your GPU):**
```
pip install -e ".[parallax]"          # or: pip install depthflow
python -m shiksha_cast parallax-check  # renders dist\parallax_test.mp4 to verify
```
Then set `imagegen.motion: parallax` in `config\channel.yaml` and build:
```
python -m shiksha_cast ai-build -c s36-ai
```
Each slide image is turned into a parallax clip, the narration is mixed on, and
everything assembles as usual. If DepthFlow isn't installed (or a render fails),
the build **automatically falls back to Ken Burns** — it never breaks.

**Per-slide motion override.** Mix motions within one episode by adding a
`motion:` field to any slide in `script.yaml` (overrides `imagegen.motion`):
```yaml
slides:
  - n: 1
    narration: "..."
    visual_prompt: "a glowing brain firing neurons"
    motion: parallax     # this slide animates in 3D
  - n: 2
    narration: "..."
    motion: static       # this one holds still
```

**Animate every episode (batch):**
```
build-all-ai.bat
```
Resumable — skips episodes that already have `dist\<ep>.mp4`, honors per-slide
`motion:` overrides, and uses the channel default for the rest.

> Add a `visual_prompt:` to each slide in `script.yaml` so SDXL has something to
> draw. If your DepthFlow version uses different CLI flags, set
> `imagegen.parallax_command` (placeholders `{image} {output} {duration} {fps} {width} {height}`).

---

## 5. Troubleshooting

- **Veena not in the dropdown** → restart the backend (`run-backend.bat`).
- **Veena fails / `.venv-veena` missing** → recreate:
  ```
  python -m venv .venv-veena --system-site-packages
  .venv-veena\Scripts\python -m pip install snac bitsandbytes accelerate
  ```
- **CUDA out of memory** → you started two builds at once, or another app is using the GPU.
  Run **one build at a time** and close heavy GPU apps (Chrome video, NVIDIA Broadcast).
- **GPU stays "full" / a build seems stuck between runs** → a TTS worker from an
  interrupted build may be orphaned and holding VRAM. Double-click **`free-gpu.bat`**
  (or `powershell -File scripts\free_gpu.ps1`) to kill stray Veena/XTTS workers. It
  only targets this project's workers — your backend/UI are untouched.
- **Builds are slow / seem stuck** → TTS on an 8 GB laptop GPU is slow (minutes per slide for
  Veena). Keep the laptop **awake & plugged in**; it pauses when the machine sleeps.
- **"No PDF found"** → put `chNN.pdf` in `content\chNN\`, or upload PNG slides in the dashboard.
- **torch.cuda.is_available() is False** → reinstall CUDA PyTorch:
  `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`

---

## 6. Where things are

```
content\<category>\<ep>\  episode folder (script.yaml + SLIDES.md), e.g.
                          content\how-it-works\technology\s02-wifi\
config\channel.yaml       voice + timing + branding config
assets\intro|outro.mp4    branding bumpers (python -m shiksha_cast make-assets)
assets\music\*.mp3        music bed
dist\<ep>.mp4 / .srt      final video + captions
dist\<ep>.thumb.png       YouTube thumbnail (shiksha-cast thumb)
dist\<ep>.youtube.md      title/description/tags (shiksha-cast meta)
src\shiksha_cast\         backend (pipeline, server, TTS, render, assemble,
                          metadata, thumbnail, assets, branding)
scripts\veena_worker.py   Veena TTS worker (runs in .venv-veena)
ui\                       React dashboard
```
