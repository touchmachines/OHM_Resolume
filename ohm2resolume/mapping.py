"""Pure mapping functions between OHM64 grid, MIDI notes, and Resolume OSC addresses."""


GRID_SIZE = 8


def grid_to_note(row: int, col: int) -> int:
    """Convert grid position to OHM64 MIDI note number (column-first layout)."""
    return col * GRID_SIZE + row


def note_to_grid(note: int) -> tuple[int, int]:
    """Convert OHM64 MIDI note number to (row, col) grid position."""
    col, row = divmod(note, GRID_SIZE)
    return row, col


def grid_to_osc_path(row: int, col: int) -> str:
    """Convert grid position to Resolume OSC path (1-based indexing).

    Row 0 (top of OHM) = Layer 8 (top of Resolume), Row 7 = Layer 1.
    """
    layer = GRID_SIZE - row
    clip = col + 1
    return f"/composition/layers/{layer}/clips/{clip}/connected"


def grid_to_trigger_path(row: int, col: int) -> str:
    """Convert grid position to Resolume OSC trigger path (1-based)."""
    layer = GRID_SIZE - row
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
    row = GRID_SIZE - layer
    col = clip - 1
    if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
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
