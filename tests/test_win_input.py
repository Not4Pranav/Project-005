import ctypes

import pytest

import autotyper.win_input as W


class FakeUser32:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def SendInput(self, count, array, size):
        events = []
        for index in range(count):
            event = array[index]
            events.append(
                (
                    event.union.ki.wVk,
                    event.union.ki.wScan,
                    event.union.ki.dwFlags,
                )
            )
        self.calls.append((count, size, events))
        return count if self.result is None else self.result


def make_typist(user32=None, delay=0.0):
    # Bypass __init__ because these tests intentionally run on non-Windows CI.
    typist = W.WindowsTypist.__new__(W.WindowsTypist)
    typist._user32 = user32 or FakeUser32()
    typist.per_char_delay = delay
    return typist


def test_input_structure_matches_win32_abi():
    """SendInput rejects a shortened INPUT union with WinError 87."""
    assert ctypes.sizeof(W.INPUT) == W.EXPECTED_INPUT_SIZE
    assert W.EXPECTED_INPUT_SIZE == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
    assert ctypes.sizeof(W._INPUTunion) == ctypes.sizeof(W.MOUSEINPUT)


def test_unicode_text_uses_complete_input_size_and_correct_events():
    user32 = FakeUser32()
    typist = make_typist(user32)

    typist.type_text("Hi9!")

    assert len(user32.calls) == 1
    count, cb_size, captured = user32.calls[0]
    assert count == 8
    assert cb_size == W.EXPECTED_INPUT_SIZE
    downs = [event for event in captured if not (event[2] & W.KEYEVENTF_KEYUP)]
    assert [event[1] for event in downs] == [ord(char) for char in "Hi9!"]
    assert all(event[2] & W.KEYEVENTF_UNICODE for event in downs)


def test_enter_uses_virtual_return_key():
    user32 = FakeUser32()
    make_typist(user32).press_enter()

    count, cb_size, captured = user32.calls[0]
    assert count == 2
    assert cb_size == W.EXPECTED_INPUT_SIZE
    assert captured == [
        (W.VK_RETURN, 0, 0),
        (W.VK_RETURN, 0, W.KEYEVENTF_KEYUP),
    ]


def test_non_ascii_and_emoji_are_encoded_as_utf16():
    user32 = FakeUser32()
    typist = make_typist(user32)

    typist.type_text("é")
    assert len(user32.calls[-1][2]) == 2
    assert user32.calls[-1][2][0][1] == ord("é")

    typist.type_text("🙂")
    emoji_events = user32.calls[-1][2]
    assert len(emoji_events) == 4  # surrogate pair: two UTF-16 units x down/up
    assert [event[1] for event in emoji_events[::2]] == [0xD83D, 0xDE42]


def test_partial_send_has_actionable_error():
    typist = make_typist(FakeUser32(result=0))

    with pytest.raises(RuntimeError) as exc_info:
        typist.type_text("x")

    message = str(exc_info.value)
    assert "0 of 2 keyboard events" in message
    assert "editable text field" in message
    assert "administrator" in message
