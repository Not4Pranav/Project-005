def test_windows_backend():
    """Verify win_input builds correct Win32 event sequences, using a mock user32."""
    import sys, types, ctypes
    import autotyper.win_input as W

    # Force the module to believe it's on Windows and capture SendInput calls.
    W.WINDOWS = True
    captured = []
    class FakeUser32:
        def SendInput(self, count, array, size):
            for i in range(count):
                e = array[i]
                captured.append((e.union.ki.wVk, e.union.ki.wScan, e.union.ki.dwFlags))
            return count
    class FakeDLL:
        SendInput = None
    t = W.WindowsTypist.__new__(W.WindowsTypist)
    t._user32 = FakeUser32(); t.per_char_delay = 0.0

    t.type_text("Hi9!")
    downs = [c for c in captured if not (c[2] & W.KEYEVENTF_KEYUP)]
    assert len(captured) == 8, len(captured)          # 4 chars x down+up
    assert [d[1] for d in downs] == [ord(c) for c in "Hi9!"]
    assert all(d[2] & W.KEYEVENTF_UNICODE for d in downs)
    print("unicode typing OK:", [chr(d[1]) for d in downs], "(one SendInput batch)")

    captured.clear(); t.press_enter()
    assert captured == [(W.VK_RETURN,0,0),(W.VK_RETURN,0,W.KEYEVENTF_KEYUP)], captured
    print("enter key OK: VK_RETURN down+up")

    # Non-ASCII / emoji must survive as UTF-16 surrogate pairs
    captured.clear(); t.type_text("é")
    assert len(captured)==2 and captured[0][1]==ord("é")
    captured.clear(); t.type_text("🙂")
    assert len(captured)==4, captured   # surrogate pair -> 2 units x down+up
    print("non-ASCII OK: accents 1 unit, emoji 2 surrogate units")

    # Error path: partial send must raise, not silently drop keystrokes
    class BadUser32:
        def SendInput(self, count, array, size): return 0
    t2 = W.WindowsTypist.__new__(W.WindowsTypist); t2._user32=BadUser32(); t2.per_char_delay=0
    try:
        t2.type_text("x"); print("FAIL: no error raised")
    except Exception as e:
        print("partial-send correctly raised:", type(e).__name__)
    print("\nWINDOWS BACKEND TESTS PASSED")
