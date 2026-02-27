#!/usr/bin/env bash
# Build macOS .app bundle via PyInstaller
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Installing build dependencies ==="
pip install pyinstaller

echo "=== Building OHM2Resolume.app ==="
pyinstaller \
    --name "OHM2Resolume" \
    --windowed \
    --onefile \
    --add-data "config.json:." \
    --hidden-import "rtmidi" \
    --hidden-import "rtmidi._rtmidi" \
    --hidden-import "pythonosc" \
    ohm2resolume/__main__.py

echo ""
echo "Build complete: dist/OHM2Resolume.app"
echo ""
echo "To run:  open dist/OHM2Resolume.app"
echo "To distribute: zip -r OHM2Resolume.zip dist/OHM2Resolume.app"
