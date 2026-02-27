@echo off
REM Build Windows exe via PyInstaller
cd /d "%~dp0\.."

pip install pyinstaller

pyinstaller ^
    --name "OHM2Resolume" ^
    --windowed ^
    --onefile ^
    --add-data "config.json;." ^
    --hidden-import "rtmidi" ^
    --hidden-import "pythonosc" ^
    ohm2resolume\__main__.py

echo Build complete: dist\OHM2Resolume.exe
