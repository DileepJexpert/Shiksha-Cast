"""Generate pilot assets on the GPU: a 2nd full-body character + a living-room
background (no characters). Throwaway spike; outputs feed the slicing/build steps.
"""
from pathlib import Path

from shiksha_cast.imagegen.sdxl import SDXLImageProvider

OUT = Path("dist/_spike_story")
OUT.mkdir(parents=True, exist_ok=True)
BG = Path("assets/cartoon/backgrounds")
BG.mkdir(parents=True, exist_ok=True)

prov = SDXLImageProvider(model_id="stabilityai/stable-diffusion-xl-base-1.0", num_steps=28)

# --- 2nd character: a younger man, FULL BODY (head to feet), plain bg, for slicing ---
man2 = (
    "full body head to feet, young indian man about 28 standing straight facing front, "
    "neat short black hair, clean shaven, blue collared shirt and dark grey trousers, "
    "arms relaxed slightly away from body, 2D cartoon illustration, semi-realistic, "
    "flat cel shading, clean outlines, plain solid light grey background"
)
prov.generate(man2, OUT / "man_young_full.png", width=832, height=1216)
print("saved man_young_full")

# --- living-room background (landscape, NO people) ---
room = (
    "empty indian middle class living room interior, sofa, cushions, low table, "
    "window with curtains, framed picture on wall, potted plant, warm daylight, "
    "2D cartoon illustration background, flat shading, clean, no people, no characters"
)
prov.generate(room, BG / "story_living_room.png", width=1344, height=768)
print("saved story_living_room")

prov.unload()
print("DONE")
