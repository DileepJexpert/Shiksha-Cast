from __future__ import annotations

import json
import time
import urllib.request
import uuid


BASE = "http://localhost:8188"


def get_json(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    info = get_json("/object_info")
    ckpts = info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    if not ckpts:
        raise SystemExit("No ComfyUI checkpoints found.")
    ckpt = ckpts[0]
    client_id = str(uuid.uuid4())

    prompt = {
        "3": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": ckpt},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "cute bright Indian kids educational cartoon classroom, colorful, clean, high quality",
                "clip": ["3", 1],
            },
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, watermark, text, distorted",
                "clip": ["3", 1],
            },
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 123456,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["3", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["7", 0], "vae": ["3", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "shiksha_cast_smoke", "images": ["8", 0]},
        },
    }

    queued = post_json("/prompt", {"prompt": prompt, "client_id": client_id})
    prompt_id = queued["prompt_id"]
    print(f"queued {prompt_id} with checkpoint {ckpt}")

    for _ in range(180):
        hist = get_json(f"/history/{prompt_id}")
        if prompt_id in hist:
            outputs = hist[prompt_id].get("outputs", {})
            for node in outputs.values():
                for img in node.get("images", []):
                    print("generated:", img)
                    return
            raise SystemExit("Prompt finished but no image output was reported.")
        time.sleep(1)
    raise SystemExit("Timed out waiting for ComfyUI generation.")


if __name__ == "__main__":
    main()
