import random
import threading
import time

import pytest

from autotyper.core import (
    DIGITS,
    LOWERCASE,
    SYMBOLS,
    UPPERCASE,
    CharsetError,
    TypingConfig,
    TypingWorker,
    build_message,
)


class FakeTypist:
    """Records keystrokes instead of sending them to the OS."""

    def __init__(self):
        self.actions = []
        self.lock = threading.Lock()

    def type_text(self, text):
        with self.lock:
            self.actions.append(("text", text))

    def press_enter(self):
        with self.lock:
            self.actions.append(("enter", None))

    def snapshot(self):
        with self.lock:
            return list(self.actions)


# --- message building ------------------------------------------------------ #


def test_length_is_respected():
    cfg = TypingConfig(length=25)
    assert len(build_message(cfg, 1)) == 25


def test_only_selected_charsets_are_used():
    cfg = TypingConfig(length=400, use_lowercase=False, use_digits=True)
    msg = build_message(cfg, 1)
    assert set(msg) <= set(DIGITS)

    cfg = TypingConfig(length=400, use_lowercase=True, use_digits=False,
                       use_uppercase=True, use_symbols=True)
    msg = build_message(cfg, 1)
    assert set(msg) <= set(LOWERCASE + UPPERCASE + SYMBOLS)
    assert not set(msg) & set(DIGITS)


def test_no_charset_selected_raises():
    cfg = TypingConfig(use_lowercase=False, use_uppercase=False,
                       use_digits=False, use_symbols=False, use_space=False)
    with pytest.raises(CharsetError):
        build_message(cfg, 1)


def test_fixed_text_overrides_random_generation():
    cfg = TypingConfig(fixed_text="buy milk", length=99)
    assert build_message(cfg, 1) == "buy milk"


def test_prefix_suffix_and_counter():
    cfg = TypingConfig(fixed_text="task", prefix="[", suffix="]", add_counter=True)
    assert build_message(cfg, 7) == "[task] #7"


def test_generation_is_deterministic_with_seeded_rng():
    cfg = TypingConfig(length=16)
    a = build_message(cfg, 1, random.Random(42))
    b = build_message(cfg, 1, random.Random(42))
    assert a == b


@pytest.mark.parametrize("kwargs", [
    {"length": 0},
    {"length": 10_000},
    {"interval": 0.0},
    {"start_delay": -1},
    {"repeat_limit": -5},
])
def test_invalid_configs_rejected(kwargs):
    with pytest.raises(ValueError):
        TypingConfig(**kwargs).validate()


# --- worker loop ----------------------------------------------------------- #


def test_worker_sends_text_then_enter_repeatedly():
    typist = FakeTypist()
    cfg = TypingConfig(length=5, interval=0.05, start_delay=0, repeat_limit=3)
    finished = threading.Event()
    worker = TypingWorker(cfg, typist, on_finished=lambda r: finished.set())
    worker.start()
    assert finished.wait(5)

    actions = typist.snapshot()
    assert [kind for kind, _ in actions] == ["text", "enter"] * 3
    assert all(len(payload) == 5 for kind, payload in actions if kind == "text")
    assert worker.sent_count == 3


def test_enter_can_be_disabled():
    typist = FakeTypist()
    cfg = TypingConfig(interval=0.05, start_delay=0, repeat_limit=2, press_enter=False)
    finished = threading.Event()
    TypingWorker(cfg, typist, on_finished=lambda r: finished.set()).start()
    assert finished.wait(5)
    assert [kind for kind, _ in typist.snapshot()] == ["text", "text"]


def test_unlimited_run_keeps_going_until_stopped():
    typist = FakeTypist()
    cfg = TypingConfig(interval=0.05, start_delay=0, repeat_limit=0)
    finished = threading.Event()
    worker = TypingWorker(cfg, typist, on_finished=lambda r: finished.set())
    worker.start()
    time.sleep(0.25)
    assert worker.running
    worker.stop()
    assert finished.wait(5)
    assert not worker.running
    assert worker.sent_count >= 3


def test_stop_during_start_delay_sends_nothing():
    typist = FakeTypist()
    cfg = TypingConfig(interval=0.05, start_delay=30)
    finished = threading.Event()
    worker = TypingWorker(cfg, typist, on_finished=lambda r: finished.set())
    worker.start()
    time.sleep(0.15)
    worker.stop()
    assert finished.wait(5)
    assert typist.snapshot() == []


def test_interval_timing_is_honoured():
    typist = FakeTypist()
    cfg = TypingConfig(interval=0.2, start_delay=0, repeat_limit=3)
    finished = threading.Event()
    started = time.monotonic()
    TypingWorker(cfg, typist, on_finished=lambda r: finished.set()).start()
    assert finished.wait(5)
    elapsed = time.monotonic() - started
    # two gaps between three messages
    assert elapsed >= 0.4


def test_counter_increments_across_messages():
    typist = FakeTypist()
    cfg = TypingConfig(fixed_text="hi", add_counter=True, interval=0.05,
                       start_delay=0, repeat_limit=3)
    finished = threading.Event()
    TypingWorker(cfg, typist, on_finished=lambda r: finished.set()).start()
    assert finished.wait(5)
    texts = [p for k, p in typist.snapshot() if k == "text"]
    assert texts == ["hi #1", "hi #2", "hi #3"]


def test_typist_errors_are_reported_not_raised():
    class Boom:
        def type_text(self, text):
            raise RuntimeError("keyboard unavailable")

        def press_enter(self):
            pass

    reasons = []
    done = threading.Event()

    def finish(reason):
        reasons.append(reason)
        done.set()

    cfg = TypingConfig(interval=0.05, start_delay=0)
    TypingWorker(cfg, Boom(), on_finished=finish).start()
    assert done.wait(5)
    assert "keyboard unavailable" in reasons[0]
