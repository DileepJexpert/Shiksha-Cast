# Class-wise / Chapter-wise Episodes

Episodes here are mapped to a **specific class and NCERT chapter**, so a student
can find "Class 8, Chapter 5" directly. This is the syllabus-aligned track
(as opposed to `../how-it-works/`, which is curiosity-driven and subject-grouped).

## Layout

```
class-chapter/
├── class-06/
│   └── c06-ch01-food-where-from/      ← one folder per chapter episode
│       ├── script.yaml
│       ├── SLIDES.md
│       └── slides/
├── class-07/
├── class-08/
├── class-09/
└── class-10/
```

## Naming convention

`c<class>-ch<chapter>-<topic>` — e.g. `c08-ch05-coal-and-petroleum`.

- Keep the folder name **unique across the whole `content/` tree** — it becomes
  the episode id used for the build cache (`build/<id>/`) and output
  (`dist/<id>.mp4`).
- Inside: `script.yaml` (always), `SLIDES.md` (slide brief), `slides/` (PNGs).

## Build

Same as any episode — refer to it by folder name:

```
shiksha-cast build -c c08-ch05-coal-and-petroleum
```

No code/config change needed; the pipeline finds it by name anywhere under
`content/`.
