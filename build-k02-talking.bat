@echo off
cd /d %~dp0
echo Building moving talking-Kinnu K02 video...
python scripts\make_k02_talking_video.py --fps 24 --host-height 640
echo.
echo Done.
echo Video: dist\k02-star-bridge-counting.talking.mp4
echo Preview frame: build\k02-star-bridge-counting\talking_preview\preview_frame_slide_001.jpg
pause
