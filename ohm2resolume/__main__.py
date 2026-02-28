"""Entry point: python -m ohm2resolume"""

import logging
import sys

# Force mido backend import so PyInstaller includes it in the bundle.
# mido loads backends dynamically via importlib which PyInstaller can't detect.
import mido.backends.rtmidi  # noqa: F401

try:
    from .app import App
    from .config import load_config
    from .gui import Gui
except ImportError:
    from ohm2resolume.app import App
    from ohm2resolume.config import load_config
    from ohm2resolume.gui import Gui


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    cfg = load_config()
    app = App(cfg)
    app.start()

    gui = Gui(app)
    gui.run()


if __name__ == "__main__":
    main()
