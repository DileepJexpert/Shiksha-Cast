@echo off
cd /d %~dp0
echo Building k10-kinnu-missing-picnic-basket...
python -m shiksha_cast build -c k10-kinnu-missing-picnic-basket
python -m shiksha_cast thumb -c k10-kinnu-missing-picnic-basket
python -m shiksha_cast meta -c k10-kinnu-missing-picnic-basket
python -m shiksha_cast shorts -c k10-kinnu-missing-picnic-basket --start 0 --duration 45 --hook "Kinnu lost her picnic basket!"
python -m shiksha_cast package -c k10-kinnu-missing-picnic-basket
echo Done. Check dist\ and dist\packages\
pause
