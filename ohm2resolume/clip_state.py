"""Thread-safe clip state model (9 rows x 8 cols: 8x8 grid + Layer 9)."""

import threading

from .mapping import GRID_SIZE, NUM_ROWS


class ClipStateModel:
    """Holds the current Resolume clip connected-state for a 9x8 grid.

    All methods are thread-safe. The dirty flag lets the GUI know when
    to repaint without constant polling of every cell.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._grid = [[0] * GRID_SIZE for _ in range(NUM_ROWS)]
        self._dirty = False

    def set(self, row: int, col: int, state: int) -> None:
        """Set clip state at (row, col). state is 0-4 per Resolume."""
        with self._lock:
            if self._grid[row][col] != state:
                self._grid[row][col] = state
                self._dirty = True

    def get(self, row: int, col: int) -> int:
        with self._lock:
            return self._grid[row][col]

    def snapshot(self) -> list[list[int]]:
        """Return a copy of the full grid."""
        with self._lock:
            return [row[:] for row in self._grid]

    def is_dirty(self) -> bool:
        with self._lock:
            return self._dirty

    def clear_dirty(self) -> None:
        with self._lock:
            self._dirty = False

    def reset(self) -> None:
        """Clear all states to 0."""
        with self._lock:
            self._grid = [[0] * GRID_SIZE for _ in range(NUM_ROWS)]
            self._dirty = True
