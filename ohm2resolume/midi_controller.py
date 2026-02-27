"""OHM64 MIDI I/O — auto-detect, LED output, button input."""

import logging
import re
import sys
from typing import Callable

import mido

from .mapping import GRID_SIZE, grid_to_note, note_to_grid

log = logging.getLogger(__name__)


class MidiController:
    """Manages MIDI connection to the OHM64."""

    # Notes 0-63 are the 8x8 grid buttons
    _GRID_NOTE_MAX = GRID_SIZE * GRID_SIZE  # 64

    def __init__(
        self,
        device_name_pattern: str = "Ohm64",
        virtual_port_name: str = "OHM Bridge",
        channel: int = 0,
        on_button_press: Callable[[int, int], None] | None = None,
    ):
        self.device_name_pattern = device_name_pattern
        self.virtual_port_name = virtual_port_name
        self.channel = channel
        self.on_button_press = on_button_press

        self._input: mido.ports.BaseInput | None = None
        self._output: mido.ports.BaseOutput | None = None
        self._virtual_output: mido.ports.BaseOutput | None = None
        self._pattern = re.compile(re.escape(device_name_pattern), re.IGNORECASE)

    @property
    def connected(self) -> bool:
        return self._output is not None

    @property
    def virtual_connected(self) -> bool:
        return self._virtual_output is not None

    @property
    def port_name(self) -> str | None:
        if self._output:
            return self._output.name
        return None

    @property
    def virtual_port_name_actual(self) -> str | None:
        if self._virtual_output:
            return self._virtual_output.name
        return None

    def find_device(self) -> str | None:
        """Find the first MIDI port matching the OHM64 name pattern."""
        for name in mido.get_output_names():
            if self._pattern.search(name):
                return name
        return None

    def find_virtual_port(self) -> str | None:
        """Find the loopMIDI virtual port matching virtual_port_name."""
        for name in mido.get_output_names():
            if self.virtual_port_name.lower() in name.lower():
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

        # Open virtual output for MIDI passthrough to Resolume
        self.connect_virtual()

        return True

    def connect_virtual(self) -> bool:
        """Open virtual MIDI port for passthrough.

        macOS: creates a native virtual port via CoreMIDI (no extra software needed).
        Windows: opens an existing loopMIDI port by name.
        """
        self.disconnect_virtual()

        if sys.platform == "darwin":
            # macOS — create a virtual port natively
            try:
                self._virtual_output = mido.open_output(
                    self.virtual_port_name, virtual=True,
                )
                log.info("Created virtual MIDI port: %s", self.virtual_port_name)
                return True
            except Exception:
                log.exception("Failed to create virtual MIDI port: %s", self.virtual_port_name)
                return False
        else:
            # Windows — find an existing loopMIDI port
            vport = self.find_virtual_port()
            if not vport:
                log.warning(
                    "Virtual MIDI port '%s' not found — "
                    "install loopMIDI and create a port named '%s'",
                    self.virtual_port_name, self.virtual_port_name,
                )
                return False
            try:
                self._virtual_output = mido.open_output(vport)
                log.info("Opened virtual MIDI output: %s", vport)
                return True
            except Exception:
                log.exception("Failed to open virtual MIDI output: %s", vport)
                return False

    def disconnect(self) -> None:
        """Close all MIDI ports."""
        if self._input:
            self._input.close()
            self._input = None
        if self._output:
            self._output.close()
            self._output = None
        self.disconnect_virtual()

    def disconnect_virtual(self) -> None:
        """Close the virtual MIDI output port."""
        if self._virtual_output:
            self._virtual_output.close()
            self._virtual_output = None

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

    def _is_grid_note(self, msg: mido.Message) -> bool:
        """Check if message is a note event for the 8x8 grid (notes 0-63)."""
        return msg.type in ("note_on", "note_off") and 0 <= msg.note < self._GRID_NOTE_MAX

    def _forward_to_virtual(self, msg: mido.Message) -> None:
        """Forward a MIDI message to the virtual output port."""
        if not self._virtual_output:
            return
        try:
            self._virtual_output.send(msg)
        except Exception:
            log.exception("Failed to forward MIDI message to virtual port: %s", msg)

    def _on_message(self, msg: mido.Message) -> None:
        """Handle incoming MIDI messages from the OHM64.

        Grid button notes (0-63) are intercepted for our app.
        Everything else is forwarded to the virtual port for Resolume.
        """
        if self._is_grid_note(msg):
            # Grid button — handle internally, don't forward
            if msg.type == "note_on" and msg.velocity > 0:
                row, col = note_to_grid(msg.note)
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    log.debug("Button press: row=%d col=%d note=%d", row, col, msg.note)
                    if self.on_button_press:
                        self.on_button_press(row, col)
        else:
            # Faders, knobs, CCs, non-grid notes — pass through
            self._forward_to_virtual(msg)
