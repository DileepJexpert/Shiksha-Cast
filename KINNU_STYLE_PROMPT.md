# Kinnu — Reusable ChatGPT Slide Prompt (locks the channel style)

Use ChatGPT (GPT‑4o image / DALL·E) to make slide decks — it's the best tool for
readable on‑image text + a consistent character. Local SDXL can't match it.

**Workflow for any episode:**
1. Open the episode's `SLIDES.md` (e.g. `content/kinnu/k02-star-bridge-counting/SLIDES.md`).
   It already lists each slide's visual + on‑screen text.
2. Paste the **STYLE PROMPT** below into ChatGPT once.
3. Then paste each slide's brief and ask for that slide. Keep the style locked.
4. Export each as 1920×1080 PNG, drop into `build/<episode-id>/slides/` as
   `slide_001.png … slide_00N.png`, then build the video (`build-video.bat <id>`).

---

## ⭐ MASTER STYLE PROMPT (paste first, once per chat)

> Create a 16:9 (1920×1080) slide for a kids' YouTube channel called **Kinnu**.
> **Character — Kinnu:** a cute friendly **girl** stickman — big round white head, big
> happy expressive eyes, thin hair strands with a small hair bow, simple thick black
> outlines, wearing a yellow shirt and blue pants. Keep Kinnu's design **identical on
> every slide**.
> **Brand:** put the round **Kinnu logo** (waving mascot + bold blue "K") in the
> **top‑left** corner. Add a small **"Slide N of M"** rounded badge in the bottom‑left.
> **Look:** bright, cheerful, flat cartoon style; cream/blue classroom or themed
> adventure background; colourful bunting; thick outlines; **3D‑looking objects**
> (laddoos, coins, stars, etc.); big rounded **bold colourful title text** with a
> white outline; short punchy on‑screen text only.
> **Rules:** spell all text exactly as I give it; counts must be exact (if I say 3
> laddoos, draw exactly 3); wholesome and kid‑safe; no extra/garbled text.

---

## Per‑slide prompt (repeat for each slide)

> Same Kinnu style and character as above. **Slide {N} of {M}.**
> Scene: {paste the "Visual" line from SLIDES.md}
> On‑screen text (spell exactly): "{paste the on‑screen text from SLIDES.md}"
> Mood: {happy / surprised / thinking / cheering}.

---

## Tips for consistency
- Generate **slide 1 first**, get the character right, then say "keep the same Kinnu
  and style" for every following slide.
- If a count is wrong, say: "show **exactly** N objects."
- If text is misspelled, say: "fix the text to read exactly: …".
- Reuse the **logo** (`chatgptsamples/.../logo/`) and **watermark** files you already have.

## Then turn the deck into a video (local, free)
```
REM put the 8 PNGs in build\<id>\slides\ as slide_001.png … slide_008.png
build-video.bat <id>          REM Kavya narration over your slides -> dist\<id>.mp4
```
Narration for k01–k08 is already written (feminine, Kavya) in each
`content/kinnu/<id>/script.yaml`.
