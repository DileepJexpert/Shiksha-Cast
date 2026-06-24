@echo off
REM Build a video for EVERY episode that doesn't have one yet.
REM Resumable: re-run anytime; it skips episodes whose dist\<ep>.mp4 already exists,
REM and the per-slide cache means an interrupted episode resumes where it left off.
REM Keep the laptop awake & plugged in; this can run for many hours.
REM Voice = whatever is set in config\channel.yaml (currently Veena).
cd /d %~dp0
set PYTHONIOENCODING=utf-8

for /d %%D in (content\s*) do (
    if exist "dist\%%~nxD.mp4" (
        echo [SKIP] %%~nxD  ^(already built^)
    ) else (
        echo.
        echo ============================================================
        echo  Building %%~nxD
        echo ============================================================
        python -m shiksha_cast build -c %%~nxD
    )
)
echo.
echo ===== ALL EPISODES PROCESSED =====
