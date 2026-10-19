@echo off
echo Building NeuroVision Core executable...
pip install -r requirements.txt
python build.py
echo Done.
pause
