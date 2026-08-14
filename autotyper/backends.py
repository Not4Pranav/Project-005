"""Chooses the best available keystroke backend.

Preference order:
  1. Native Windows (ctypes/SendInput) - no third-party packages needed.
  2. pynput - cross-platform fallback if it happens to be installed.

This keeps the app dependency-free on Windows while still working on Linux or
macOS for development.
"""

from __future__ import annotations

from typing import Optional, Tuple

from autotyper.win_input import WINDOWS, WindowsHotkey, WindowsTypist


def _pynput():
    try:
        from autotyper import keyboard_backend as kb

        if kb.PYNPUT_AVAILABLE:
            return kb
    except Exception:
        pass
    return None


def backend_name() -> str:
    """Human-readable description of the backend that will be used."""
    if WINDOWS:
        return "native Windows (no extra packages)"
    if _pynput() is not None:
        return "pynput"
    return "none available"


def is_available() -> bool:
    return WINDOWS or _pynput() is not None


def create_typist(per_char_delay: float = 0.0):
    if WINDOWS:
        return WindowsTypist(per_char_delay=per_char_delay)
    kb = _pynput()
    if kb is not None:
        return kb.PynputTypist(per_char_delay=per_char_delay)
    raise RuntimeError(
        "No keystroke backend available. On Windows this should never happen; "
        "on Linux/macOS install pynput: pip install pynput"
    )


def create_hotkey(on_stop, key_name: str = "f8"):
    """Return a started-on-demand hotkey listener, or None if unsupported."""
    if WINDOWS:
        return WindowsHotkey(on_stop)
    kb = _pynput()
    if kb is not None:
        return kb.HotkeyListener(on_stop, key_name)
    return None
