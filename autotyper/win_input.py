"""Zero-dependency Windows keystroke backend using ctypes + SendInput.

This exists so the app runs on a stock Python install with no `pip install`
step at all. It talks to the Win32 API directly:

* Text is sent with KEYEVENTF_UNICODE, so any character works regardless of
  the user's keyboard layout (no dead keys, no layout translation).
* The whole string is dispatched in a single SendInput call, which is both
  faster and far less likely to interleave with other input than sending one
  key at a time.
* The global stop hotkey uses RegisterHotKey, which needs no elevation and no
  low-level keyboard hook.
"""

from __future__ import annotations

import ctypes
import sys
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional

WINDOWS = sys.platform == "win32"

# --------------------------------------------------------------------------- #
# Win32 structures
# --------------------------------------------------------------------------- #

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_RETURN = 0x0D
VK_F8 = 0x77
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTunion)]


def _key_event(scan: int, flags: int, vk: int = 0) -> INPUT:
    return INPUT(
        type=INPUT_KEYBOARD,
        union=_INPUTunion(
            ki=KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
        ),
    )


class WindowsTypist:
    """Sends keystrokes to the focused window via SendInput."""

    def __init__(self, per_char_delay: float = 0.0) -> None:
        if not WINDOWS:
            raise RuntimeError("The native Windows backend requires Windows.")
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._user32.SendInput.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        )
        self._user32.SendInput.restype = wintypes.UINT
        self.per_char_delay = per_char_delay

    # -- internals ---------------------------------------------------------- #

    def _send(self, events) -> None:
        if not events:
            return
        count = len(events)
        array = (INPUT * count)(*events)
        sent = self._user32.SendInput(count, array, ctypes.sizeof(INPUT))
        if sent != count:
            win_error = getattr(ctypes, "WinError", None)
            if win_error is not None:
                raise win_error(ctypes.get_last_error())
            raise RuntimeError(
                f"SendInput sent {sent} of {count} events. Input may be blocked "
                "by another application running as administrator."
            )

    @staticmethod
    def _char_events(char: str):
        """Key down/up events for one character, handling non-BMP via UTF-16."""
        events = []
        data = char.encode("utf-16-le")
        for i in range(0, len(data), 2):
            code = data[i] | (data[i + 1] << 8)
            events.append(_key_event(code, KEYEVENTF_UNICODE))
            events.append(_key_event(code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
        return events

    # -- public API --------------------------------------------------------- #

    def type_text(self, text: str) -> None:
        if self.per_char_delay > 0:
            for char in text:
                self._send(self._char_events(char))
                time.sleep(self.per_char_delay)
        else:
            events = []
            for char in text:
                events.extend(self._char_events(char))
            self._send(events)

    def press_enter(self) -> None:
        self._send(
            [
                _key_event(0, 0, VK_RETURN),
                _key_event(0, KEYEVENTF_KEYUP, VK_RETURN),
            ]
        )


class WindowsHotkey:
    """Global F8 stop hotkey via RegisterHotKey (no elevation required)."""

    def __init__(self, on_stop: Callable[[], None], vk: int = VK_F8) -> None:
        self._on_stop = on_stop
        self._vk = vk
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._ok = False

    @property
    def available(self) -> bool:
        return WINDOWS

    def start(self) -> bool:
        if not WINDOWS or self._thread is not None:
            return False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(2.0)
        return self._ok

    def _run(self) -> None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._thread_id = kernel32.GetCurrentThreadId()
        hotkey_id = 1
        # RegisterHotKey binds to the calling thread, so the message pump must
        # live on this same thread.
        self._ok = bool(user32.RegisterHotKey(None, hotkey_id, MOD_NOREPEAT, self._vk))
        self._ready.set()
        if not self._ok:
            return
        try:
            msg = wintypes.MSG()
            while not self._stop.is_set():
                got = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if got in (0, -1):
                    break
                if msg.message == WM_HOTKEY:
                    try:
                        self._on_stop()
                    except Exception:
                        pass
        finally:
            user32.UnregisterHotKey(None, hotkey_id)

    def stop(self) -> None:
        self._stop.set()
        if self._thread_id is not None and WINDOWS:
            # Nudge GetMessageW so the loop notices the stop flag.
            ctypes.WinDLL("user32").PostThreadMessageW(self._thread_id, 0x0400, 0, 0)
        self._thread = None
