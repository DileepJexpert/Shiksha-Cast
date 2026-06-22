# Shiksha-Cast — Local Setup & Usage Guide

## Prerequisites

- **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads/)
- **FFmpeg** — required for video assembly
  - Windows: `winget install FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- **Node.js 18+** — only needed if you want the React UI
  - [nodejs.org/download](https://nodejs.org/en/download)
- **GPU (optional)** — Parler-TTS runs on CPU too, just slower. 8GB VRAM is enough.

---

## Step 1: Clone the repo

```bash
git clone https://github.com/dileepjexpert/shiksha-cast.git
cd shiksha-cast
git checkout claude/youthful-mccarthy-xg0wn7
```

## Step 2: Install Python dependencies

```bash
# Core (render + assembly + captions)
pip install -e "."

# With TTS (real voice generation via Indic Parler-TTS)
pip install -e ".[tts]"

# With API server (for React UI)
pip install -e ".[server]"

# With dev tools (testing + linting)
pip install -e ".[dev]"

# All at once
pip install -e ".[tts,server,dev]"
```

## Step 3: Verify installation

```bash
shiksha-cast --help
ffmpeg -version
python -m pytest tests/ -v
```

---

## Using the CLI

### Prepare your chapter

1. Create a folder under `content/`:
   ```
   content/ch05/
   ├── ch05.pdf      ← your slide deck
   └── ch05.yaml     ← narration script
   ```

2. Write the narration script (`ch05.yaml`):
   ```yaml
   chapter: "Ch 5 — Fun with Shapes"
   slides:
     - n: 1
       narration: "नमस्ते बच्चों! आज हम सीखेंगे shapes के बारे में।"
     - n: 2
       narration: "2D shapes flat होती हैं — triangle, square, rectangle, circle।"
     - n: 3
       narration: "3D shapes solid होती हैं — cube, sphere, cylinder, cone।"
   ```

   **Narration tips:**
   - Write Hindi in **Devanagari** (not Roman) — TTS pronunciation is much better
   - Keep English maths terms in English (place value, triangle, etc.)
   - One narration per slide = one audio clip = that slide's on-screen time

### Run individual stages

```bash
# PDF → slide PNGs (1920×1080)
shiksha-cast render --chapter ch05

# Script → narration WAV per slide
shiksha-cast speak --chapter ch05

# Script + durations → SRT subtitles
shiksha-cast captions --chapter ch05
```

### Build the full video (recommended)

```bash
# Runs all stages: render → speak → assemble → caption
shiksha-cast build --chapter ch05
```

Output files appear in `dist/`:
```
dist/
├── ch05.mp4    ← YouTube-ready video (1920×1080, H.264, AAC)
└── ch05.srt    ← timed subtitles
```

### Useful flags

```bash
# Force rebuild (ignore cache)
shiksha-cast build --chapter ch05 --force

# Point to a different project root
shiksha-cast build --chapter ch05 --root /path/to/shiksha-cast
```

---

## Using the React UI

### Start the API server (Terminal 1)

```bash
uvicorn shiksha_cast.server:app --reload
```

Server runs at `http://localhost:8000`.

### Start the React dev server (Terminal 2)

```bash
cd ui
npm install
npm run dev
```

UI runs at `http://localhost:5173`.

### UI workflow

1. Open `http://localhost:5173` in your browser
2. Choose **Upload PDF** or **Upload Slides (PNG)**
3. Enter a chapter name (e.g. `ch05`) or leave blank for auto
4. Drop your file(s) — slides appear as thumbnails
5. Type narration text for each slide in the text areas
6. Set voice description (optional, shared across slides)
7. Click **Build Video**
8. Wait for build to complete → click **Download MP4**

---

## TTS Configuration

### Default (with GPU or CPU)

The default provider is **Indic Parler-TTS** (`ai4bharat/indic-parler-tts`).
First run downloads the model (~1 GB). Subsequent runs use the cached model.

Voice is controlled in `config/channel.yaml`:
```yaml
voice:
  provider: parler
  description: >
    A young female teacher speaks in a warm, cheerful, animated tone,
    clearly and a little slowly, as if teaching small children.
    Very clear audio, almost no background noise.
```

### Without GPU / for quick testing

If `torch` is not installed, TTS automatically falls back to a **stub provider**
that generates a sine-wave tone (correct duration, no real voice). This lets you
test the full pipeline without a GPU.

You can also force the stub provider:
```yaml
# config/channel.yaml
voice:
  provider: stub
```

---

## Project structure

```
shiksha-cast/
├── config/channel.yaml          ← shared channel settings (voice, resolution, timing)
├── content/chNN/                ← one folder per chapter
│   ├── chNN.pdf                 ←   slide deck
│   └── chNN.yaml                ←   narration script
├── build/chNN/                  ← cache (auto-generated, gitignored)
│   ├── slides/                  ←   rendered PNGs
│   ├── audio/                   ←   narration WAVs
│   ├── clips/                   ←   per-slide video clips
│   └── manifest.json            ←   hash cache for idempotency
├── dist/                        ← final outputs (gitignored)
│   ├── chNN.mp4                 ←   YouTube-ready video
│   └── chNN.srt                 ←   subtitles
├── src/shiksha_cast/            ← Python source
│   ├── cli.py                   ←   Typer CLI
│   ├── config.py                ←   pydantic models + YAML loading
│   ├── render.py                ←   PDF → PNG (pypdfium2)
│   ├── speak.py                 ←   script → audio (TTS)
│   ├── assemble.py              ←   PNG + WAV → MP4 (FFmpeg)
│   ├── captions.py              ←   script → SRT
│   ├── pipeline.py              ←   orchestrates all stages
│   ├── server.py                ←   FastAPI backend for UI
│   └── tts/
│       ├── base.py              ←   TTSProvider interface
│       ├── parler.py            ←   Indic Parler-TTS (real voice)
│       └── stub.py              ←   test tone (no GPU needed)
├── ui/                          ← React frontend (Vite)
└── tests/                       ← pytest suite (19 tests)
```

## Caching

Re-running a build skips unchanged work:
- **Render**: skipped if PDF page hash unchanged
- **Speak**: skipped if narration text + voice settings unchanged
- **Assembly**: always rebuilt (fast, just FFmpeg concat)

Use `--force` to bust the cache. Delete `build/chNN/` for a clean rebuild.

## Running tests

```bash
python -m pytest tests/ -v
```

All 19 tests should pass. Tests cover config loading, cache, render, TTS (stub), captions, and assembly.
