@echo off
cd /d %~dp0
echo Building Kinnu Star Bridge Counting video...
python -m shiksha_cast build -c k02-star-bridge-counting
echo.
echo Creating thumbnail, metadata, short, and package...
python -m shiksha_cast thumb -c k02-star-bridge-counting
python -m shiksha_cast thumbs -c k02-star-bridge-counting
python -m shiksha_cast meta -c k02-star-bridge-counting
python -m shiksha_cast shorts -c k02-star-bridge-counting --start 0 --duration 35 --hook "Count 1 to 10 with Kinnu!"
python -m shiksha_cast package -c k02-star-bridge-counting
echo.
echo Done. Check dist\ and dist\packages\k02-star-bridge-counting
pause
