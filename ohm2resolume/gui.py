"""Tkinter GUI — status dashboard with 9x8 grid mirror (8 layers + Layer 9)."""

import sys
import tkinter as tk
from tkinter import ttk

from .app import App
from .mapping import GRID_SIZE, NUM_ROWS

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

        # Virtual MIDI status
        tk.Label(bar, text="Bridge:", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self._virt_dot = tk.Canvas(bar, width=12, height=12, bg="#222222", highlightthickness=0)
        self._virt_dot.pack(side=tk.LEFT, padx=(2, 4))
        self._virt_oval = self._virt_dot.create_oval(2, 2, 10, 10, fill="#cc3333")

        self._virt_label = tk.Label(bar, text="Searching...", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10))
        self._virt_label.pack(side=tk.LEFT, padx=(0, 16))

        # OSC status
        tk.Label(bar, text="OSC:", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self._osc_dot = tk.Canvas(bar, width=12, height=12, bg="#222222", highlightthickness=0)
        self._osc_dot.pack(side=tk.LEFT, padx=(2, 4))
        self._osc_oval = self._osc_dot.create_oval(2, 2, 10, 10, fill="#cc3333")

        self._osc_label = tk.Label(bar, text="Waiting...", fg="#aaaaaa", bg="#222222", font=("Helvetica", 10))
        self._osc_label.pack(side=tk.LEFT)

    def _build_grid(self) -> None:
        # Outer frame holds the main grid and the Layer 9 wings
        outer = tk.Frame(self.root, bg="#222222")
        outer.pack(padx=10, pady=10)

        cell_size = 40
        self._cells: list[list[tk.Canvas]] = []

        # --- Left Layer 9 group (4 buttons) ---
        left9 = tk.Frame(outer, bg="#222222")
        left9.pack(side=tk.LEFT, anchor=tk.S, padx=(0, 6))
        tk.Label(
            left9, text="Layer 9", fg="#777777", bg="#222222",
            font=("Helvetica", 9),
        ).pack(pady=(0, 2))
        left9_grid = tk.Frame(left9, bg="#222222")
        left9_grid.pack()

        # --- Main 8x8 grid (center) ---
        center = tk.Frame(outer, bg="#222222")
        center.pack(side=tk.LEFT, pady=(0, 44))
        main_grid = tk.Frame(center, bg="#222222")
        main_grid.pack()

        for row in range(GRID_SIZE):
            layer_num = GRID_SIZE - row
            tk.Label(
                main_grid, text=f"Layer {layer_num}", fg="#777777", bg="#222222",
                font=("Helvetica", 9), anchor=tk.E,
            ).grid(row=row, column=0, padx=(0, 6), pady=1, sticky=tk.E)

            row_cells = []
            for col in range(GRID_SIZE):
                c = tk.Canvas(
                    main_grid,
                    width=cell_size,
                    height=cell_size,
                    bg=STATE_COLORS[0],
                    highlightbackground="#444444",
                    highlightthickness=1,
                )
                c.grid(row=row, column=col + 1, padx=1, pady=1)
                row_cells.append(c)
            self._cells.append(row_cells)

        # --- Right Layer 9 group (4 buttons) ---
        right9 = tk.Frame(outer, bg="#222222")
        right9.pack(side=tk.LEFT, anchor=tk.S, padx=(6, 0), pady=(0, 0))
        tk.Label(
            right9, text="Layer 9", fg="#777777", bg="#222222",
            font=("Helvetica", 9),
        ).pack(pady=(0, 2))
        right9_grid = tk.Frame(right9, bg="#222222")
        right9_grid.pack()

        # Build Layer 9 cells: left 4 in left9_grid, right 4 in right9_grid
        layer9_cells = []
        for col in range(GRID_SIZE):
            parent = left9_grid if col < 4 else right9_grid
            grid_col = col if col < 4 else col - 4
            c = tk.Canvas(
                parent,
                width=cell_size,
                height=cell_size,
                bg=STATE_COLORS[0],
                highlightbackground="#444444",
                highlightthickness=1,
            )
            c.grid(row=0, column=grid_col, padx=1, pady=1)
            layer9_cells.append(c)
        self._cells.append(layer9_cells)

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

        tk.Button(bar, text="?", command=self._on_setup_help, width=2, **btn_style).pack(side=tk.RIGHT)

    # --- Actions ---------------------------------------------------------

    def _on_refresh(self) -> None:
        self.app.refresh()

    def _on_trigger_toggle(self) -> None:
        self.app.enable_clip_trigger = self._trigger_var.get()

    def _on_setup_help(self) -> None:
        """Show a Getting Started dialog."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Getting Started")
        dlg.configure(bg="#222222")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        cfg = self.app.cfg
        vport = cfg["midi"]["virtual_port_name"]
        osc_send = cfg["osc"]["send_port"]
        osc_listen = cfg["osc"]["listen_port"]

        steps = (
            "1. Connect your OHM64 via USB\n"
            "   The MIDI status dot turns green when detected.\n"
            "\n"
            f"2. Install loopMIDI and create a port named \"{vport}\"\n"
            "   This lets faders/knobs pass through to Resolume.\n"
            "   The Bridge status dot turns green when found.\n"
            "   (macOS: the virtual port is created automatically)\n"
            "\n"
            "3. Configure Resolume OSC settings:\n"
            f"   - OSC Input enabled on port {osc_send}\n"
            f"   - OSC Output to 127.0.0.1:{osc_listen}\n"
            "   The OSC status dot turns green when Resolume responds.\n"
            "\n"
            f"4. In Resolume, set MIDI input to \"{vport}\"\n"
            "   This receives fader/knob data from the bridge.\n"
            "\n"
            "5. Click Refresh to re-sync clip states at any time.\n"
            "\n"
            "Grid buttons trigger clips in Resolume layers 1-9.\n"
            "LEDs reflect clip state: off=empty, dim=loaded, blink=playing."
        )

        tk.Label(
            dlg, text="OHM2Resolume Bridge Setup", fg="#ffffff", bg="#222222",
            font=("Helvetica", 12, "bold"),
        ).pack(padx=20, pady=(16, 8))

        tk.Label(
            dlg, text=steps, fg="#cccccc", bg="#222222",
            font=("Consolas", 10), justify=tk.LEFT, anchor=tk.W,
        ).pack(padx=20, pady=(0, 12))

        tk.Button(
            dlg, text="OK", command=dlg.destroy, width=10,
            bg="#444444", fg="#dddddd", activebackground="#555555",
            activeforeground="#ffffff", relief=tk.FLAT,
        ).pack(pady=(0, 16))

    # --- Polling ---------------------------------------------------------

    def _schedule_poll(self) -> None:
        self._poll()
        self.root.after(self._poll_interval, self._schedule_poll)

    def _poll(self) -> None:
        # Update grid colors
        if self.app.clip_state.is_dirty():
            snap = self.app.clip_state.snapshot()
            self.app.clip_state.clear_dirty()
            for row in range(NUM_ROWS):
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

        # Update virtual MIDI port status
        if self.app.midi.virtual_connected:
            self._virt_dot.itemconfig(self._virt_oval, fill="#33cc33")
            self._virt_label.configure(text=self.app.midi.virtual_port_name_actual or "Connected")
        else:
            self._virt_dot.itemconfig(self._virt_oval, fill="#cc3333")
            vname = self.app.midi.virtual_port_name
            if sys.platform == "darwin":
                self._virt_label.configure(text=f"'{vname}' failed")
            else:
                self._virt_label.configure(text=f"Create '{vname}' in loopMIDI")

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
