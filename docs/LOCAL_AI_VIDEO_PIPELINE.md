# Local AI Video Pipeline

This is the practical local setup for the current machine:

- GPU: NVIDIA RTX 4060 Laptop, 8 GB VRAM.
- Reliable today: Shiksha-Cast + SDXL-Turbo/SDXL Base + Kokoro + Ollama.
- ComfyUI: running successfully at `http://localhost:8188`, but only SD 1.5 is installed there right now.
- Wan 2.2 and LivePortrait are not installed locally yet.

## Recommended Order

1. **Static slide/frame creation**
   - Use Claude Design or ChatGPT for clean educational slides.
   - Use Shiksha-Cast direct SDXL for local generated backgrounds.

2. **Local ComfyUI starter**
   - Start ComfyUI from `C:\dileepkm\Learning\image-generator\backend`.
   - Use SD 1.5 first because the checkpoint already exists.
   - Add SDXL checkpoint later if you want better still images inside ComfyUI.

3. **Motion**
   - Keep Wan 2.2 on Kaggle until local ComfyUI is stable.
   - Local Wan 2.2 on 8 GB VRAM should be treated as experimental and short-clip only.

4. **Face/lip motion**
   - Add LivePortrait only after ComfyUI is stable.
   - Use it for close-up talking faces, not full-body Kinnu walk cycles.

5. **Final assembly**
   - Use Shiksha-Cast for narration, captions, music bed, and final MP4.

## Current Local Model State

Shiksha-Cast Python cache has:

```text
stabilityai/sdxl-turbo
stabilityai/stable-diffusion-xl-base-1.0
hexgrad/Kokoro-82M
```

ComfyUI model folder has:

```text
C:\dileepkm\Learning\image-generator\media\comfyui\models\checkpoints\v1-5-pruned-emaonly.safetensors
```

Smoke test result:

```text
C:\dileepkm\Learning\image-generator\media\comfyui\output\shiksha_cast_smoke_00001_.png
```

This proves the ComfyUI API can generate on the RTX 4060. The result is only SD 1.5 quality, so it is useful for setup validation, not final Kinnu production art.

Missing for full ComfyUI workflow:

```text
SDXL checkpoint for ComfyUI
Flux model files
Wan 2.2 model files
LivePortrait custom nodes/models
```

## Commands

Check readiness from Shiksha-Cast:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-local-ai-pipeline.ps1
```

Start ComfyUI only:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-comfyui.ps1
```

Open:

```text
http://localhost:8188
```

Run a tiny ComfyUI API generation test:

```powershell
python scripts\comfyui-txt2img-smoke.py
```

## Important Licensing Note

For YouTube/commercial content, check the license of every model and asset.
FLUX.1-dev is not the best default for monetized YouTube because its official model card points to a non-commercial license.
For the channel, prefer commercial-safe models/assets.
