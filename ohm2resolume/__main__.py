"""Entry point: python -m ohm2resolume"""

import logging
import sys

from .app import App
from .config import load_config
from .gui import Gui


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
