"""Persistent Veena-TTS worker — runs inside .venv-veena.

Protocol (UTF-8, one JSON object per line):
  stdin :  {"text": "...", "speaker": "kavya", "out": "abs/path.wav"}
  stdout:  {"duration": 12.3}            on success
           {"error": "..."}              on failure
Loads the 3B model once (4-bit), then serves requests until stdin closes.
All diagnostics go to stderr so stdout stays a clean protocol channel.
"""
import json
import re
import sys

import numpy as np
import soundfile as sf
import torch
from snac import SNAC
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Devanagari needs UTF-8 across the pipe (Windows defaults to cp1252).
sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


START_OF_SPEECH_TOKEN = 128257
END_OF_SPEECH_TOKEN = 128258
START_OF_HUMAN_TOKEN = 128259
END_OF_HUMAN_TOKEN = 128260
START_OF_AI_TOKEN = 128261
END_OF_AI_TOKEN = 128262
AUDIO_CODE_BASE_OFFSET = 128266
SR = 24000

log("loading veena-tts (4-bit)...")
quant = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    "maya-research/veena-tts", quantization_config=quant,
    device_map="auto", trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained("maya-research/veena-tts", trust_remote_code=True)
snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval().cuda()
log("model loaded.")


def decode_snac_tokens(snac_tokens):
    if not snac_tokens or len(snac_tokens) % 7 != 0:
        return None
    dev = next(snac_model.parameters()).device
    lvl = [[] for _ in range(3)]
    off = [AUDIO_CODE_BASE_OFFSET + i * 4096 for i in range(7)]
    for i in range(0, len(snac_tokens), 7):
        lvl[0].append(snac_tokens[i] - off[0])
        lvl[1].append(snac_tokens[i + 1] - off[1])
        lvl[1].append(snac_tokens[i + 4] - off[4])
        lvl[2].append(snac_tokens[i + 2] - off[2])
        lvl[2].append(snac_tokens[i + 3] - off[3])
        lvl[2].append(snac_tokens[i + 5] - off[5])
        lvl[2].append(snac_tokens[i + 6] - off[6])
    codes = []
    for c in lvl:
        t = torch.tensor(c, dtype=torch.int32, device=dev).unsqueeze(0)
        if torch.any((t < 0) | (t > 4095)):
            raise ValueError("Invalid SNAC token values")
        codes.append(t)
    with torch.no_grad():
        audio_hat = snac_model.decode(codes)
    return audio_hat.squeeze().clamp(-1, 1).cpu().numpy()


def gen_one(text, speaker, temperature=0.4, top_p=0.9):
    prompt_tokens = tokenizer.encode(f"<spk_{speaker}> {text}", add_special_tokens=False)
    input_tokens = [
        START_OF_HUMAN_TOKEN, *prompt_tokens, END_OF_HUMAN_TOKEN,
        START_OF_AI_TOKEN, START_OF_SPEECH_TOKEN,
    ]
    input_ids = torch.tensor([input_tokens], device=model.device)
    max_tokens = min(int(len(text) * 1.3) * 7 + 21, 700)
    with torch.no_grad():
        out = model.generate(
            input_ids, max_new_tokens=max_tokens, do_sample=True,
            temperature=temperature, top_p=top_p, repetition_penalty=1.05,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=[END_OF_SPEECH_TOKEN, END_OF_AI_TOKEN],
        )
    gen = out[0][len(input_tokens):].tolist()
    snac_tokens = [t for t in gen if AUDIO_CODE_BASE_OFFSET <= t < (AUDIO_CODE_BASE_OFFSET + 7 * 4096)]
    if not snac_tokens:
        raise ValueError("No audio tokens generated")
    return decode_snac_tokens(snac_tokens)


def synth(text, speaker, out_path):
    # Veena is trained on short utterances; split to sentences and stitch.
    parts = [p.strip() for p in re.split(r"(?<=[।.!?])\s+", text.strip()) if p.strip()]
    if not parts:
        parts = [text.strip()]
    gap = np.zeros(int(SR * 0.12), dtype="float32")
    chunks = []
    for p in parts:
        a = np.asarray(gen_one(p, speaker), dtype="float32")
        chunks.append(a)
        chunks.append(gap)
    audio = np.concatenate(chunks)
    # Loudness normalize: target ~ -18 dB RMS, peak-limit to -1 dB.
    import math
    rms = math.sqrt(float(np.mean(audio ** 2))) + 1e-9
    audio = audio * (10 ** (-18 / 20) / rms)
    peak = float(np.max(np.abs(audio))) + 1e-9
    if peak > 10 ** (-1 / 20):
        audio = audio * (10 ** (-1 / 20) / peak)
    sf.write(out_path, audio, SR)
    if model.device.type == "cuda":
        torch.cuda.empty_cache()
    return len(audio) / SR


print("READY", flush=True)
# NOTE: use readline() in a while loop, NOT `for line in sys.stdin` — the iterator
# does read-ahead buffering and deadlocks when one request is sent at a time over a
# persistent pipe (it waits to fill its buffer instead of yielding the single line).
while True:
    line = sys.stdin.readline()
    if not line:  # EOF -> parent closed stdin
        break
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        d = synth(req["text"], req.get("speaker", "kavya"), req["out"])
        print(json.dumps({"duration": d}), flush=True)
    except Exception as e:  # noqa: BLE001
        log("ERROR:", repr(e))
        print(json.dumps({"error": str(e)}), flush=True)
