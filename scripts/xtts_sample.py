"""Standalone XTTS-v2 sample render (runs in the isolated .venv-xtts env).

XTTS-v2 is non-commercial (CPML); use only for a non-monetized channel.
"""
import sys
import time

import torch
from TTS.api import TTS

HINGLISH = (
    "नमस्ते दोस्तों, और welcome back to Katixo KhojLab! आज हम एक बहुत ही मज़ेदार "
    "chapter शुरू कर रहे हैं — House of Hundreds. एक cool idea है: हर बड़ी number का "
    "अपना एक घर होता है, और उस घर के अंदर तीन छोटे-छोटे rooms होते हैं! आज हम 3-digit "
    "numbers के घर के अंदर जाएँगे और मिलेंगे तीन rooms से — hundreds, tens, और ones. "
    "मैं हूँ Mela, तुम्हारी guide. तो चलो, अंदर चलते हैं!"
)

out = sys.argv[1] if len(sys.argv) > 1 else "dist/xtts_slide1.wav"
speaker = sys.argv[2] if len(sys.argv) > 2 else "Ana Florence"

dev = "cuda" if torch.cuda.is_available() else "cpu"
print(f"device={dev}")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(dev)

# Show a few valid built-in speaker names in case the chosen one is invalid.
try:
    names = list(tts.synthesizer.tts_model.speaker_manager.name_to_id.keys())
    print("sample speakers:", names[:8])
    if speaker not in names:
        speaker = names[0]
        print(f"falling back to speaker: {speaker}")
except Exception as e:  # noqa: BLE001
    print("could not list speakers:", e)

t0 = time.time()
tts.tts_to_file(text=HINGLISH, speaker=speaker, language="hi", file_path=out)
print(f"DONE: wrote {out} (speaker={speaker}) in {time.time() - t0:.1f}s wall")
