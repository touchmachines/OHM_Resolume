#!/usr/bin/env bash
# OHM2Resolume Bridge — double-click this file to launch
# First run will install Python dependencies automatically (~30 seconds)

set -euo pipefail
cd "$(dirname "$0")"

echo "========================================"
echo "  OHM2Resolume Bridge"
echo "========================================"
echo ""

# --- Check for Python 3 ---
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ is required but not found."
    echo ""
    echo "Install Python:"
    echo "  1. Go to https://www.python.org/downloads/"
    echo "  2. Download and install Python 3.12+"
    echo "  3. Double-click this file again"
    echo ""
    echo "Press Enter to close..."
    read -r
    exit 1
fi

echo "Using $($PYTHON --version)"

# --- Create virtual environment on first run ---
if [ ! -d ".venv" ]; then
    echo ""
    echo "First run — setting up (this takes ~30 seconds)..."
    echo ""
    $PYTHON -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "Setup complete!"
else
    source .venv/bin/activate
fi

echo ""
echo "Starting OHM2Resolume Bridge..."
echo "(Close this terminal window to quit)"
echo ""

python -m ohm2resolume
