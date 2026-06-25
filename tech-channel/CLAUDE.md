# Katixo KhojLab — tech-curiosity channel (build guide)

## CHANNEL IDENTITY — Katixo KhojLab
- **Public name:** Katixo KhojLab
- **Handle:** @KatixoKhojLab
- **Tagline:** "Tech, science aur AI — Hinglish mein samjho"
- **Audience:** Class 8+ (~13–18), 13+ general — **NOT** Made for Kids
- **Footer brand (every slide):** "Katixo KhojLab" — *Katixo* muted, *KhojLab* accent (cyan)
- **Tone:** cool tech / curiosity, never childish. Dark "cool tech" theme.
- **End-screen CTA:** "Subscribe @KatixoKhojLab — nayi khoj har hafte"
- **Parent brand:** Katixo. Sister channel *Katixo Shiksha* (@KatixoShiksha, Class 1–5 maths) lives in this same repo later.

A faceless, slide-driven YouTube channel explaining **Computer Science, AI, and
"how technology works"** to Indian students (Class 8+, ages ~13–18). Videos are
4–7 min, **one curiosity-question per video**. The creator is a CS graduate /
software architect — that expertise is the edge.

**Audience is 13+ → NOT "Made for Kids".** Visual tone = "cool science / tech",
never childish.

This lives in `tech-channel/` and is **independent** of the rest of the repo
(Katixo Shiksha's TTS/SDXL video pipeline). It uses no GPU and no TTS — the
creator records their own voice off the narration script.

---

## What each episode produces (3-file system)
1. **slides** — `slides.html` → `slides.pdf` → `png/slide-01.png …` (2000×1125).
2. **narration** — `narration-en.html` + `narration-hi.html` → matching PDFs.
   Per-slide, Hinglish + English, with `[CUE]` reveal/pause notes and **stress**
   highlights. The slides are language-neutral, so one deck serves both scripts.
3. **meta.md** — title, hook line, the question answered, tags.

## Repo layout
```
tech-channel/
  CLAUDE.md                 ← this file
  render.sh                 ← one command: episode folder → PDFs + PNGs
  core/
    pdf2png.py              ← PDF → PNG @150dpi (PyMuPDF)
    themes/tech.css         ← slide design system (dark "cool tech")
    themes/narration.css    ← narration-script document style (light, readable)
    fonts/                  ← bundled: SpaceGrotesk.ttf (sans) + JetBrainsMono.ttf (mono)
    template/_episode-skeleton.html
  episodes/
    ep01_how-does-ai-work/  ← FULLY BUILT gold-standard reference
      slides.html  slides.pdf  png/
      narration-en.html  narration-en.pdf
      narration-hi.html  narration-hi.pdf
      meta.md
    ep02_… … ep12_…/        ← scaffolded (meta.md only)
```

## Render pipeline (Windows, no WeasyPrint)
We render with **Chrome headless → PDF**, then **PyMuPDF → PNG**. No GTK/poppler.
```
cd tech-channel
./render.sh episodes/ep01_how-does-ai-work
```
`render.sh` finds `slides.html` + any `narration-*.html` and renders them.
Slide size is set in CSS: `@page { size: 33.867cm 19.05cm; margin:0 }` →
exactly 2000×1125 px at 150 dpi. Override Chrome with `CHROME=… ./render.sh …`.

## Slide design system — `core/themes/tech.css`
- **Colors (CSS vars):** `--bg` deep navy/near-black, `--accent` cyan, `--accent2`
  lime, `--accent3` orange, `--danger` myth-pink. Change once, restyle everything.
- **Brand + counter** are auto-drawn on every slide from the deck — set them once:
  `<div class="deck" style='--total:"11"; --brand:"Katixo KhojLab";'>`. Each slide just needs
  an empty `<div class="foot"></div>`.
- **Reusable slide types (classes):**
  - `slide--title` — title slide + brandmark
  - `slide--question` — "Aaj ka sawaal" big question + faint `?`
  - `slide--concept` — one idea; helpers: `.headline .hl`, `.two-col`, `.bullets`
  - `.code` — terminal/code block (mono, mac dots, `.cm/.kw/.st/.fn` syntax colors)
  - `.predbar` — probability/level bars; `.chip` — labelled pills
  - `.hot` / `.want` — inline context highlights
  - `slide--myth` — "myth vs reality" two cards (`.myth .card.wrong/.right`)
  - `slide--recap` — auto-numbered `.takeaways`
  - `slide--cta` — subscribe + next-episode tease

## Episode structure — EXACTLY this order (~10–12 slides)
1. Title (the question) + brand
2. Hook (first 10s): relatable real-life framing + promise the payoff
3. "Aaj ka sawaal" — restate the one question
4–7. 3–4 explanation beats, **one idea per slide**, visual-first
8. Why it matters / real-world
9. Common myth ("yeh galat samajhte hain")
10. Recap (1–2 takeaways, one line each)
11. CTA: soft subscribe + tease next episode's question

## Content & tone rules
- **Dual narration:** slides are in English (globally readable); record an
  **English** track and a **Hinglish** (Hindi in Roman script + English terms)
  track from the two narration files. Pick the language per upload/channel.
- One question per episode. Curiosity-first **but accurate** — don't oversimplify
  into being wrong (the creator is an expert).
- Indian daily-life analogies (samosa queue = stack/queue, dabbawala = routing…).
- Original content only — own explanations, own diagrams. No copyrighted images.
- 13+ "cool", never nursery-rhyme childish.

## Add a new episode (clone the pattern)
1. `cp -r episodes/ep01_how-does-ai-work episodes/epNN_<slug>` (or start from
   `core/template/_episode-skeleton.html`).
2. Rewrite `slides.html` (keep the slide-type classes; set `--total` to the new
   slide count). Rewrite `narration-en.html` + `narration-hi.html` and `meta.md`.
3. `./render.sh episodes/epNN_<slug>` → check `png/`.
4. Record voice over the slides using the narration PDF; edit; upload with the
   title/hook/tags from `meta.md`.

## Brand
Footer/title brand is the single CSS variable `--brand` (currently `"Katixo KhojLab"`) plus
the title-slide `.brandmark` text. To rebrand, change those — re-render to update
PNGs. (A repo-wide rename of the *other* channel "Katixo Shiksha" is separate.)
