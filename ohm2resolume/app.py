"""Main orchestrator — wires together MIDI, OSC, state model, and GUI."""

import logging
import threading

from .clip_state import ClipStateModel
from .config import load_config
from .mapping import GRID_SIZE, resolume_state_to_velocity
from .midi_controller import MidiController
from .osc_bridge import OscBridge

log = logging.getLogger(__name__)


class App:
    """Application core that owns all components."""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or load_config()
        self.clip_state = ClipStateModel()

        self.midi = MidiController(
            device_name_pattern=self.cfg["midi"]["device_name_pattern"],
            virtual_port_name=self.cfg["midi"]["virtual_port_name"],
            channel=self.cfg["midi"]["channel"],
            on_button_press=self._on_button_press,
        )

        self.osc = OscBridge(
            clip_state=self.clip_state,
            listen_port=self.cfg["osc"]["listen_port"],
            send_host=self.cfg["osc"]["send_host"],
            send_port=self.cfg["osc"]["send_port"],
            led_map=self.cfg["led"],
            on_led_update=self._on_led_update,
        )

        self.enable_clip_trigger = self.cfg["app"]["enable_clip_trigger"]

        # Blink state for playing clips
        self._blink_on = True
        self._blink_timer: threading.Timer | None = None
        self._blink_interval = 0.2  # seconds

    def start(self) -> None:
        """Start OSC listener and attempt MIDI connection."""
        self.osc.start()
        self.midi.connect()
        if self.midi.connected:
            self.midi.all_leds_off()
            log.info("MIDI connected to %s", self.midi.port_name)
        else:
            log.info("OHM64 not found — will retry on refresh")
        self._start_blink()

    def stop(self) -> None:
        """Shut down all components."""
        self._stop_blink()
        if self.midi.connected:
            self.midi.all_leds_off()
            self.midi.disconnect()
        self.osc.stop()

    def refresh(self) -> None:
        """Re-query Resolume and reconnect MIDI if needed."""
        if not self.midi.connected:
            self.midi.connect()
            if self.midi.connected:
                log.info("MIDI reconnected to %s", self.midi.port_name)

        if not self.midi.virtual_connected:
            self.midi.connect_virtual()
            if self.midi.virtual_connected:
                log.info("Virtual MIDI reconnected to %s", self.midi.virtual_port_name_actual)

        self.osc.query_all()

    def _start_blink(self) -> None:
        """Start the blink timer loop."""
        self._blink_tick()

    def _stop_blink(self) -> None:
        if self._blink_timer:
            self._blink_timer.cancel()
            self._blink_timer = None

    def _blink_tick(self) -> None:
        """Toggle blink state and update LEDs for playing clips."""
        self._blink_on = not self._blink_on
        if self.midi.connected:
            snap = self.clip_state.snapshot()
            led_map = self.cfg["led"]
            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE):
                    state = snap[row][col]
                    if state in (3, 4):
                        # Playing: blink between full and off
                        vel = led_map.get("playing", 127) if self._blink_on else 0
                        self.midi.set_led(row, col, vel)
                    elif state in (1, 2):
                        # Loaded/previewed: steady on
                        vel = resolume_state_to_velocity(state, led_map)
                        self.midi.set_led(row, col, vel)

        self._blink_timer = threading.Timer(self._blink_interval, self._blink_tick)
        self._blink_timer.daemon = True
        self._blink_timer.start()

    def _on_led_update(self, row: int, col: int, velocity: int) -> None:
        """Called by OscBridge when a clip state changes."""
        # Non-playing states get immediate LED update; playing states are handled by blink
        state = self.clip_state.get(row, col)
        if state not in (3, 4):
            self.midi.set_led(row, col, velocity)

    def _on_button_press(self, row: int, col: int) -> None:
        """Called by MidiController when a button is pressed on the OHM64."""
        if self.enable_clip_trigger:
            self.osc.trigger_clip(row, col)
            log.info("Button press -> trigger layer=%d clip=%d", row + 1, col + 1)
