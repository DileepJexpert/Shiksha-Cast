# General Knowledge Episodes

Fun facts, trivia, and "did you know?" episodes — knowledge that is **not** a
step-by-step mechanism walkthrough (those belong in `../how-it-works/`) and is
**not** tied to a specific syllabus chapter (those belong in `../class-chapter/`).

Examples of what fits here: tallest/biggest/fastest records, history bites,
geography facts, inventors & discoveries, "weird but true" science.

## Layout

```
general-knowledge/
└── gk01-<topic>/          ← one folder per episode
    ├── script.yaml
    ├── SLIDES.md
    └── slides/
```

## Naming convention

`gk<nn>-<topic>` — e.g. `gk01-tallest-mountains`. Keep the folder name unique
across the whole `content/` tree (it is the episode id used for `build/<id>/`
and `dist/<id>.mp4`).

## Build

```
shiksha-cast build -c gk01-tallest-mountains
```
