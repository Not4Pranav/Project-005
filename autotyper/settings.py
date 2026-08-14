"""Persist the user's configuration between runs.

Settings live next to the executable when frozen by PyInstaller, otherwise in
the user's home directory. Any failure to read or write is non-fatal: the app
simply falls back to defaults.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

FILENAME = "autotyper_settings.json"


def settings_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / FILENAME
    return Path(os.path.expanduser("~")) / FILENAME


def load_settings() -> Dict[str, Any]:
    try:
        path = settings_path()
        if path.is_file():
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_settings(data: Dict[str, Any]) -> bool:
    try:
        with open(settings_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        return True
    except Exception:
        return False
