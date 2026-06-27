"""Persistent Kokoro-82M English TTS worker — runs inside .venv-kokoro (Python 3.11).

Kokoro (Apache-2.0, 82M) needs its own venv because misaki/spacy have no wheels for
the main env's Python. We run it out-of-process over a one-JSON-per-line protocol,
like the Veena worker.

Protocol (UTF-8):
  stdin : {"text": "...", "voice": "af_heart", "out": "abs/path.wav"}
  stdout: {"duration": 12.3}   on success  |  {"error": "..."}  on failure
Loads KPipeline once, serves until stdin closes. Diagnostics -> stderr only.
"""
import json
import math
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

SR = 24000


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# A pipeline is tied to a language pack (first letter of the voice: 'a'=US, 'b'=UK).
# Build lazily and cache per language so we can switch voices without reloading.
_pipes: dict[str, KPipeline] = {}


def pipe_for(voice: str) -> KPipeline:
    lang = voice[0] if voice else "a"
    if lang not in _pipes:
        _pipes[lang] = KPipeline(lang_code=lang)
    return _pipes[lang]


log("loading kokoro-82M...")
pipe_for("af_heart")  # warm up default American English
log("kokoro loaded.")


def synth(text: str, voice: str, out_path: str) -> float:
    pipe = pipe_for(voice)
    chunks = []
    for _g, _p, audio in pipe(text, voice=voice, speed=1.0):
        if audio is None:
            continue
        a = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
        chunks.append(np.asarray(a).squeeze())
    if chunks:
        audio = np.concatenate(chunks).astype("float32")
    else:
        audio = np.zeros(int(SR * 0.2), dtype="float32")
    # Loudness normalize: ~ -16 dB RMS, peak-limit to -1 dB (punchy for kids content,
    # louder than the old Veena clips which mixed down to ~ -26 dB).
    rms = math.sqrt(float(np.mean(audio ** 2))) + 1e-9
    audio = audio * (10 ** (-16 / 20) / rms)
    peak = float(np.max(np.abs(audio))) + 1e-9
    if peak > 10 ** (-1 / 20):
        audio = audio * (10 ** (-1 / 20) / peak)
    sf.write(out_path, audio, SR)
    return len(audio) / SR


print("READY", flush=True)
# readline() loop (NOT `for line in sys.stdin`) to avoid read-ahead buffering deadlock.
while True:
    line = sys.stdin.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        d = synth(req["text"], req.get("voice", "af_heart"), req["out"])
        print(json.dumps({"duration": d}), flush=True)
    except Exception as e:  # noqa: BLE001
        log("ERROR:", repr(e))
        print(json.dumps({"error": str(e)}), flush=True)
