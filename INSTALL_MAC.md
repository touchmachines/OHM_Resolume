# OHM2Resolume Bridge — macOS Test Install

## What This Does

Connects the OHM64 controller to Resolume:
- **8x8 grid buttons** trigger clips via OSC (handled by this app)
- **8x8 grid LEDs** show clip state from Resolume (handled by this app)
- **Faders, knobs, and other controls** pass through as standard MIDI to Resolume via a virtual port called "OHM Bridge"

## Option A: Run from Source

### 1. Install Python 3.11+

```bash
# If you don't have Python, install via Homebrew:
brew install python@3.12
```

### 2. Clone and install

```bash
git clone https://github.com/YOUR_ORG/ohm2resolume-bridge.git
cd ohm2resolume-bridge
pip install -r requirements.txt
```

### 3. Run

```bash
python -m ohm2resolume
```

## Option B: Build a .app Bundle

```bash
cd ohm2resolume-bridge
pip install -r requirements.txt
bash scripts/build_mac.sh
```

The app will be at `dist/OHM2Resolume.app`. Double-click to run.

**Note:** macOS may block it the first time. Go to System Settings > Privacy & Security and click "Open Anyway".

## Resolume Setup

### OSC (for grid button clip triggering + LED feedback)

1. Open Resolume Arena/Avenue
2. Go to **Preferences > OSC**
3. Enable OSC
4. Set **Output** to `127.0.0.1` port `7001` — this sends clip state to our app
5. Set **Input** port to `7000` — this receives clip triggers from our app

### MIDI (for faders/knobs)

1. Plug in the OHM64 via USB (no driver needed on macOS)
2. Launch OHM2Resolume Bridge — it will:
   - Open the OHM64 MIDI ports (you'll see "MIDI: green dot")
   - Create a virtual port called "OHM Bridge" (you'll see "Bridge: green dot")
3. In Resolume, go to **Preferences > MIDI**
4. Enable **"OHM Bridge"** as a MIDI input
5. **Do NOT enable "Ohm64"** — our app owns that port

### Mapping faders/knobs in Resolume

1. In Resolume, click the parameter you want to control (e.g., opacity, effect amount)
2. Move the fader/knob on the OHM64
3. Resolume should see the CC come through "OHM Bridge" and map it

## Verify Everything Works

| Test | Expected |
|------|----------|
| App launches | Window shows MIDI (green), Bridge (green), OSC (red until Resolume sends) |
| Press a grid button | Clip triggers in Resolume (if "Enable clip trigger" is checked) |
| Play a clip in Resolume | Corresponding LED lights up on the OHM64 grid |
| Move a fader on OHM64 | Resolume receives CC via "OHM Bridge" |

## Troubleshooting

- **MIDI dot is red**: OHM64 not detected. Check USB connection, click Refresh.
- **Bridge dot is red**: Virtual port creation failed. This shouldn't happen on macOS (it's automatic). Check console output for errors.
- **OSC dot stays red**: Resolume isn't sending clip state. Check OSC is enabled in Resolume preferences and output port is 7001.
- **Faders don't work in Resolume**: Make sure Resolume's MIDI input is set to "OHM Bridge", not "Ohm64".
- **macOS blocks the app**: System Settings > Privacy & Security > "Open Anyway".
