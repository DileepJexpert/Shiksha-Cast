# Katixo Shiksha — Content Folder Structure

## Target Audience
**Class 6–10 (Age 11–16)** | Indian teens | Hinglish | Curiosity-driven science

## Overview

Content is grouped into **three top-level categories** (these map to YouTube
playlists). Inside `how-it-works/`, episodes are further grouped by **subject**.

```
content/
├── README.md                    ← You are here
├── CONTENT_CREATION_GUIDE.md    ← How to design slides in Canva
├── SCRIPT_PROMPT_TEMPLATE.md    ← Prompt template for writing new scripts
│
├── how-it-works/                ← "Why/How does X work?" curiosity explainers
│   ├── human-body/              ←   goosebumps, dreams, hiccups, memory…
│   │   └── s01-goosebumps/
│   │       ├── script.yaml      ← Narration text (pipeline reads this)
│   │       ├── SLIDES.md        ← Per-slide Canva design instructions
│   │       └── slides/          ← Final PNG exports (1920×1080)
│   │           ├── slide_001.png
│   │           └── ...
│   ├── space/                   ←   rockets, black-holes, mars, stars…
│   ├── technology/              ←   wifi, gps, internet, ai, qr-codes…
│   ├── physics/                 ←   sky-blue, rainbows, magnets, planes…
│   ├── chemistry/               ←   batteries, popcorn, soda-fizz, glass…
│   └── earth-nature/            ←   ocean-salt, thunder, northern-lights…
│
├── class-chapter/               ← Syllabus-aligned, by class & chapter
│   ├── class-06/  …  class-10/  ←   (ready for NCERT chapter episodes)
│   └── README.md
│
├── general-knowledge/           ← Misc GK / fun facts (not "how it works")
│   └── README.md
│
└── _archive/                    ← Old Class 2-5 content (not active)
    ├── ch03/
    └── ...
```

> **Episode IDs are still just the folder name** (e.g. `s01-goosebumps`).
> The build tool finds an episode by name no matter how deeply it is nested,
> so `shiksha-cast build -c s01-goosebumps` works unchanged after the move.
> Build cache (`build/<id>/`) and output (`dist/<id>.mp4`) keep using that id.

## Categories

| Folder | What goes here | YouTube playlist |
|--------|----------------|------------------|
| `how-it-works/` | "Why is the sky blue?", "How does WiFi work?" — curiosity-driven explainers, grouped by subject | *How It Works* |
| `class-chapter/` | Episodes mapped to a specific class + NCERT chapter (`class-08/ch05-…`) | *Class 6 / 7 / 8 / 9 / 10* |
| `general-knowledge/` | Fun facts, trivia, "did you know" — knowledge that isn't a mechanism walkthrough | *General Knowledge* |

**Adding a new episode:** drop the episode folder under the category (and
subject) it belongs to. No code or config change is needed — the pipeline and
dashboard discover it automatically.

## How It Works

### For YOU (content creator):
1. Open any episode folder (e.g. `s01-goosebumps/`)
2. Read `SLIDES.md` — tells you exactly what to design per slide in Canva
3. Read `script.yaml` — the narration text (already written, 15 slides each)
4. Design slides in Canva following SLIDES.md instructions
5. Export as PNG (1920×1080) → save in the `slides/` folder as `slide_001.png`, `slide_002.png`, ...
6. Done! The pipeline takes over from here.

### For the PIPELINE (video tool):
1. Reads `script.yaml` → generates TTS audio per slide
2. Reads `slides/*.png` → renders video frames
3. Combines audio + slides → outputs MP4 + SRT captions
4. Command: `shiksha-cast build --chapter s01-goosebumps`

### Naming Convention
- `s01`, `s02`, ... = episode number (sortable)
- Keyword after number = topic (human-readable)
- Inside: `script.yaml` (always), `SLIDES.md` (always), `slides/` (PNGs), optionally `deck.pdf`

### Episode Checklist
- [ ] script.yaml written (15 slides of narration)
- [ ] SLIDES.md written (Canva design brief per slide)
- [ ] Slides designed in Canva (1920×1080)
- [ ] PNGs exported to slides/ (slide_001.png, slide_002.png, ...)
- [ ] Build tested: `shiksha-cast build --chapter s01-goosebumps`
- [ ] Video reviewed and quality-checked

### Season 1 Episodes (Class 6-10)
| # | Folder | Topic | Subject |
|---|--------|-------|---------|
| 1 | s01-goosebumps | Why Do You Get Goosebumps? | Biology / Evolution |
| 2 | s02-wifi | How Does WiFi Actually Work? | Physics / Tech |
| 3 | s03-blood-factory | Your Blood Factory | Biology / Human Body |
| 4 | s04-rockets | How Do Rockets Escape Earth? | Physics / Space / ISRO |
| 5 | s05-sky-blue | Why Is the Sky Blue? | Physics / Optics |
