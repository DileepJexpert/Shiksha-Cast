"""Standalone Kokoro-82M English sample (runs in the isolated .venv-kokoro env).

Kokoro (Apache-2.0, 82M) is a crisp, lightweight English TTS that runs real-time
on CPU. American English voices start with 'a' (af_=female, am_=male); British
voices start with 'b'.

Usage: .venv-kokoro/Scripts/python.exe scripts/kokoro_sample.py <voice> <out.wav>
"""
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
OUT = sys.argv[2] if len(sys.argv) > 2 else f"dist/kokoro_{VOICE}.wav"

TEXT = (
    "Hello friends! Kinnu sees a magical star bridge in the night sky. "
    "But oh no, Kinnu got confused while counting! Let's help Kinnu count "
    "from one to ten. One, two, three! Are you ready? Let's go!"
)

lang = VOICE[0] if VOICE else "a"
print(f"loading kokoro (voice={VOICE}, lang={lang})...")
pipe = KPipeline(lang_code=lang)

chunks = []
for _g, _p, audio in pipe(TEXT, voice=VOICE, speed=1.0):
    if audio is None:
        continue
    a = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
    chunks.append(np.asarray(a).squeeze())

arr = np.concatenate(chunks).astype("float32") if chunks else np.zeros(4800, dtype="float32")
sf.write(OUT, arr, 24000)
print(f"DONE {OUT} ({len(arr) / 24000:.1f}s, voice={VOICE})")
