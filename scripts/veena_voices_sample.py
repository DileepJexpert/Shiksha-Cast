"""Render the SAME Hinglish line in all 4 Veena voices for a clean A/B.
Runs in .venv-veena. Outputs voice_samples/sample_<voice>.wav (24 kHz).
"""
import os
import numpy as np
import soundfile as sf
import torch
from snac import SNAC
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

LINE = ("नमस्ते दोस्तों! ये Katixo Shiksha की आवाज़ है। आज हम science के एक "
        "मज़ेदार सवाल का जवाब ढूँढेंगे। तो चलो, शुरू करते हैं!")
VOICES = ["kavya", "maitri", "agastya", "vinaya"]
OUTDIR = "voice_samples"
os.makedirs(OUTDIR, exist_ok=True)

START_OF_SPEECH_TOKEN = 128257
END_OF_SPEECH_TOKEN = 128258
START_OF_HUMAN_TOKEN = 128259
END_OF_HUMAN_TOKEN = 128260
START_OF_AI_TOKEN = 128261
END_OF_AI_TOKEN = 128262
AUDIO_CODE_BASE_OFFSET = 128266
SR = 24000

quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                           bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
print("loading veena-tts...", flush=True)
model = AutoModelForCausalLM.from_pretrained("maya-research/veena-tts", quantization_config=quant,
                                             device_map="auto", trust_remote_code=True)
tok = AutoTokenizer.from_pretrained("maya-research/veena-tts", trust_remote_code=True)
snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval().cuda()


def decode(snac_tokens):
    dev = next(snac_model.parameters()).device
    lvl = [[], [], []]
    off = [AUDIO_CODE_BASE_OFFSET + i * 4096 for i in range(7)]
    for i in range(0, len(snac_tokens), 7):
        lvl[0].append(snac_tokens[i] - off[0])
        lvl[1].append(snac_tokens[i + 1] - off[1]); lvl[1].append(snac_tokens[i + 4] - off[4])
        lvl[2].append(snac_tokens[i + 2] - off[2]); lvl[2].append(snac_tokens[i + 3] - off[3])
        lvl[2].append(snac_tokens[i + 5] - off[5]); lvl[2].append(snac_tokens[i + 6] - off[6])
    codes = [torch.tensor(c, dtype=torch.int32, device=dev).unsqueeze(0) for c in lvl]
    with torch.no_grad():
        return snac_model.decode(codes).squeeze().clamp(-1, 1).cpu().numpy()


def gen(text, speaker):
    pt = tok.encode(f"<spk_{speaker}> {text}", add_special_tokens=False)
    inp = [START_OF_HUMAN_TOKEN, *pt, END_OF_HUMAN_TOKEN, START_OF_AI_TOKEN, START_OF_SPEECH_TOKEN]
    ids = torch.tensor([inp], device=model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=min(int(len(text) * 1.3) * 7 + 21, 700),
                             do_sample=True, temperature=0.4, top_p=0.9, repetition_penalty=1.05,
                             pad_token_id=tok.pad_token_id,
                             eos_token_id=[END_OF_SPEECH_TOKEN, END_OF_AI_TOKEN])
    g = out[0][len(inp):].tolist()
    st = [t for t in g if AUDIO_CODE_BASE_OFFSET <= t < AUDIO_CODE_BASE_OFFSET + 7 * 4096]
    st = st[: (len(st) // 7) * 7]
    a = decode(st).astype("float32")
    import math
    rms = math.sqrt(float(np.mean(a ** 2))) + 1e-9
    a = a * (10 ** (-18 / 20) / rms)
    pk = float(np.max(np.abs(a))) + 1e-9
    if pk > 10 ** (-1 / 20):
        a = a * (10 ** (-1 / 20) / pk)
    return a


for v in VOICES:
    a = gen(LINE, v)
    out = os.path.join(OUTDIR, f"sample_{v}.wav")
    sf.write(out, a, SR)
    torch.cuda.empty_cache()
    print(f"  {v}: {len(a)/SR:.1f}s -> {out}", flush=True)
print("DONE", flush=True)
