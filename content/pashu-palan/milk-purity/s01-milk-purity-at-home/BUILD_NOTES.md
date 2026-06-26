# Build notes — S01 Milk Purity at Home

This episode is ready for the AI-image video path because `script.yaml` already has narration and `visual_prompt` for every slide.

Recommended commands:

```bash
python -m shiksha_cast ai-build -c s01-milk-purity-at-home
python -m shiksha_cast thumb -c s01-milk-purity-at-home
python -m shiksha_cast meta -c s01-milk-purity-at-home
python -m shiksha_cast package -c s01-milk-purity-at-home
```

Dashboard path:

1. Start backend with `run-backend.bat`.
2. Start frontend with `run-frontend.bat`.
3. Open the dashboard URL.
4. Select `s01-milk-purity-at-home`.
5. Review narration and visual prompts.
6. Choose voice and build video.

Manual slide path:

Use `SLIDES.md` as the design brief. Create 12 slides in Canva, PowerPoint, or Figma, export them as PNG files named `slide_001.png` to `slide_012.png`, and place them in `build/s01-milk-purity-at-home/slides/`.

Then run standard build:

```bash
python -m shiksha_cast build -c s01-milk-purity-at-home
```

The generated video, captions, thumbnail, and package will be created locally under `dist/`.
