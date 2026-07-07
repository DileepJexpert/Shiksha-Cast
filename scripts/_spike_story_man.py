"""ART SPIKE (throwaway): can the 4060 + SDXL produce a usable semi-realistic
2D Indian man for the story universe? Generates a few candidates so we can judge
the LOOK and whether it could be sliced into rig parts. Not wired into the engine.
"""
from pathlib import Path

from shiksha_cast.imagegen.sdxl import SDXLImageProvider

OUT = Path("dist/_spike_story")
OUT.mkdir(parents=True, exist_ok=True)

STYLE = (
    "2D cartoon illustration, semi-realistic Indian adult man, flat cel shading, "
    "clean vector outlines, simple soft gradients, full body standing, facing front, "
    "arms slightly away from body, plain solid light-grey background, "
    "moral-story animation style, friendly expression"
)
CANDIDATES = {
    "man_father_kurta": "middle aged man about 40, short black hair, small moustache, "
    "wearing a brown kurta and pajama, " + STYLE,
    "man_young_shirt": "young man about 25, neat black hair, clean shaven, "
    "wearing a blue collared shirt and dark trousers, " + STYLE,
}

# SDXL base for control (turbo ignores guidance). Portrait-ish full body.
prov = SDXLImageProvider(model_id="stabilityai/stable-diffusion-xl-base-1.0", num_steps=28)
for name, prompt in CANDIDATES.items():
    p = OUT / f"{name}.png"
    prov.generate(prompt, p, width=832, height=1216)
    print("saved", p)
prov.unload()
print("DONE")
