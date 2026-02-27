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
    --hidden-import "rtmidi._rtmidi" ^
    --hidden-import "pythonosc" ^
    --hidden-import "pythonosc.osc_message_builder" ^
    --hidden-import "pythonosc.osc_bundle_builder" ^
    --hidden-import "pythonosc.udp_client" ^
    --hidden-import "pythonosc.dispatcher" ^
    --hidden-import "pythonosc.osc_server" ^
    ohm2resolume\__main__.py

echo Build complete: dist\OHM2Resolume.exe
