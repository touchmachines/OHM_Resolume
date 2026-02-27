# OHM2Resolume Bridge — Mac Setup

## Step 1: Install Python (one time)

If you don't already have Python installed:

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x"** button
3. Open the downloaded `.pkg` file and follow the installer

## Step 2: Launch the App

1. Unzip the folder
2. Open **Terminal** (Spotlight search "Terminal")
3. Type `chmod +x ` (with a space after), then drag the **`launch.command`** file into the Terminal window and press Enter
4. Now double-click **`launch.command`**
5. If macOS says "can't be opened": **right-click** the file > **Open** > click **Open** again
6. A Terminal window opens — the first time takes ~30 seconds to install dependencies
7. The OHM2Resolume window appears with three status dots

## Step 3: Set Up Resolume

### OSC (for grid buttons + LEDs)

1. Open Resolume
2. Go to **Preferences > OSC**
3. Turn OSC **on**
4. Set **Output address** to `127.0.0.1`
5. Set **Output port** to `7001`
6. Set **Input port** to `7000`

### MIDI (for faders and knobs)

1. Plug in the OHM64 via USB
2. Make sure OHM2Resolume Bridge is running (you should see green dots)
3. In Resolume, go to **Preferences > MIDI**
4. Turn on **"OHM Bridge"** as an input
5. **Leave "Ohm64" off** — our app uses that one

### Map a fader or knob

1. In Resolume, click any parameter you want to control
2. Move the fader or knob on the OHM64
3. It should link automatically

## What You Should See

| In the app window | Meaning |
|---|---|
| **MIDI** — green dot | OHM64 is connected |
| **Bridge** — green dot | Virtual MIDI port is active |
| **OSC** — green dot | Resolume is sending clip state |

## Quick Test

- **Press a grid button** → clip should trigger in Resolume
- **Play a clip in Resolume** → LED should light up on the OHM64
- **Move a fader** → Resolume should respond (after mapping)

## Troubleshooting

- **"Can't be opened" error**: Right-click > Open > Open
- **MIDI dot is red**: OHM64 not detected — check USB cable, click Refresh in the app
- **OSC dot stays red**: Resolume OSC isn't configured — check Step 3 above
- **Faders don't work**: Make sure "OHM Bridge" (not "Ohm64") is enabled in Resolume MIDI preferences
- **App won't start**: Make sure Python is installed (Step 1)

## To Quit

Close the app window, or close the Terminal window.
