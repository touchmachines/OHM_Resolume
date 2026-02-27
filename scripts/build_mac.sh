#!/usr/bin/env bash
# Build macOS .app bundle via PyInstaller
set -euo pipefail

cd "$(dirname "$0")/.."

pip install pyinstaller

pyinstaller \
    --name "OHM2Resolume" \
    --windowed \
    --onefile \
    --add-data "config.json:." \
    --hidden-import "rtmidi" \
    --hidden-import "pythonosc" \
    ohm2resolume/__main__.py

echo "Build complete: dist/OHM2Resolume.app"
