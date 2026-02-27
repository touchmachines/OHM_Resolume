"""OHM64 MIDI I/O — auto-detect, LED output, button input."""

import logging
import re
from typing import Callable

import mido

from .mapping import GRID_SIZE, grid_to_note, note_to_grid

log = logging.getLogger(__name__)


class MidiController:
    """Manages MIDI connection to the OHM64."""

    def __init__(
        self,
        device_name_pattern: str = "Ohm64",
        channel: int = 0,
        on_button_press: Callable[[int, int], None] | None = None,
    ):
        self.device_name_pattern = device_name_pattern
        self.channel = channel
        self.on_button_press = on_button_press

        self._input: mido.ports.BaseInput | None = None
        self._output: mido.ports.BaseOutput | None = None
        self._pattern = re.compile(re.escape(device_name_pattern), re.IGNORECASE)

    @property
    def connected(self) -> bool:
        return self._output is not None

    @property
    def port_name(self) -> str | None:
        if self._output:
            return self._output.name
        return None

    def find_device(self) -> str | None:
        """Find the first MIDI port matching the OHM64 name pattern."""
        for name in mido.get_output_names():
            if self._pattern.search(name):
                return name
        return None

    def connect(self) -> bool:
        """Auto-detect and open MIDI ports for the OHM64. Returns True on success."""
        self.disconnect()
        port_name = self.find_device()
        if not port_name:
            log.warning("OHM64 not found in MIDI devices")
            return False

        try:
            self._output = mido.open_output(port_name)
            log.info("Opened MIDI output: %s", port_name)
        except Exception:
            log.exception("Failed to open MIDI output: %s", port_name)
            return False

        # Find matching input port
        for name in mido.get_input_names():
            if self._pattern.search(name):
                try:
                    self._input = mido.open_input(name, callback=self._on_message)
                    log.info("Opened MIDI input: %s", name)
                except Exception:
                    log.exception("Failed to open MIDI input: %s", name)
                break

        return True

    def disconnect(self) -> None:
        """Close MIDI ports."""
        if self._input:
            self._input.close()
            self._input = None
        if self._output:
            self._output.close()
            self._output = None

    def set_led(self, row: int, col: int, velocity: int) -> None:
        """Set a single LED on the OHM64 grid."""
        if not self._output:
            return
        note = grid_to_note(row, col)
        msg = mido.Message("note_on", channel=self.channel, note=note, velocity=velocity)
        try:
            self._output.send(msg)
        except Exception:
            log.exception("Failed to send LED update note=%d vel=%d", note, velocity)

    def all_leds_off(self) -> None:
        """Turn off all 64 LEDs."""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self.set_led(row, col, 0)

    def refresh_leds(self, grid: list[list[int]], led_map: dict[str, int]) -> None:
        """Update all LEDs from a state grid snapshot using the velocity map."""
        from .mapping import resolume_state_to_velocity

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                vel = resolume_state_to_velocity(grid[row][col], led_map)
                self.set_led(row, col, vel)

    def _on_message(self, msg: mido.Message) -> None:
        """Handle incoming MIDI messages from the OHM64."""
        if msg.type == "note_on" and msg.velocity > 0:
            row, col = note_to_grid(msg.note)
            if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                log.debug("Button press: row=%d col=%d note=%d", row, col, msg.note)
                if self.on_button_press:
                    self.on_button_press(row, col)
