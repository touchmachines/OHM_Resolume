#!/usr/bin/env bash
# Package a distributable zip for macOS testers (run from any OS)
set -euo pipefail

cd "$(dirname "$0")/.."

NAME="OHM2Resolume-Mac"
OUTDIR="dist"
STAGING="$OUTDIR/$NAME"

rm -rf "$STAGING" "$OUTDIR/$NAME.zip"
mkdir -p "$STAGING/ohm2resolume"

# Copy app source
cp ohm2resolume/*.py "$STAGING/ohm2resolume/"
cp requirements.txt  "$STAGING/"
cp config.json       "$STAGING/"
cp launch.command    "$STAGING/"
cp INSTALL_MAC.md    "$STAGING/README.md"

# Ensure launch.command is executable (git preserves this)
chmod +x "$STAGING/launch.command"

# Create zip
cd "$OUTDIR"
zip -r "$NAME.zip" "$NAME"
cd ..

rm -rf "$STAGING"

echo ""
echo "Package ready: $OUTDIR/$NAME.zip"
echo "Upload to Dropbox and share the link."
