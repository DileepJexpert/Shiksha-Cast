@echo off
REM Build a video for EVERY episode that doesn't have one yet.
REM Episodes live in category subfolders (e.g.
REM   content\how-it-works\technology\s02-wifi), so we discover them by
REM   finding every script.yaml under content\ rather than globbing top-level.
REM Resumable: re-run anytime; it skips episodes whose dist\<ep>.mp4 already exists,
REM and the per-slide cache means an interrupted episode resumes where it left off.
REM Keep the laptop awake & plugged in; this can run for many hours.
REM Voice = whatever is set in config\channel.yaml (currently Veena).
cd /d %~dp0
set PYTHONIOENCODING=utf-8
setlocal enabledelayedexpansion

for /f "delims=" %%F in ('dir /s /b /a-d content\script.yaml 2^>nul') do (
    REM %%~dpF = ...\<episode>\  -> take the folder name as the episode id
    for %%D in ("%%~dpF.") do set "EP=%%~nxD"
    if exist "dist\!EP!.mp4" (
        echo [SKIP] !EP!  ^(already built^)
    ) else (
        echo.
        echo ============================================================
        echo  Building !EP!
        echo ============================================================
        python -m shiksha_cast build -c !EP!
    )
    REM Publishing assets (thumbnail + YouTube metadata). Cheap, only need the
    REM script; generate once and skip if already present (keeps re-runs fast).
    if not exist "dist\!EP!.thumb.png" python -m shiksha_cast thumb -c !EP!
    if not exist "dist\!EP!.youtube.md" python -m shiksha_cast meta -c !EP!
)
echo.
echo ===== ALL EPISODES PROCESSED ^(video + thumbnail + metadata^) =====
endlocal
