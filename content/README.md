# Katixo Shiksha — Content Folder Structure

## Target Audience
**Class 6–10 (Age 11–16)** | Indian teens | Hinglish | Curiosity-driven science

## Overview

```
content/
├── README.md                    ← You are here
├── CONTENT_CREATION_GUIDE.md    ← How to design slides in Canva
├── SCRIPT_PROMPT_TEMPLATE.md    ← Prompt template for writing new scripts
│
├── s01-goosebumps/              ← Episode 1: Why Do You Get Goosebumps?
│   ├── script.yaml              ← Narration text (pipeline reads this)
│   ├── SLIDES.md                ← Per-slide Canva design instructions
│   └── slides/                  ← Final PNG exports from Canva (1920×1080)
│       ├── slide_001.png
│       ├── slide_002.png
│       └── ...
│
├── s02-wifi/                    ← Episode 2: How Does WiFi Actually Work?
│   ├── script.yaml
│   ├── SLIDES.md
│   └── slides/
│
├── s03-blood-factory/           ← Episode 3: Your Blood Factory
│   ├── script.yaml
│   ├── SLIDES.md
│   └── slides/
│
├── s04-rockets/                 ← Episode 4: How Do Rockets Escape Earth?
│   ├── script.yaml
│   ├── SLIDES.md
│   └── slides/
│
├── s05-sky-blue/                ← Episode 5: Why Is the Sky Blue?
│   ├── script.yaml
│   ├── SLIDES.md
│   └── slides/
│
└── _archive/                    ← Old Class 2-5 content (not active)
    ├── ch03/
    ├── ch05/
    └── ...
```

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
