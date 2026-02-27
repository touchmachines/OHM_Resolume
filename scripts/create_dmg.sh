#!/usr/bin/env bash
# Wrap dist/OHM2Resolume.app into a drag-to-Applications DMG
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "dist/OHM2Resolume.app" ]; then
    echo "ERROR: dist/OHM2Resolume.app not found."
    echo "Run scripts/build_mac.sh first."
    exit 1
fi

if ! command -v create-dmg &>/dev/null; then
    echo "Installing create-dmg via Homebrew..."
    brew install create-dmg
fi

rm -f OHM2Resolume-Mac.dmg

create-dmg \
    --volname "OHM2Resolume" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "OHM2Resolume.app" 150 190 \
    --app-drop-link 450 190 \
    --no-internet-enable \
    "OHM2Resolume-Mac.dmg" \
    "dist/OHM2Resolume.app"

echo ""
echo "DMG ready: OHM2Resolume-Mac.dmg"
