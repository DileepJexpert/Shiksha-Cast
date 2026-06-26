# Shiksha-Cast Dashboard — What You Can Do

Open the dashboard at **http://localhost:5173** (start it with `run-backend.bat` +
`run-frontend.bat`). This is a reference for every action available in the UI.

---

## 🏠 Dashboard (home screen)

- **Browse all chapters** as cards — each shows the title, slide count, badges
  (PDF / Script / Video) and a status (**Draft → Building → Ready**).
- **Refresh** button, plus **auto-refresh** (every ~8s and whenever you switch back
  to the browser tab) — newly added chapters and finished builds appear on their own.
- **+ New Chapter** → starts the upload flow.
- **How-to panel** (collapsible) with the basic steps.
- **Download MP4 / SRT** directly from any finished chapter's card.
- **Click a card** → opens that chapter's editor.

---

## ➕ New Chapter (the "+ New Chapter" flow)

- **Upload a PDF**, or **upload PNG slides** (select multiple).
- **Name the chapter** (e.g. `s56-my-topic`; auto-generated if left blank).
- A **stepper** guides you: Upload → Script & Voice → Build.

> You can also add a chapter on disk (`content/<id>/script.yaml` + slides) and just
> hit **Refresh** — no restart needed.

---

## ✏️ Chapter Editor (after clicking a card)

### 1. Build Video panel
- **Build Video** — auto-saves your script, then builds, with a **live log**
  (render → narration → assemble).
- **AI Visual Mode** toggle — generate SDXL images per slide instead of text slides
  (uses each slide's visual prompt).
- **Force Rebuild** toggle — ignore the cache and regenerate everything.
- **Download MP4 / SRT** when the build finishes.

### 2. TTS Voice Model selector
- Pick the voice by category tab — sets the default voice for the build:
  - **Veena** — Kavya / Maitri / Agastya / Vinaya (Hinglish, Hindi+English)
  - **Parler** — English
  - **Kokoro** — English (clear)
  - **Test Tone** — silent placeholder (pipeline test, no GPU)

### 3. Slide Editor
- **Paste full script** — drop your whole narration; separate slides with a blank
  line (or `---`); it auto-splits into the slides in order.
- **Per slide:**
  - edit the **narration** text,
  - choose a **per-slide voice** (mix male/female across slides),
  - add an **AI Visual Prompt** (for AI Visual Mode),
  - set an **advanced voice description**.
- **Two-host dialogue in one slide** — start lines with `F:` (female) or `M:` (male)
  and each line is voiced separately and stitched together.
- **Live stats** — narrated count, word count, estimated minutes.

---

## ⚠️ Things to remember

- Builds run on your **GPU — one at a time** (a second build will OOM the 8 GB card).
  For many episodes, use `build-all.bat` in a terminal instead.
- Editing narration + clicking **Build** **auto-saves** the script — there's no
  separate Save button.
- Keep the laptop **awake & plugged in** during builds (Veena narration is slow).
- The dashboard only **makes** the video locally. To publish, upload the finished
  `dist/<id>.mp4` to YouTube yourself (with `dist/<id>.youtube.md` + `dist/<id>.thumb.png`).

---

## Quick reference — equivalent terminal commands

| Dashboard action | Terminal equivalent |
|---|---|
| Build Video | `build-video.bat <id>` |
| Build all chapters | `build-all.bat` |
| AI Visual Mode | `python -m shiksha_cast ai-build -c <id>` |
| Thumbnail | `python -m shiksha_cast thumb -c <id>` |
| YouTube metadata | `python -m shiksha_cast meta -c <id>` |
| Make a Short | `python scripts/make_short.py <id>` |
| Presenter PDF/HTML decks | `python scripts/export_decks.py` |
