#!/usr/bin/env bash
# Build macOS .app bundle via PyInstaller (--onedir for faster startup)
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Installing build dependencies ==="
pip install pyinstaller

echo "=== Building OHM2Resolume.app ==="
pyinstaller \
    --name "OHM2Resolume" \
    --windowed \
    --onedir \
    --add-data "config.json:." \
    --hidden-import "rtmidi" \
    --hidden-import "rtmidi._rtmidi" \
    --hidden-import "pythonosc" \
    --hidden-import "pythonosc.osc_message_builder" \
    --hidden-import "pythonosc.osc_bundle_builder" \
    --hidden-import "pythonosc.udp_client" \
    --hidden-import "pythonosc.dispatcher" \
    --hidden-import "pythonosc.osc_server" \
    ohm2resolume/__main__.py

echo "=== Ad-hoc code signing ==="
codesign --force --deep --sign - "dist/OHM2Resolume.app"

echo ""
echo "Build complete: dist/OHM2Resolume.app"
echo ""
echo "To run:  open dist/OHM2Resolume.app"
echo "To make a DMG:  bash scripts/create_dmg.sh"
