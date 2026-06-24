@echo off
REM Build one chapter into a narrated MP4 from the command line (no browser needed).
REM Usage:  build-video.bat ch06
REM Output: dist\<chapter>.mp4  and  dist\<chapter>.srt
REM Voice is whatever is set in config\channel.yaml (currently Veena / kavya).
cd /d %~dp0
set PYTHONIOENCODING=utf-8
if "%~1"=="" (
    echo Usage: build-video.bat ^<chapter^>   e.g.  build-video.bat ch06
    exit /b 1
)
echo Building %~1 ... (keep this window open; this can take a while on TTS)
python -m shiksha_cast build -c %~1 --force
