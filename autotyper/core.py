"""Core logic for AutoTyper: configuration, string generation and the typing loop.

This module is deliberately free of any GUI or OS-automation imports so that it
can be unit-tested anywhere. The actual keystroke backend is injected, which
also makes the loop testable with a fake typist.
"""

from __future__ import annotations

import random
import string
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

# --------------------------------------------------------------------------- #
# Character sets
# --------------------------------------------------------------------------- #

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?"
SPACE = " "

MIN_INTERVAL = 0.05
MAX_LENGTH = 5000


class CharsetError(ValueError):
    """Raised when a configuration cannot produce any characters."""


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #


@dataclass
class TypingConfig:
    """Everything the user can configure from the UI."""

    length: int = 10
    interval: float = 2.0          # seconds between messages
    start_delay: float = 5.0       # seconds before the first message
    repeat_limit: int = 0          # 0 == unlimited
    press_enter: bool = True

    use_lowercase: bool = True
    use_uppercase: bool = False
    use_digits: bool = True
    use_symbols: bool = False
    use_space: bool = False

    fixed_text: str = ""           # if non-empty, sent verbatim instead of random
    prefix: str = ""
    suffix: str = ""
    add_counter: bool = False      # append " #1", " #2", ...

    def charset(self) -> str:
        pool = ""
        if self.use_lowercase:
            pool += LOWERCASE
        if self.use_uppercase:
            pool += UPPERCASE
        if self.use_digits:
            pool += DIGITS
        if self.use_symbols:
            pool += SYMBOLS
        if self.use_space:
            pool += SPACE
        return pool

    def validate(self) -> None:
        """Raise a descriptive error if the config cannot be run."""
        if not self.fixed_text:
            if self.length < 1:
                raise ValueError("Length must be at least 1 character.")
            if self.length > MAX_LENGTH:
                raise ValueError(f"Length must be {MAX_LENGTH} or fewer characters.")
            if not self.charset():
                raise CharsetError("Select at least one character type.")
        if self.interval < MIN_INTERVAL:
            raise ValueError(f"Interval must be at least {MIN_INTERVAL} seconds.")
        if self.start_delay < 0:
            raise ValueError("Start delay cannot be negative.")
        if self.repeat_limit < 0:
            raise ValueError("Repeat count cannot be negative.")


def build_message(config: TypingConfig, counter: int, rng: Optional[random.Random] = None) -> str:
    """Build the exact string that will be typed for message number `counter`."""
    config.validate()
    if config.fixed_text:
        body = config.fixed_text
    else:
        r = rng or random
        pool = config.charset()
        body = "".join(r.choice(pool) for _ in range(config.length))
    message = f"{config.prefix}{body}{config.suffix}"
    if config.add_counter:
        message = f"{message} #{counter}"
    return message


# --------------------------------------------------------------------------- #
# Typing backend
# --------------------------------------------------------------------------- #


class Typist(Protocol):
    """Minimal keystroke interface so the loop can be tested with a fake."""

    def type_text(self, text: str) -> None: ...

    def press_enter(self) -> None: ...


# --------------------------------------------------------------------------- #
# The worker
# --------------------------------------------------------------------------- #


@dataclass
class TypingWorker:
    """Runs the send loop on a background thread until stopped.

    Callbacks are invoked from the worker thread; the Tk UI marshals them back
    onto the main thread with `after`.
    """

    config: TypingConfig
    typist: Typist
    on_status: Callable[[str], None] = lambda msg: None
    on_sent: Callable[[int, str], None] = lambda count, text: None
    on_finished: Callable[[str], None] = lambda reason: None
    rng: Optional[random.Random] = None

    _stop: threading.Event = field(default_factory=threading.Event, init=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False)
    sent_count: int = field(default=0, init=False)

    # -- lifecycle ---------------------------------------------------------- #

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self.config.validate()
        self._stop.clear()
        self.sent_count = 0
        self._thread = threading.Thread(target=self._run, name="autotyper", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def join(self, timeout: Optional[float] = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    # -- internals ---------------------------------------------------------- #

    def _sleep(self, seconds: float) -> bool:
        """Interruptible sleep. Returns False if a stop was requested."""
        return not self._stop.wait(seconds)

    def _run(self) -> None:
        cfg = self.config
        reason = "Stopped"
        try:
            if cfg.start_delay > 0:
                remaining = cfg.start_delay
                while remaining > 0:
                    self.on_status(
                        f"Starting in {remaining:.0f}s - click your Notepad window now"
                    )
                    step = min(1.0, remaining)
                    if not self._sleep(step):
                        self.on_finished("Stopped before starting")
                        return
                    remaining -= step

            while not self._stop.is_set():
                self.sent_count += 1
                text = build_message(cfg, self.sent_count, self.rng)
                self.typist.type_text(text)
                if self._stop.is_set():
                    break
                if cfg.press_enter:
                    self.typist.press_enter()
                self.on_sent(self.sent_count, text)
                self.on_status(f"Sent {self.sent_count} message(s)")

                if cfg.repeat_limit and self.sent_count >= cfg.repeat_limit:
                    reason = f"Finished - sent {self.sent_count} message(s)"
                    break
                if not self._sleep(cfg.interval):
                    break
            else:
                reason = "Stopped"
        except Exception as exc:  # surfaced in the UI instead of dying silently
            reason = f"Error: {exc}"
        finally:
            if reason == "Stopped":
                reason = f"Stopped after {self.sent_count} message(s)"
            self.on_finished(reason)
