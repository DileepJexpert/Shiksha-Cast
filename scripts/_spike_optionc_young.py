"""Attempt Option-C source assets for story_young on LOCAL SDXL:
  1. story_young_parts_sheet  (separated animation parts, gaps between)
  2. story_young_side_walk    (side profile walking pose)
  3. a couple of walk-pose attempts (identity will drift - expected)

Honest spike: SDXL is unreliable for clean parts-sheets / consistent walk frames.
Outputs go to dist/_spike_story/ for review before any rigging.
"""
from pathlib import Path

from shiksha_cast.imagegen.sdxl import SDXLImageProvider

OUT = Path("dist/_spike_story")
OUT.mkdir(parents=True, exist_ok=True)

STYLE = ("2D cartoon illustration, semi-realistic Indian young man about 28, neat black "
         "hair, clean shaven, light blue collared shirt, dark grey trousers, brown shoes, "
         "flat cel shading, clean outlines, plain solid white background")

# The important instruction the user asked to include:
SEPARATION = ("character animation model sheet: do NOT draw one whole person. Draw the "
              "body parts SEPARATED with clean empty white space between every part - "
              "head, torso, two upper arms, two forearms with hands, two thighs, two "
              "shins with shoes - laid out in a neat grid, each part fully detached")

prov = SDXLImageProvider(model_id="stabilityai/stable-diffusion-xl-base-1.0", num_steps=30)

prov.generate(f"{SEPARATION}, {STYLE}", OUT / "story_young_parts_sheet.png",
              width=1216, height=832)
print("saved story_young_parts_sheet")

prov.generate(f"side profile view, full body, mid-stride walking pose, facing right, "
              f"{STYLE}", OUT / "story_young_side_walk.png", width=832, height=1216)
print("saved story_young_side_walk")

for i in (1, 4):
    prov.generate(f"full body side profile, walking cycle frame, leg {'forward' if i==1 else 'back'}, "
                  f"facing right, {STYLE}", OUT / f"story_young_walk_{i:03d}.png",
                  width=832, height=1216)
    print(f"saved story_young_walk_{i:03d}")

prov.unload()
print("DONE")
