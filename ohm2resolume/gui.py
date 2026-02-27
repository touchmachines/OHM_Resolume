"""Tkinter GUI — status dashboard with 8x8 grid mirror."""

import tkinter as tk
from tkinter import ttk

from .app import App
from .mapping import GRID_SIZE

# Colors for clip states
STATE_COLORS = {
    0: "#1a1a1a",   # empty — dark
    1: "#2a4a2a",   # loaded — dim green
    2: "#6a6a2a",   # previewed — amber
    3: "#00cc44",   # playing — bright green
    4: "#00cc44",   # playing + previewed — bright green
}


class Gui:
    """Tkinter-based status dashboard."""

    def __init__(self, app: App):
        self.app = app
        self.root = tk.Tk()
        self.root.title("OHM2Resolume Bridge")
        self.root.resizable(False, False)
        self.root.configure(bg="#222222")

        self._build_status_bar()
        self._build_grid()
        self._build_controls()

        self._poll_interval = app.cfg["app"]["poll_interval_ms"]
        self._schedule_poll()

    # --- Layout ----------------------------------------------------------

    def _build_status_bar(self) -> None:
        bar = tk.Frame(self.root, bg="#222222")
        bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        # MIDI status
        tk.Label(bar, text="MIDI:", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self._midi_dot = tk.Canvas(bar, width=12, height=12, bg="#222222", highlightthickness=0)
        self._midi_dot.pack(side=tk.LEFT, padx=(2, 4))
        self._midi_oval = self._midi_dot.create_oval(2, 2, 10, 10, fill="#cc3333")

        self._midi_label = tk.Label(bar, text="Searching...", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10))
        self._midi_label.pack(side=tk.LEFT, padx=(0, 16))

        # OSC status
        tk.Label(bar, text="OSC:", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self._osc_dot = tk.Canvas(bar, width=12, height=12, bg="#222222", highlightthickness=0)
        self._osc_dot.pack(side=tk.LEFT, padx=(2, 4))
        self._osc_oval = self._osc_dot.create_oval(2, 2, 10, 10, fill="#cc3333")

        self._osc_label = tk.Label(bar, text="Waiting...", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10))
        self._osc_label.pack(side=tk.LEFT)

    def _build_grid(self) -> None:
        frame = tk.Frame(self.root, bg="#222222")
        frame.pack(padx=10, pady=10)

        self._cells: list[list[tk.Canvas]] = []
        cell_size = 40
        for row in range(GRID_SIZE):
            row_cells = []
            for col in range(GRID_SIZE):
                c = tk.Canvas(
                    frame,
                    width=cell_size,
                    height=cell_size,
                    bg=STATE_COLORS[0],
                    highlightbackground="#444444",
                    highlightthickness=1,
                )
                c.grid(row=row, column=col, padx=1, pady=1)
                row_cells.append(c)
            self._cells.append(row_cells)

    def _build_controls(self) -> None:
        bar = tk.Frame(self.root, bg="#222222")
        bar.pack(fill=tk.X, padx=10, pady=(0, 10))

        btn_style = {"bg": "#444444", "fg": "#dddddd", "activebackground": "#555555",
                      "activeforeground": "#ffffff", "relief": tk.FLAT, "padx": 8, "pady": 4}

        tk.Button(bar, text="Refresh", command=self._on_refresh, **btn_style).pack(side=tk.LEFT, padx=(0, 8))

        self._trigger_var = tk.BooleanVar(value=self.app.enable_clip_trigger)
        self._trigger_cb = tk.Checkbutton(
            bar,
            text="Enable clip trigger",
            variable=self._trigger_var,
            command=self._on_trigger_toggle,
            bg="#222222",
            fg="#aaaaaa",
            selectcolor="#333333",
            activebackground="#222222",
            activeforeground="#aaaaaa",
        )
        self._trigger_cb.pack(side=tk.LEFT)

    # --- Actions ---------------------------------------------------------

    def _on_refresh(self) -> None:
        self.app.refresh()

    def _on_trigger_toggle(self) -> None:
        self.app.enable_clip_trigger = self._trigger_var.get()

    # --- Polling ---------------------------------------------------------

    def _schedule_poll(self) -> None:
        self._poll()
        self.root.after(self._poll_interval, self._schedule_poll)

    def _poll(self) -> None:
        # Update grid colors
        if self.app.clip_state.is_dirty():
            snap = self.app.clip_state.snapshot()
            self.app.clip_state.clear_dirty()
            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE):
                    color = STATE_COLORS.get(snap[row][col], STATE_COLORS[0])
                    self._cells[row][col].configure(bg=color)

        # Update MIDI status
        if self.app.midi.connected:
            self._midi_dot.itemconfig(self._midi_oval, fill="#33cc33")
            self._midi_label.configure(text=self.app.midi.port_name or "Connected")
        else:
            self._midi_dot.itemconfig(self._midi_oval, fill="#cc3333")
            self._midi_label.configure(text="Searching for OHM64...")

        # Update OSC status
        if self.app.osc.connected:
            self._osc_dot.itemconfig(self._osc_oval, fill="#33cc33")
            self._osc_label.configure(text=f"Receiving (port {self.app.osc.listen_port})")
        else:
            self._osc_dot.itemconfig(self._osc_oval, fill="#cc3333")
            self._osc_label.configure(text=f"Listening on port {self.app.osc.listen_port}")

    # --- Run -------------------------------------------------------------

    def run(self) -> None:
        """Start the Tkinter main loop. Blocks until window is closed."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self) -> None:
        self.app.stop()
        self.root.destroy()
