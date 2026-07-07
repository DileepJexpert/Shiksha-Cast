@echo off
cd /d %~dp0
echo Building today's two English Kinnu videos...
python -m shiksha_cast build -c k03-shape-island-english
python -m shiksha_cast thumb -c k03-shape-island-english
python -m shiksha_cast meta -c k03-shape-island-english
python -m shiksha_cast shorts -c k03-shape-island-english --start 0 --duration 35 --hook "Learn Shapes with Kinnu!"
python -m shiksha_cast package -c k03-shape-island-english

python -m shiksha_cast build -c k04-color-balloon-rescue-english
python -m shiksha_cast thumb -c k04-color-balloon-rescue-english
python -m shiksha_cast meta -c k04-color-balloon-rescue-english
python -m shiksha_cast shorts -c k04-color-balloon-rescue-english --start 0 --duration 35 --hook "Learn Colors with Kinnu!"
python -m shiksha_cast package -c k04-color-balloon-rescue-english
echo Done. Check dist\ and dist\packages\
pause
