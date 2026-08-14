# AutoTyper

A small desktop app that types a message into **whatever window you have focused**
— Notepad, a to-do list, a chat box, anything — then presses **Enter**, waits a
configurable interval (default **2 seconds**), and repeats until you stop it.

The message can be random text of any length, or a fixed string you supply.

## Download

Grab the ready-to-run **`AutoTyper.exe`** from the
[latest release](https://github.com/Not4Pranav/Project-005/releases/latest).
No Python installation is needed — everything is bundled into the one file.

Windows SmartScreen may warn about the download because the build is unsigned
and simulates keystrokes. It is produced on a GitHub-hosted Windows runner by
the public release workflow (`ci/release-workflow.yml`, see `ci/README.md`).

## Features

- Types into any focused window; no integration needed with the target app
- **Interval** between messages (default 2 s) and a **start delay** so you have time to click your Notepad window
- **Length** of the generated string is fully configurable
- Pick which characters to use: `a-z`, `A-Z`, `0-9`, symbols, space
- Or send **fixed text** instead of random, with optional **prefix**, **suffix** and an auto-incrementing **counter** (`#1`, `#2`, ...)
- **Press Enter** after each message can be toggled off
- **Repeat count** limit, or 0 for unlimited
- **Start / Stop** buttons plus a global **F8** hotkey that stops it from anywhere
- Live preview of exactly what will be typed

## Quick start (run from source)

```bash
pip install -r requirements.txt
python main.py
```

## Build a standalone .exe (Windows)

Double-click **`build_exe.bat`**, or run:

```bat
pip install -r requirements-dev.txt
pyinstaller --onefile --windowed --name AutoTyper main.py
```

The executable is written to **`dist\AutoTyper.exe`** and needs no Python
installed to run.

### Automated releases

Pushing a tag that starts with `v` builds the executable on a Windows runner and
attaches it to a GitHub Release automatically:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Once `ci/release-workflow.yml` is moved to `.github/workflows/` (see `ci/README.md`),
the same workflow can also be run on demand from the **Actions** tab via
**Build and Release → Run workflow**. A Windows `.exe` cannot be cross-compiled
from Linux or macOS, which is why the build job runs on `windows-latest`.

## How to use it

1. Launch the app.
2. Set the **length**, tick the **character types** you want, and set the
   **interval** (2 seconds by default).
3. Click **Start**.
4. During the start-delay countdown, click into your **Notepad / to-do list**
   window so it has keyboard focus.
5. The app types a string, presses Enter, and repeats.
6. Press **Stop** in the app, or hit **F8** from any window, to end it.

## Settings reference

| Setting | Meaning |
| --- | --- |
| Length | Number of characters in each random message |
| Fixed text | If set, this exact text is sent instead of a random string |
| Prefix / Suffix | Wrapped around the message body |
| Append counter | Adds ` #1`, ` #2`, ... to each message |
| Characters | Which pools random characters are drawn from |
| Interval | Seconds between messages (minimum 0.05) |
| Start delay | Seconds before the first message, to switch windows |
| Repeat count | Stop after N messages; 0 means unlimited |
| Press Enter | Whether Enter is pressed after each message |

## Project layout

```
main.py                     Launcher
autotyper/core.py           Config, message generation, timing loop (no GUI)
autotyper/keyboard_backend.py  pynput keystrokes + global F8 hotkey
autotyper/app.py            Tkinter user interface
tests/test_core.py          Unit tests for the core logic
build_exe.bat               One-click Windows build
ci/release-workflow.yml     CI: test, build .exe on Windows, publish release
```

The typing logic is kept separate from the GUI and from the OS keyboard layer,
so it can be tested without a display:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Notes

- The app types into the **focused** window, so don't click elsewhere while it
  is running, or the text will go to whichever window you moved to. F8 stops it
  immediately.
- Some antivirus tools flag PyInstaller executables that simulate keystrokes.
  This is a false positive; you can always run from source instead.
- Use it against apps you control. Automated repeated messages may violate the
  terms of service of chat platforms.
