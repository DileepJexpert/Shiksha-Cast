import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from shiksha_cast.imagegen.ipadapter import KinnuRemixer
ref = ROOT / "assets/cartoon/source/kinnu_3d_ref.png"
rx = KinnuRemixer()  # SDXL base now
for nm, pr in [("wave","Kinnu waving hello and smiling, standing in a sunny flower garden"),
               ("point","Kinnu pointing to the side with one hand, in a classroom")]:
    t0=time.time()
    rx.generate(str(ref), pr, ROOT/f"dist/_remix2_{nm}.png", ip_scale=0.6)
    print(f"OK {nm} in {time.time()-t0:.0f}s")
print("SMOKE2_DONE")
