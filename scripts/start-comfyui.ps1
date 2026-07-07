$ErrorActionPreference = "Stop"

$composeDir = "C:\dileepkm\Learning\image-generator\backend"
$modelsDir = "C:\dileepkm\Learning\image-generator\media\comfyui\models\checkpoints"

if (!(Test-Path -LiteralPath $composeDir)) {
  throw "Compose directory not found: $composeDir"
}

if (!(Test-Path -LiteralPath $modelsDir)) {
  New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null
}

Write-Host "ComfyUI checkpoint folder:"
Write-Host "  $modelsDir"
Get-ChildItem -LiteralPath $modelsDir -File | Select-Object Name,Length | Format-Table -AutoSize

Write-Host "`nStarting ComfyUI Docker service..."
Push-Location $composeDir
try {
  docker compose up -d comfyui
} finally {
  Pop-Location
}

Write-Host "`nWaiting for http://localhost:8188 ..."
for ($i = 0; $i -lt 60; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:8188" -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
      Write-Host "ComfyUI is reachable: http://localhost:8188"
      exit 0
    }
  } catch {
    Start-Sleep -Seconds 2
  }
}

throw "ComfyUI did not become reachable. Check: docker logs image-generator-comfyui-1"
