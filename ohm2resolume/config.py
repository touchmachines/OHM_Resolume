"""Config loading with sensible defaults."""

import json
import os
from pathlib import Path

DEFAULTS = {
    "osc": {
        "listen_port": 7001,
        "send_port": 7000,
        "send_host": "127.0.0.1",
    },
    "midi": {
        "device_name_pattern": "Ohm64",
        "virtual_port_name": "OHM Bridge",
        "channel": 0,
    },
    "led": {
        "empty": 0,
        "loaded": 32,
        "previewed": 48,
        "playing": 127,
    },
    "app": {
        "poll_interval_ms": 50,
        "enable_clip_trigger": True,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base, returning a new dict."""
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def _config_path() -> Path:
    """Resolve config.json next to the package (or frozen exe)."""
    if getattr(os.sys, "frozen", False):
        # PyInstaller bundle
        base = Path(os.sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "config.json"


def load_config(path: Path | None = None) -> dict:
    """Load config from disk, merged over defaults."""
    path = path or _config_path()
    if path.exists():
        with open(path, "r") as f:
            user = json.load(f)
        return _deep_merge(DEFAULTS, user)
    return DEFAULTS.copy()


def save_config(cfg: dict, path: Path | None = None) -> None:
    """Write config to disk."""
    path = path or _config_path()
    with open(path, "w") as f:
        json.dump(cfg, f, indent=4)
