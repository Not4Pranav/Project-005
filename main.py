"""Launcher for the AutoTyper GUI.

Runs the app and, if anything goes wrong during startup, shows the reason in a
dialog box instead of failing silently. This matters because the app is normally
started with pythonw.exe, which has no console to print a traceback to.
"""

import sys
import traceback


def _report_error(exc: BaseException) -> None:
    """Show a startup failure to the user, however we can."""
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    message = (
        "AutoTyper could not start.\n\n"
        f"{type(exc).__name__}: {exc}\n\n"
        "If you are on Windows, no extra packages are needed.\n"
        "On Linux or macOS, run:  pip install pynput\n\n"
        "Details:\n" + details
    )
    # Try a dialog first, since there is usually no console window.
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("AutoTyper - startup error", message)
        root.destroy()
        return
    except Exception:
        pass
    print(message, file=sys.stderr)


def main() -> int:
    try:
        from autotyper.app import main as run_app

        run_app()
        return 0
    except Exception as exc:  # noqa: BLE001 - last-resort handler
        _report_error(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
