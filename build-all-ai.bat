@echo off
REM AI-animate EVERY episode that doesn't have a video yet.
REM Uses `ai-build`: SDXL image per slide + the motion set in config\channel.yaml
REM (kenburns | parallax | static), with per-slide `motion:` overrides honored.
REM Episodes live in category subfolders, so we discover them by finding every
REM script.yaml under content\ (same as build-all.bat).
REM Resumable: re-run anytime; skips episodes whose dist\<ep>.mp4 already exists,
REM and the per-slide image/audio cache resumes an interrupted episode.
REM Keep the laptop awake & plugged in; image+TTS gen is slow on an 8 GB GPU.
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
        echo  AI-building !EP!
        echo ============================================================
        python -m shiksha_cast ai-build -c !EP!
    )
)
echo.
echo ===== ALL EPISODES PROCESSED =====
endlocal
