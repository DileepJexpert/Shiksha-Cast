# Kill orphaned Shiksha-Cast TTS workers that can keep holding GPU VRAM after an
# interrupted or crashed build. SAFE: only targets python processes running the
# Veena worker or living inside this project's .venv-veena / .venv-xtts — it does
# NOT touch the backend server, the UI, or unrelated python.
$ErrorActionPreference = 'SilentlyContinue'

function Show-Gpu($label) {
    Write-Host "GPU ${label}:" -ForegroundColor Cyan
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
}

Show-Gpu 'before'

$targets = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
    $_.CommandLine -and (
        $_.CommandLine -like '*veena_worker.py*' -or
        $_.CommandLine -like '*\.venv-veena\*' -or
        $_.CommandLine -like '*\.venv-xtts\*'
    )
}

if (-not $targets) {
    Write-Host "No stray TTS workers found." -ForegroundColor Green
} else {
    foreach ($p in $targets) {
        $cmd = $p.CommandLine
        $short = if ($cmd.Length -gt 90) { $cmd.Substring(0, 90) + '...' } else { $cmd }
        Write-Host ("Killing PID {0}: {1}" -f $p.ProcessId, $short) -ForegroundColor Yellow
        Stop-Process -Id $p.ProcessId -Force
    }
    Start-Sleep -Seconds 2
    Show-Gpu 'after'
}
