$ErrorActionPreference = "Continue"

Write-Host "== GPU =="
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} else {
  Write-Host "nvidia-smi not found"
}

Write-Host "`n== Disk =="
Get-PSDrive -PSProvider FileSystem | Select-Object Name,Free,Used,Root | Format-Table

Write-Host "`n== Python CUDA =="
@'
import importlib.util
mods = ["torch", "diffusers", "transformers", "accelerate", "safetensors"]
for m in mods:
    print(f"{m}: {bool(importlib.util.find_spec(m))}")
if importlib.util.find_spec("torch"):
    import torch
    print("torch:", torch.__version__)
    print("cuda_available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("device:", torch.cuda.get_device_name(0))
'@ | python -

Write-Host "`n== Docker =="
if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker info --format "ServerVersion={{.ServerVersion}} OSType={{.OSType}} Architecture={{.Architecture}}"
  docker ps --format "table {{.Names}}`t{{.Image}}`t{{.Status}}`t{{.Ports}}" | Select-String -Pattern "comfy|NAMES"
} else {
  Write-Host "docker not found"
}

Write-Host "`n== Ollama =="
if (Get-Command ollama -ErrorAction SilentlyContinue) {
  ollama list
} else {
  Write-Host "ollama not found"
}

Write-Host "`n== ComfyUI Models =="
$comfyModels = "C:\dileepkm\Learning\image-generator\media\comfyui\models"
if (Test-Path -LiteralPath $comfyModels) {
  Get-ChildItem -LiteralPath $comfyModels -Recurse -File |
    Where-Object { $_.Extension -in ".safetensors", ".ckpt", ".pt", ".pth", ".gguf" } |
    Select-Object FullName,Length | Format-Table -AutoSize
} else {
  Write-Host "ComfyUI model folder not found: $comfyModels"
}

Write-Host "`n== Hugging Face Cache Highlights =="
$hf = Join-Path $env:USERPROFILE ".cache\huggingface\hub"
if (Test-Path -LiteralPath $hf) {
  Get-ChildItem -LiteralPath $hf -Directory |
    Where-Object { $_.Name -match "sdxl|stable-diffusion-xl|flux|wan|ltx|Kokoro|LivePortrait" } |
    Select-Object Name,FullName | Format-Table -AutoSize
} else {
  Write-Host "No Hugging Face cache found"
}
