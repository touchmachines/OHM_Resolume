"""Resolume OSC listener and sender."""

import logging
import threading
from typing import Callable

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from .clip_state import ClipStateModel
from .mapping import (
    GRID_SIZE,
    NUM_ROWS,
    grid_to_osc_path,
    grid_to_trigger_path,
    osc_path_to_grid,
    resolume_state_to_velocity,
)

log = logging.getLogger(__name__)


class OscBridge:
    """Manages OSC communication with Resolume."""

    def __init__(
        self,
        clip_state: ClipStateModel,
        listen_port: int = 7001,
        send_host: str = "127.0.0.1",
        send_port: int = 7000,
        led_map: dict[str, int] | None = None,
        on_led_update: Callable[[int, int, int], None] | None = None,
    ):
        self.clip_state = clip_state
        self.listen_port = listen_port
        self.send_host = send_host
        self.send_port = send_port
        self.led_map = led_map or {"empty": 0, "loaded": 32, "previewed": 48, "playing": 127}
        self.on_led_update = on_led_update

        self._client = SimpleUDPClient(send_host, send_port)
        self._server: ThreadingOSCUDPServer | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._received_any = False

    @property
    def connected(self) -> bool:
        """True once we've received at least one OSC message from Resolume."""
        return self._received_any

    def start(self) -> None:
        """Start the OSC listener in a daemon thread."""
        if self._running:
            return

        dispatcher = Dispatcher()
        # Match all clip connected paths (including Layer 9)
        for row in range(NUM_ROWS):
            for col in range(GRID_SIZE):
                path = grid_to_osc_path(row, col)
                dispatcher.map(path, self._handle_connected)

        self._server = ThreadingOSCUDPServer(("0.0.0.0", self.listen_port), dispatcher)
        self._server.socket.setsockopt(__import__('socket').SOL_SOCKET, __import__('socket').SO_REUSEADDR, 1)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self._running = True
        log.info("OSC listener started on port %d", self.listen_port)

    def stop(self) -> None:
        """Stop the OSC listener."""
        if self._server:
            self._server.shutdown()
            self._running = False
            log.info("OSC listener stopped")

    def _handle_connected(self, address: str, *args) -> None:
        """Handle /composition/layers/{L}/clips/{C}/connected messages."""
        pos = osc_path_to_grid(address)
        if pos is None:
            return
        row, col = pos
        state = int(args[0]) if args else 0
        self._received_any = True

        self.clip_state.set(row, col, state)

        velocity = resolume_state_to_velocity(state, self.led_map)
        if self.on_led_update:
            self.on_led_update(row, col, velocity)

        log.debug("OSC %s -> grid(%d,%d) state=%d vel=%d", address, row, col, state, velocity)

    def trigger_clip(self, row: int, col: int) -> None:
        """Send OSC to trigger a clip in Resolume (connect then disconnect)."""
        path = grid_to_trigger_path(row, col)
        self._client.send_message(path, 1)
        self._client.send_message(path, 0)
        log.info("Triggered clip layer=%d clip=%d", row + 1, col + 1)

    def query_all(self) -> None:
        """Ask Resolume to send the state of all clips."""
        for row in range(NUM_ROWS):
            for col in range(GRID_SIZE):
                path = grid_to_osc_path(row, col)
                self._client.send_message(path, "?")
        log.info("Queried all clip states from Resolume")
