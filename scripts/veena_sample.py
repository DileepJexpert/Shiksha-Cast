"""Standalone Veena-TTS sample render (runs in the isolated .venv-veena env).

Veena (maya-research/veena-tts) is Apache-2.0, 3B params, Hindi+English code-switch,
with built-in pro voices (kavya, agastya, maitri, vinaya). 4-bit on an 8 GB GPU.
"""
import sys
import time

import soundfile as sf
import torch
from snac import SNAC
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/veena_slide1.wav"
SPEAKER = sys.argv[2] if len(sys.argv) > 2 else "kavya"

HINGLISH = (
    "नमस्ते दोस्तों, और welcome back to Katixo Shiksha! आज हम एक बहुत ही मज़ेदार "
    "chapter शुरू कर रहे हैं — House of Hundreds. एक cool idea है: हर बड़ी number का "
    "अपना एक घर होता है, और उस घर के अंदर तीन छोटे-छोटे rooms होते हैं! आज हम 3-digit "
    "numbers के घर के अंदर जाएँगे और मिलेंगे तीन rooms से — hundreds, tens, और ones. "
    "मैं हूँ Mela, तुम्हारी guide. तो चलो, अंदर चलते हैं!"
)

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

print("loading veena-tts (4-bit)...")
model = AutoModelForCausalLM.from_pretrained(
    "maya-research/veena-tts",
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained("maya-research/veena-tts", trust_remote_code=True)
snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval().cuda()

START_OF_SPEECH_TOKEN = 128257
END_OF_SPEECH_TOKEN = 128258
START_OF_HUMAN_TOKEN = 128259
END_OF_HUMAN_TOKEN = 128260
START_OF_AI_TOKEN = 128261
END_OF_AI_TOKEN = 128262
AUDIO_CODE_BASE_OFFSET = 128266


def decode_snac_tokens(snac_tokens, snac_model):
    if not snac_tokens or len(snac_tokens) % 7 != 0:
        return None
    snac_device = next(snac_model.parameters()).device
    codes_lvl = [[] for _ in range(3)]
    off = [AUDIO_CODE_BASE_OFFSET + i * 4096 for i in range(7)]
    for i in range(0, len(snac_tokens), 7):
        codes_lvl[0].append(snac_tokens[i] - off[0])
        codes_lvl[1].append(snac_tokens[i + 1] - off[1])
        codes_lvl[1].append(snac_tokens[i + 4] - off[4])
        codes_lvl[2].append(snac_tokens[i + 2] - off[2])
        codes_lvl[2].append(snac_tokens[i + 3] - off[3])
        codes_lvl[2].append(snac_tokens[i + 5] - off[5])
        codes_lvl[2].append(snac_tokens[i + 6] - off[6])
    hierarchical_codes = []
    for lvl in codes_lvl:
        t = torch.tensor(lvl, dtype=torch.int32, device=snac_device).unsqueeze(0)
        if torch.any((t < 0) | (t > 4095)):
            raise ValueError("Invalid SNAC token values")
        hierarchical_codes.append(t)
    with torch.no_grad():
        audio_hat = snac_model.decode(hierarchical_codes)
    return audio_hat.squeeze().clamp(-1, 1).cpu().numpy()


def generate_speech(text, speaker="kavya", temperature=0.4, top_p=0.9):
    prompt = f"<spk_{speaker}> {text}"
    prompt_tokens = tokenizer.encode(prompt, add_special_tokens=False)
    input_tokens = [
        START_OF_HUMAN_TOKEN, *prompt_tokens, END_OF_HUMAN_TOKEN,
        START_OF_AI_TOKEN, START_OF_SPEECH_TOKEN,
    ]
    input_ids = torch.tensor([input_tokens], device=model.device)
    max_tokens = min(int(len(text) * 1.3) * 7 + 21, 700)
    with torch.no_grad():
        output = model.generate(
            input_ids, max_new_tokens=max_tokens, do_sample=True,
            temperature=temperature, top_p=top_p, repetition_penalty=1.05,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=[END_OF_SPEECH_TOKEN, END_OF_AI_TOKEN],
        )
    generated_ids = output[0][len(input_tokens):].tolist()
    snac_tokens = [
        t for t in generated_ids
        if AUDIO_CODE_BASE_OFFSET <= t < (AUDIO_CODE_BASE_OFFSET + 7 * 4096)
    ]
    if not snac_tokens:
        raise ValueError("No audio tokens generated")
    return decode_snac_tokens(snac_tokens, snac_model)


t0 = time.time()
# Veena is trained on shorter utterances; split into sentences and stitch for stability.
import re
import numpy as np

parts = [p.strip() for p in re.split(r'(?<=[।.!?])\s+', HINGLISH.strip()) if p.strip()]
gap = np.zeros(int(24000 * 0.12), dtype="float32")
chunks = []
for i, part in enumerate(parts, 1):
    a = generate_speech(part, speaker=SPEAKER)
    chunks.append(np.asarray(a, dtype="float32"))
    chunks.append(gap)
    print(f"  chunk {i}/{len(parts)}: {len(a)/24000:.1f}s")
audio = np.concatenate(chunks)
sf.write(OUT, audio, 24000)
print(f"DONE: {OUT} ({len(audio)/24000:.1f}s, speaker={SPEAKER}) in {time.time()-t0:.1f}s wall")
