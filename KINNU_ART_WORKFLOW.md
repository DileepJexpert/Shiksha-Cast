# Kinnu Art Workflow — from an AI image to an animated character

You do **not** need VRoid, VRM, or any 3D tool. Kinnu is a **2D cutout puppet**: one
"rig sheet" image of all her body parts, sliced into transparent PNGs that the engine
rotates, swaps, and lip-syncs. To upgrade how Kinnu looks, you replace **one image**.

```
 Nano Banana / Gemini            slice_rigsheet.py           rig2.py (engine)
 ┌──────────────────┐   PNG      ┌───────────────┐  parts/   ┌──────────────┐
 │ high-quality     │ ────────►  │ auto-detect & │ ────────► │ poses, walk, │
 │ rig sheet image  │            │ slice 26 parts│           │ talk, blink  │
 └──────────────────┘            └───────────────┘           └──────────────┘
```

---

## Step 1 — Generate the rig sheet with Google Nano Banana (Gemini)

Nano Banana is ideal here because it keeps a character **consistent** while editing.
Open Google AI Studio (Gemini), and **upload the existing sheet as a reference**:
`assets/cartoon/source/kinnu_rigsheet.png`. Then prompt:

> Redraw this exact character rig sheet at high quality. Keep the SAME grid layout —
> same rows, same left-to-right order, same labels under each part. Character is
> **Kinnu**: a cute cartoon girl, black hair in a side ponytail with a pink bow, fair
> skin, yellow dress with a pink flower belt, blue sneakers. Flat 2D cartoon style,
> thick clean dark outlines, smooth vector-like shading, plain white background.
>
> The sheet MUST contain these parts, in these rows, in this order:
> - **Row 1:** torso (dress), head (BLANK face — no eyes/brows/mouth), upper_arm_left,
>   forearm_left (hand at the end), upper_arm_right, forearm_right (hand at the end)
> - **Row 2:** 4 eyebrow pairs (neutral, happy, sad, surprised), then 3 eye pairs
>   (open, closed, happy)
> - **Row 3:** 9 mouth shapes labelled A B C D E F G H X — A=closed lips, B=slightly
>   open, C=open, D=wide open, E=rounded "oh", F=puckered "oo", G=teeth on lower lip
>   "f/v", H=tongue up "L", X=relaxed rest
> - **Row 4:** thigh_left, shin_left (shoe at the end), thigh_right, shin_right (shoe)
>
> Rules: the head has NO facial features (they are separate parts). Arms and legs are
> straight vertical segments hanging down. Same skin tone on every limb. Leave clear
> whitespace between parts and between a part and its label.

Export the result as a PNG and save it over
`assets/cartoon/source/kinnu_rigsheet.png` (keep a backup of the old one).

> **Why a blank face on the head?** The eyes, eyebrows and mouth are swapped every
> frame for expression and lip-sync, so they must be separate pieces layered onto a
> featureless head.

### Alternative: the AI Studio "Rig Studio" app

Asking AI Studio (Build mode) for the rig sheet may produce an **interactive web app**
that draws the sheet as vector SVGs with a "Download Vector Rig Sheet" button. That
works great too — run it (`npm install && npm run dev`), click the download button,
and feed the downloaded **.svg straight to the slicer** (Step 2). The slicer strips
the text labels from the SVG before rasterizing, so parts can never collide with
their labels. To iterate on the art, just tell the app what to change (e.g. "side
ponytail with pink bow, thicker arms") and download again.

## Step 2 — Slice it into parts (automatic)

```
python scripts/slice_rigsheet.py
# or, for a sheet elsewhere (PNG or SVG):
python scripts/slice_rigsheet.py path/to/sheet.png assets/cartoon/source/parts
python scripts/slice_rigsheet.py path/to/kinnu_character_rigsheet.svg
```

> SVG input needs `pip install playwright` + Chrome/Chromium (used to rasterize at
> 3× resolution). PNG input has no extra requirements.

The slicer **auto-detects** every part — no pixel coordinates to edit — using the
canonical part order (the 26 names above) and these robust rules:

- keys out the flat background,
- finds the 4 tallest content rows (the part rows, not the label rows),
- merges vertically-stacked pieces of one part (e.g. an eye + its highlight dot),
- assigns names left-to-right, treating brows/eyes as left+right **pairs**.

It writes `assets/cartoon/source/parts/<name>.png` plus two verification images next
to that folder:

- **`parts_detected.png`** — the sheet with every detected box + name drawn on it.
  Glance at this first: if a box is wrong, the sheet layout drifted from the spec.
- **`parts_montage.png`** — each cut-out part in a grid.

If a row's blob count is unexpected the slicer prints a `[warn]` and falls back to a
gap-based split — check `parts_detected.png` and, if needed, nudge the sheet (clearer
gaps between parts) and re-run.

## Step 3 — Verify the character assembles

```
python scripts/rig2_calib.py      # renders stand/wave/walk/point poses -> dist/rig2_calib.png
```

Open `dist/rig2_calib.png`. Kinnu should wave, walk and point cleanly. If a limb
pivots oddly, the joint anchors in `src/shiksha_cast/cartoon/rig2.py` (`JOINTS`,
`FACE`, `PIVOT`) may need a small tune to match new proportions.

## Step 4 — Use her in an episode

The cutout engine builds an animated episode from a `scenes.yaml`:

```
python -m shiksha_cast cartoon-build -c <episode-id>
```

Characters that have the separated parts (a `rig2.json`) automatically use the
advanced skeletal rig with 2-bone arms/legs, head nod, eyebrow/eye swaps and 9-shape
lip-sync.

---

## Lip-sync: phoneme-accurate mouths (optional but recommended)

By default the mouth is chosen from audio **loudness** — it opens and closes but can't
tell an "oo" from an "ee". Installing **Rhubarb Lip Sync** (free, local, offline)
upgrades this to real **phoneme visemes** that map 1:1 onto the A–H/X mouths above.

**Install:** download from https://github.com/DanielWolf/rhubarb-lip-sync/releases,
unzip, and either put `rhubarb` on your PATH or set `SHIKSHA_RHUBARB=C:\path\to\rhubarb.exe`.

That's it — the next `cartoon-build` prints `[lipsync] rhubarb (phoneme visemes)` and
uses it. Nothing else changes. To force the old behaviour, set `SHIKSHA_RHUBARB=0`.

- It uses the language-independent **phonetic** recognizer, so **Hinglish** narration
  works without an English transcript.
- If rhubarb ever fails on a clip, that clip silently falls back to amplitude lip-sync
  — a build never breaks because of it.

---

## Which parts exist (reference)

| Row | Parts |
|-----|-------|
| Body | `torso`, `head`, `upper_arm_left`, `forearm_left`, `upper_arm_right`, `forearm_right` |
| Face | `brows_neutral/happy/sad/surprised`, `eyes_open/closed/happy` |
| Mouths | `mouth_A … mouth_H`, `mouth_X` (Preston-Blair / Rhubarb scheme) |
| Legs | `thigh_left`, `shin_left`, `thigh_right`, `shin_right` |

Keep this set and order identical when regenerating the sheet — the slicer and the
engine both rely on it.
