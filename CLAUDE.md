# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

OHM2Resolume Bridge — a standalone Python app that connects a Livid Ohm MIDI controller (Ohm64 or OhmRGB/Slim) to Resolume 7+ via OSC. It maps the 8x8 button grid to Resolume layers 1-8 and the 8 extra buttons to Layer 9, reads clip state and lights LEDs accordingly (playing clips blink), and optionally forwards button presses to trigger clips. An auto-poll timer (default 2s) periodically queries Resolume to stay in sync with structural changes like layer reordering.

## Commands

```bash
pip install -r requirements.txt        # Install dependencies
python -m ohm2resolume                  # Run the app
bash scripts/build_mac.sh              # Build macOS .app (requires PyInstaller)
scripts/build_win.bat                  # Build Windows .exe (requires PyInstaller)
```

There is no test suite or linter configured.

## Architecture

Three threads communicate through a shared `ClipStateModel` (thread-safe 9x8 grid with a dirty flag — 8 main rows + Layer 9):

- **Main thread**: Tkinter GUI polls `ClipStateModel` every 50ms via `root.after()`
- **OSC thread**: `ThreadingOSCUDPServer` daemon thread receives clip state from Resolume on port 7001
- **MIDI thread**: `mido` rtmidi callback thread fires on OHM64 button presses

`App` (in `app.py`) is the orchestrator that owns all components and wires callbacks:

```
Resolume ──OSC:7001──→ OscBridge ──→ ClipStateModel ──→ MidiController ──→ OHM64 LEDs
                                          ↓
                                     GUI grid repaint

OHM64 (all MIDI) ──→ MidiController
  ├─ Grid buttons (notes 0-63)        ──→ OscBridge ──OSC:7000──→ Resolume (clip trigger)
  ├─ Extra buttons (notes 65-68,73-76) ──→ OscBridge ──OSC:7000──→ Resolume (Layer 9 trigger)
  └─ Everything else (faders/knobs/CCs) ──→ loopMIDI "OHM Bridge" ──→ Resolume (MIDI mapping)
```

### MIDI Proxy (loopMIDI)

Windows MIDI ports are exclusive — only one app can open a port. The app acts as a MIDI proxy: it reads all input from the OHM64, intercepts grid button presses (notes 0-63) and Layer 9 extra buttons (notes 65-68, 73-76) for OSC clip triggering, and forwards everything else (faders, knobs, CCs) to a loopMIDI virtual port named "OHM Bridge". Resolume reads from "OHM Bridge" for standard MIDI mapping.

**User setup**: Install loopMIDI, create a port named "OHM Bridge", set Resolume's MIDI input to "OHM Bridge".

## Key Mappings

**OHM64 grid is column-first**: `note = col * 8 + row` (note 0 is top-left, note 63 is bottom-right).

**Resolume OSC is 1-based with inverted rows**: OHM row 0 (top) maps to Resolume layer 8 (top), row 7 (bottom) maps to layer 1 (bottom). This matches Resolume's visual layout where layer 8 is on top.

**Layer 9 (extra buttons)**: The OHM64 has 8 extra buttons below the main grid — 4 lower-left (notes 65-68) and 4 lower-right (notes 73-76). These are physically interleaved, so the left-to-right note order is: 65, 73, 66, 74, 67, 75, 68, 76. They map to row 8 (cols 0-7) → Resolume Layer 9, clips 1-8. The GUI renders them as two flanking groups (left/right wings) matching the physical OHM layout. Constants: `GRID_SIZE=8` (columns), `NUM_ROWS=9` (rows including Layer 9).

**Clip states**: 0=empty, 1=loaded, 2=previewed, 3=playing, 4=playing+previewed. These map to LED velocities in `config.json`. Playing clips (3/4) blink on/off; loaded/previewed stay steady.

**LED velocity** meaning depends on the controller model — configured via `led` section in `config.json`:
- **Ohm64**: Single-color (amber). Velocity controls brightness: 0=off, 1-126=varying brightness, 127=full.
- **OhmRGB / OhmRGB Slim**: Multi-color. Velocity selects color: 0=off, 1-3=white, 4-7=cyan, 8-15=magenta, 16-31=red, 32-63=blue, 64-126=yellow, 127=green.

All mapping logic lives in `mapping.py` as pure functions with no I/O.

## Configuration

`config.json` at the repo root. Merged over hardcoded defaults in `config.py` via deep merge. When bundled with PyInstaller, config is resolved from `sys._MEIPASS`.
