"""Keystroke backend built on pynput, plus a global stop-hotkey listener.

Kept separate from `core` so the logic stays testable on machines without a
display or without pynput installed.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

try:
    from pynput.keyboard import Controller, Key, Listener
    PYNPUT_AVAILABLE = True
except Exception:  # pragma: no cover - depends on the host environment
    Controller = None  # type: ignore[assignment]
    Key = None  # type: ignore[assignment]
    Listener = None  # type: ignore[assignment]
    PYNPUT_AVAILABLE = False


class PynputTypist:
    """Types into whatever window currently has keyboard focus."""

    def __init__(self, per_char_delay: float = 0.0) -> None:
        if not PYNPUT_AVAILABLE:
            raise RuntimeError(
                "pynput is not installed. Run: pip install -r requirements.txt"
            )
        self._keyboard = Controller()
        self.per_char_delay = per_char_delay

    def type_text(self, text: str) -> None:
        if self.per_char_delay > 0:
            for char in text:
                self._keyboard.type(char)
                time.sleep(self.per_char_delay)
        else:
            self._keyboard.type(text)

    def press_enter(self) -> None:
        self._keyboard.press(Key.enter)
        self._keyboard.release(Key.enter)


class HotkeyListener:
    """Listens globally for a single key (default F8) and fires a callback.

    Lets the user stop the typing loop without needing to click back into the
    app window, which matters because the app is typing into another window.
    """

    def __init__(self, on_stop: Callable[[], None], key_name: str = "f8") -> None:
        self._on_stop = on_stop
        self._key_name = key_name
        self._listener: Optional["Listener"] = None

    @property
    def available(self) -> bool:
        return PYNPUT_AVAILABLE

    def start(self) -> bool:
        if not PYNPUT_AVAILABLE or self._listener is not None:
            return False
        target = getattr(Key, self._key_name, None)
        if target is None:
            return False

        def on_press(key):  # pragma: no cover - requires real key events
            if key == target:
                self._on_stop()

        try:
            self._listener = Listener(on_press=on_press)
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception:
            self._listener = None
            return False

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            finally:
                self._listener = None
