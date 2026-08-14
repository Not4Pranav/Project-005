# AutoTyper

A small, fast, **fully offline** desktop app that types a message into whatever
window you have focused — Notepad, a to-do list, a chat box — presses **Enter**,
waits a configurable interval (default **2 seconds**), and repeats until you
stop it.

**No installation. No downloads. No dependencies on Windows.**

## Easiest way to run it

1. Download this project (green **Code → Download ZIP**, then unzip).
2. Double-click **`AutoTyper.bat`**.

That's it. The app uses Python's built-in `ctypes` module to talk to Windows
directly, so there is nothing to `pip install`. If Windows doesn't have Python
at all, the launcher tells you where to get it.

Prefer a single `.exe`? Run **`build_exe.bat`** once and you'll get
`dist\AutoTyper.exe`, a standalone file you can copy anywhere.

## What you can configure

| Setting | What it does |
| --- | --- |
| **Length** | Number of characters in each random message |
| **Characters** | Which pools to draw from: `a-z`, `A-Z`, `0-9`, symbols, space |
| **Fixed text** | Send this exact text instead of a random string |
| **Prefix / Suffix** | Wrapped around the message body |
| **Append counter** | Adds ` #1`, ` #2`, ... to each message |
| **Interval** | Seconds between messages (default 2, minimum 0.05) |
| **Typing speed** | Seconds per character — `0` types the whole string instantly |
| **Start delay** | Seconds before the first message, so you can switch windows |
| **Repeat count** | Stop after N messages, or `0` for unlimited |
| **Press Enter** | Whether Enter is pressed after each message |

Your settings are saved automatically and restored the next time you open the
app.

## How to use it

1. Launch the app.
2. Set the length, characters, interval and typing speed you want. The
   **Preview** box shows exactly what will be typed.
3. Click **Start**.
4. During the countdown, click into your **Notepad / to-do list** window so it
   has keyboard focus.
5. The app types a string, presses Enter, waits, and repeats.
6. Press **Stop**, or hit **F8** from any window, to end it.

## Speed and offline behaviour

- **Offline:** the app makes no network calls of any kind.
- **Fast typing:** on Windows the entire string is delivered in a single
  `SendInput` call, so even long messages appear instantly. Set *typing speed*
  above 0 only if you want a visible human-like keystroke effect.
- **Responsive UI:** typing runs on a background thread, so the window never
  freezes and **Stop** reacts immediately.
- **Any character:** keystrokes are sent as Unicode, so symbols and accented
  characters work regardless of your keyboard layout.

## Project layout

```
AutoTyper.bat               Double-click launcher (no setup)
build_exe.bat               Build a standalone dist\AutoTyper.exe
main.py                     Entry point
autotyper/core.py           Config, message generation, timing loop (no GUI)
autotyper/win_input.py      Native Windows keystrokes via ctypes (no packages)
autotyper/keyboard_backend.py  Optional pynput backend for Linux/macOS
autotyper/backends.py       Picks the best available backend
autotyper/settings.py       Saves your configuration between runs
autotyper/app.py            Tkinter user interface
tests/                      Unit tests
ci/release-workflow.yml     Optional CI to publish a prebuilt .exe
```

## Running on Linux or macOS

The core app is cross-platform, but sending keystrokes needs a helper there:

```bash
pip install pynput
python main.py
```

## Tests

```bash
pip install pytest
python -m pytest tests -q
```

20 tests cover message generation, character-set selection, validation, the
timing loop, the Windows event encoding, and the settings round-trip.

## Notes

- The app types into the **focused** window, so don't click elsewhere while it
  runs. **F8** stops it instantly from anywhere.
- A self-built `.exe` may trigger a SmartScreen or antivirus warning, because
  unsigned executables that simulate keystrokes match generic heuristics. This
  is a false positive. Running `AutoTyper.bat` avoids the issue entirely.
- Use it against apps you control; automated repeat messages may breach the
  terms of service of chat platforms.
