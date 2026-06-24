"""Seed the speak-cache manifest for ch06 slides already rendered today (Veena),
so a resumed `build -c ch06` (without --force) skips them. Mirrors speak.py's key.
"""
import datetime
from pathlib import Path

import soundfile as sf

from shiksha_cast.cache import BuildManifest, content_hash
from shiksha_cast.config import load_channel_config, load_script

ROOT = Path(__file__).resolve().parents[1]
cfg = load_channel_config(ROOT)
script = load_script(ROOT / "content" / "ch06")
build_dir = ROOT / "build" / "ch06"
audio_dir = build_dir / "audio"
manifest = BuildManifest(build_dir)

provider_name = "veena"  # matches VeenaTTSProvider.name()
today = datetime.date.today()
seeded = 0
for slide in script.slides:
    out = audio_dir / f"slide_{slide.n:03d}.wav"
    if not out.exists():
        continue
    if datetime.date.fromtimestamp(out.stat().st_mtime) != today:
        continue  # only today's Veena outputs
    voice_desc = slide.voice_description or cfg.voice.description
    key = content_hash(slide.narration, voice_desc, provider_name, str(cfg.voice.sample_rate))
    info = sf.info(str(out))
    dur = info.frames / info.samplerate
    manifest.set("speak", f"{slide.n}:{key}", {
        "output": str(out), "duration": dur, "narration_hash": key,
    })
    seeded += 1
    print(f"seeded slide {slide.n}: {dur:.1f}s")
manifest.save()
print(f"DONE: seeded {seeded} slides")
