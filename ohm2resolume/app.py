"""Main orchestrator — wires together MIDI, OSC, state model, and GUI."""

import logging
import threading

from .clip_state import ClipStateModel
from .config import load_config, save_config
from .mapping import GRID_SIZE, NUM_ROWS, resolume_state_to_velocity
from .midi_controller import MidiController
from .osc_bridge import OscBridge

log = logging.getLogger(__name__)


class App:
    """Application core that owns all components."""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or load_config()
        self.clip_state = ClipStateModel()

        # Disabled pads — forwarded to virtual port, no OSC, no LED.
        self.disabled_buttons: set[tuple[int, int]] = {
            tuple(b) for b in self.cfg.get("disabled_buttons", [])
            if isinstance(b, (list, tuple)) and len(b) == 2
        }

        self.midi = MidiController(
            device_name_pattern=self.cfg["midi"]["device_name_pattern"],
            virtual_port_name=self.cfg["midi"]["virtual_port_name"],
            channel=self.cfg["midi"]["channel"],
            on_button_press=self._on_button_press,
            on_button_release=self._on_button_release,
            is_disabled=self.is_disabled,
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

        # Auto-poll timer to keep in sync with Resolume (e.g. layer reorder)
        self._auto_poll_interval = self.cfg["app"].get("auto_poll_interval_s", 2)
        self._auto_poll_timer: threading.Timer | None = None

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
        self._start_auto_poll()

    def stop(self) -> None:
        """Shut down all components."""
        self._stop_auto_poll()
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

    def _start_auto_poll(self) -> None:
        """Start periodic full-state query to catch structural changes in Resolume."""
        if self._auto_poll_interval > 0:
            self._auto_poll_tick()

    def _stop_auto_poll(self) -> None:
        if self._auto_poll_timer:
            self._auto_poll_timer.cancel()
            self._auto_poll_timer = None

    def _auto_poll_tick(self) -> None:
        """Query all clip states from Resolume to stay in sync."""
        self.osc.query_all()
        self._auto_poll_timer = threading.Timer(
            self._auto_poll_interval, self._auto_poll_tick
        )
        self._auto_poll_timer.daemon = True
        self._auto_poll_timer.start()

    def _blink_tick(self) -> None:
        """Toggle blink state and update LEDs for playing clips."""
        self._blink_on = not self._blink_on
        if self.midi.connected:
            snap = self.clip_state.snapshot()
            led_map = self.cfg["led"]
            for row in range(NUM_ROWS):
                for col in range(GRID_SIZE):
                    if self.is_disabled(row, col):
                        continue
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
        if self.is_disabled(row, col):
            return
        # Non-playing states get immediate LED update; playing states are handled by blink
        state = self.clip_state.get(row, col)
        if state not in (3, 4):
            self.midi.set_led(row, col, velocity)

    def _on_button_press(self, row: int, col: int) -> None:
        """Called by MidiController when a button is pressed on the OHM64."""
        if self.enable_clip_trigger:
            self.osc.connect_clip(row, col)

    def _on_button_release(self, row: int, col: int) -> None:
        """Called by MidiController when a grid button is released.

        Sending connect=0 unconditionally — Resolume only acts on it for clips
        set to Piano trigger style, so Trigger/Toggle clips are unaffected.
        """
        if self.enable_clip_trigger:
            self.osc.disconnect_clip(row, col)

    def is_disabled(self, row: int, col: int) -> bool:
        return (row, col) in self.disabled_buttons

    def set_disabled(self, row: int, col: int, disabled: bool) -> None:
        """Toggle a pad's disabled state and persist to config.json.

        Disabled pads forward MIDI to the virtual port (for Resolume MIDI
        mapping) and do not receive LED updates from clip state.
        """
        key = (row, col)
        if disabled:
            if key in self.disabled_buttons:
                return
            self.disabled_buttons.add(key)
            # Turn the physical LED off immediately
            if self.midi.connected:
                self.midi.set_led(row, col, 0)
        else:
            if key not in self.disabled_buttons:
                return
            self.disabled_buttons.discard(key)
            # Restore LED from current clip state
            if self.midi.connected:
                state = self.clip_state.get(row, col)
                vel = resolume_state_to_velocity(state, self.cfg["led"])
                self.midi.set_led(row, col, vel)

        # Persist as sorted list-of-lists for deterministic JSON
        self.cfg["disabled_buttons"] = [list(b) for b in sorted(self.disabled_buttons)]
        try:
            save_config(self.cfg)
        except Exception:
            log.exception("Failed to save disabled_buttons to config")
