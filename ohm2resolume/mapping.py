"""Pure mapping functions between OHM64 grid, MIDI notes, and Resolume OSC addresses."""


GRID_SIZE = 8   # columns (and rows for the main 8x8 grid)
NUM_ROWS = 9    # total rows including Layer 9 (extra buttons)

# Layer 9 note mapping: (row=8, col) -> MIDI note
# Buttons are physically interleaved: left-group and right-group alternate
# Physical left-to-right order: 65, 73, 66, 74, 67, 75, 68, 76
_LAYER9_GRID_TO_NOTE: dict[int, int] = {
    0: 65, 1: 73, 2: 66, 3: 74,
    4: 67, 5: 75, 6: 68, 7: 76,
}
_LAYER9_NOTE_TO_COL: dict[int, int] = {v: k for k, v in _LAYER9_GRID_TO_NOTE.items()}
LAYER9_NOTES: frozenset[int] = frozenset(_LAYER9_NOTE_TO_COL.keys())


def grid_to_note(row: int, col: int) -> int:
    """Convert grid position to OHM64 MIDI note number (column-first layout)."""
    if row == 8:
        return _LAYER9_GRID_TO_NOTE[col]
    return col * GRID_SIZE + row


def note_to_grid(note: int) -> tuple[int, int]:
    """Convert OHM64 MIDI note number to (row, col) grid position."""
    if note in _LAYER9_NOTE_TO_COL:
        return 8, _LAYER9_NOTE_TO_COL[note]
    col, row = divmod(note, GRID_SIZE)
    return row, col


def grid_to_osc_path(row: int, col: int) -> str:
    """Convert grid position to Resolume OSC path (1-based indexing).

    Row 0 (top of OHM) = Layer 8 (top of Resolume), Row 7 = Layer 1.
    Row 8 (extra buttons) = Layer 9.
    """
    layer = GRID_SIZE - row if row < 8 else 9
    clip = col + 1
    return f"/composition/layers/{layer}/clips/{clip}/connected"


def grid_to_trigger_path(row: int, col: int) -> str:
    """Convert grid position to Resolume OSC trigger path (1-based)."""
    layer = GRID_SIZE - row if row < 8 else 9
    clip = col + 1
    return f"/composition/layers/{layer}/clips/{clip}/connect"


def osc_path_to_grid(path: str) -> tuple[int, int] | None:
    """Parse a Resolume connected-state OSC path into (row, col).

    Returns None if the path doesn't match the expected pattern.
    """
    parts = path.strip("/").split("/")
    # Expected: composition/layers/{L}/clips/{C}/connected
    if len(parts) != 6:
        return None
    if parts[0] != "composition" or parts[1] != "layers" or parts[3] != "clips" or parts[5] != "connected":
        return None
    try:
        layer = int(parts[2])
        clip = int(parts[4])
    except ValueError:
        return None
    if layer == 9:
        row = 8
    else:
        row = GRID_SIZE - layer
    col = clip - 1
    if not (0 <= row < NUM_ROWS and 0 <= col < GRID_SIZE):
        return None
    return row, col


def resolume_state_to_velocity(state: int, led_map: dict[str, int]) -> int:
    """Convert Resolume clip connected state (0-4) to OHM64 LED velocity."""
    if state == 0:
        return led_map.get("empty", 0)
    elif state == 1:
        return led_map.get("loaded", 32)
    elif state == 2:
        return led_map.get("previewed", 48)
    elif state in (3, 4):
        return led_map.get("playing", 127)
    return 0
