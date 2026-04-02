# OHM2Resolume Bridge

A standalone app that connects a Livid Ohm MIDI controller (Ohm64 / OhmRGB / OhmRGB Slim) to Resolume 7+ via OSC.

Press a button on the grid, trigger a clip. Play a clip in Resolume, the LED lights up. Faders and knobs pass through for standard MIDI mapping.

## Features

- **8x8 grid** maps to Resolume layers 1-8 with LED feedback
- **Layer 9** via the 8 extra buttons below the grid
- **LED states** reflect clip status — playing clips blink, loaded/previewed stay steady
- **MIDI proxy** forwards faders, knobs, and CCs through a virtual port so Resolume can still use standard MIDI mapping
- **Auto-poll** keeps in sync with Resolume when layers are reordered or clips change
- **Works on macOS and Windows**

## Download

Grab the latest release from the [Releases page](https://github.com/touchmachines/OHM_Resolume/releases) — pre-built binaries for macOS and Windows, no Python required.

## Setup

### Resolume OSC

1. Open Resolume > **Preferences > OSC**
2. Turn OSC **on**
3. Set **Output address** to `127.0.0.1`
4. Set **Output port** to `7001`
5. Set **Input port** to `7000`

### Windows — MIDI proxy via loopMIDI

Windows MIDI ports are exclusive (only one app can open a port), so the bridge acts as a proxy. It reads all input from the OHM64, intercepts grid buttons for OSC clip triggering, and forwards everything else to a virtual port.

1. Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
2. Create a virtual port named **OHM Bridge**
3. In Resolume > **Preferences > MIDI**, enable **OHM Bridge** as input
4. Leave **Ohm64** disabled in Resolume — the bridge uses that port

### macOS — MIDI proxy via IAC Driver

1. Open **Audio MIDI Setup** > **Window > Show MIDI Studio**
2. Double-click **IAC Driver**, check **Device is online**
3. Add a port named **OHM Bridge**
4. In Resolume > **Preferences > MIDI**, enable **OHM Bridge** as input
5. Leave **Ohm64** disabled in Resolume

### Map faders and knobs

1. In Resolume, click any parameter you want to control
2. Move the fader or knob on the OHM64
3. It links automatically

## What you should see

| Status indicator | Meaning |
|---|---|
| **MIDI** green | OHM64 is connected |
| **Bridge** green | Virtual MIDI port is active |
| **OSC** green | Resolume is sending clip state |

## Configuration

Edit `config.json` to customize ports, LED colors, and behavior:

```json
{
    "osc": {
        "listen_port": 7001,
        "send_port": 7000,
        "send_host": "127.0.0.1"
    },
    "midi": {
        "device_name_pattern": "Ohm",
        "virtual_port_name": "OHM Bridge",
        "channel": 0
    },
    "led": {
        "empty": 0,
        "loaded": 4,
        "previewed": 64,
        "playing": 127
    },
    "app": {
        "poll_interval_ms": 50,
        "enable_clip_trigger": true,
        "auto_poll_interval_s": 2
    }
}
```

LED velocity values depend on your controller model:
- **Ohm64**: Single-color (amber). Velocity controls brightness (0=off, 127=full).
- **OhmRGB / OhmRGB Slim**: Multi-color. Velocity selects color (1-3=white, 4-7=cyan, 8-15=magenta, 16-31=red, 32-63=blue, 64-126=yellow, 127=green).

## Running from source

```bash
pip install -r requirements.txt
python -m ohm2resolume
```

## Building

```bash
# macOS
bash scripts/build_mac.sh

# Windows
scripts\build_win.bat
```

Requires [PyInstaller](https://pyinstaller.org/).

## Troubleshooting

- **MIDI dot is red** — OHM64 not detected. Check USB cable, click Refresh in the app.
- **OSC dot stays red** — Resolume OSC isn't configured. Check the setup steps above.
- **Faders don't work** — Make sure **OHM Bridge** (not Ohm64) is enabled in Resolume MIDI preferences.
- **macOS "can't be opened"** — Right-click the app > Open > Open.

## License

[MIT](LICENSE)
