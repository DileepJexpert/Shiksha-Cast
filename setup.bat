@echo off
REM ============================================================
REM  Shiksha-Cast — one-time local setup (Windows)
REM  Run this ONCE after cloning / pulling. Re-run if deps change.
REM ============================================================
cd /d %~dp0

echo.
echo [1/4] Installing Python package + server + TTS (Parler)...
python -m pip install -e ".[server,tts]"
if errorlevel 1 goto :err

echo.
echo [2/4] Installing UI (React/Vite) dependencies...
pushd ui
call npm install
popd
if errorlevel 1 goto :err

echo.
echo [3/4] Creating Veena (Hinglish) environment .venv-veena ...
if not exist ".venv-veena\Scripts\python.exe" (
    python -m venv .venv-veena --system-site-packages
)
.venv-veena\Scripts\python -m pip install snac bitsandbytes accelerate
if errorlevel 1 goto :err

echo.
echo [4/4] Quick checks...
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
ffmpeg -version >nul 2>&1 && (echo FFmpeg: OK) || (echo FFmpeg: NOT FOUND - install it and add to PATH)

echo.
echo ============================================================
echo  Setup complete. Now run:  run-backend.bat  and  run-frontend.bat
echo ============================================================
goto :eof

:err
echo.
echo *** Setup failed. See the error above. ***
exit /b 1
