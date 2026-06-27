@echo off
cd /d %~dp0
echo Building Kinnu Friction video...
python -m shiksha_cast build -c k03-friction
echo.
echo Creating thumbnail and YouTube metadata...
python -m shiksha_cast thumb -c k03-friction
python -m shiksha_cast thumbs -c k03-friction
python -m shiksha_cast meta -c k03-friction
echo.
echo Done. Check dist\k03-friction.mp4 and dist\k03-friction.youtube.md
pause
