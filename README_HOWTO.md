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
Current default: `provider: veena`, `model: kavya`.

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
- **Builds are slow / seem stuck** → TTS on an 8 GB laptop GPU is slow (minutes per slide for
  Veena). Keep the laptop **awake & plugged in**; it pauses when the machine sleeps.
- **"No PDF found"** → put `chNN.pdf` in `content\chNN\`, or upload PNG slides in the dashboard.
- **torch.cuda.is_available() is False** → reinstall CUDA PyTorch:
  `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`

---

## 6. Where things are

```
content\chNN\chNN.pdf     slide deck (Hindi)
content\chNN\chNN.yaml    narration script (Hinglish)
config\channel.yaml       voice + timing + branding config
dist\chNN.mp4 / .srt      final video + captions
src\shiksha_cast\         backend (pipeline, server, TTS, render, assemble)
scripts\veena_worker.py   Veena TTS worker (runs in .venv-veena)
ui\                       React dashboard
```
