@echo off
REM Free the GPU by killing orphaned Veena/XTTS TTS workers left behind by an
REM interrupted build. Double-click this if a build seems stuck or the GPU is
REM "full" between runs. It does NOT touch the backend server or the UI.
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\free_gpu.ps1"
echo.
pause
