"""Tkinter GUI for AutoTyper."""

from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from autotyper.core import MIN_INTERVAL, TypingConfig, TypingWorker, build_message
from autotyper.keyboard_backend import PYNPUT_AVAILABLE, HotkeyListener, PynputTypist

APP_TITLE = "AutoTyper - repeating message sender"
STOP_KEY = "f8"


class AutoTyperApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.master.title(APP_TITLE)
        self.master.resizable(False, False)
        self.grid(sticky="nsew")

        self.worker: TypingWorker | None = None
        self.events: queue.Queue = queue.Queue()

        self._build_vars()
        self._build_ui()

        self.hotkey = HotkeyListener(self.request_stop, STOP_KEY)
        self.hotkey.start()

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(60, self._drain_events)

        if not PYNPUT_AVAILABLE:
            self.set_status("pynput missing - run: pip install -r requirements.txt")
            self.start_btn.state(["disabled"])

    # -- state -------------------------------------------------------------- #

    def _build_vars(self) -> None:
        self.v_length = tk.StringVar(value="10")
        self.v_interval = tk.StringVar(value="2.0")
        self.v_delay = tk.StringVar(value="5")
        self.v_repeat = tk.StringVar(value="0")
        self.v_enter = tk.BooleanVar(value=True)

        self.v_lower = tk.BooleanVar(value=True)
        self.v_upper = tk.BooleanVar(value=False)
        self.v_digits = tk.BooleanVar(value=True)
        self.v_symbols = tk.BooleanVar(value=False)
        self.v_space = tk.BooleanVar(value=False)

        self.v_fixed = tk.StringVar(value="")
        self.v_prefix = tk.StringVar(value="")
        self.v_suffix = tk.StringVar(value="")
        self.v_counter = tk.BooleanVar(value=False)

        self.v_status = tk.StringVar(value="Ready")
        self.v_sent = tk.StringVar(value="Sent: 0")

    # -- layout ------------------------------------------------------------- #

    def _build_ui(self) -> None:
        row = 0

        msg = ttk.LabelFrame(self, text="Message", padding=8)
        msg.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(msg, text="Length (characters)").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(msg, from_=1, to=5000, width=8, textvariable=self.v_length).grid(
            row=0, column=1, sticky="w", padx=6
        )
        ttk.Label(msg, text="Fixed text (optional, overrides random)").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(msg, width=28, textvariable=self.v_fixed).grid(
            row=1, column=1, sticky="w", padx=6, pady=(6, 0)
        )
        ttk.Label(msg, text="Prefix").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(msg, width=28, textvariable=self.v_prefix).grid(
            row=2, column=1, sticky="w", padx=6, pady=(6, 0)
        )
        ttk.Label(msg, text="Suffix").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(msg, width=28, textvariable=self.v_suffix).grid(
            row=3, column=1, sticky="w", padx=6, pady=(6, 0)
        )
        ttk.Checkbutton(
            msg, text="Append counter (#1, #2, ...)", variable=self.v_counter
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        row += 1

        chars = ttk.LabelFrame(self, text="Characters to use", padding=8)
        chars.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        for col, (text, var) in enumerate(
            [
                ("a-z", self.v_lower),
                ("A-Z", self.v_upper),
                ("0-9", self.v_digits),
                ("!@#$", self.v_symbols),
                ("space", self.v_space),
            ]
        ):
            ttk.Checkbutton(chars, text=text, variable=var).grid(
                row=0, column=col, sticky="w", padx=(0, 10)
            )
        row += 1

        timing = ttk.LabelFrame(self, text="Timing", padding=8)
        timing.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(timing, text="Interval (seconds)").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(
            timing, from_=MIN_INTERVAL, to=3600, increment=0.5, width=8,
            textvariable=self.v_interval,
        ).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(timing, text="Start delay (seconds)").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Spinbox(
            timing, from_=0, to=600, width=8, textvariable=self.v_delay
        ).grid(row=1, column=1, sticky="w", padx=6, pady=(6, 0))
        ttk.Label(timing, text="Repeat count (0 = unlimited)").grid(
            row=2, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Spinbox(
            timing, from_=0, to=1000000, width=8, textvariable=self.v_repeat
        ).grid(row=2, column=1, sticky="w", padx=6, pady=(6, 0))
        ttk.Checkbutton(
            timing, text="Press Enter after each message", variable=self.v_enter
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        row += 1

        preview = ttk.LabelFrame(self, text="Preview", padding=8)
        preview.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self.preview_label = ttk.Label(preview, text="", width=44, anchor="w")
        self.preview_label.grid(row=0, column=0, sticky="w")
        ttk.Button(preview, text="Refresh", command=self.refresh_preview).grid(
            row=0, column=1, padx=(8, 0)
        )
        row += 1

        buttons = ttk.Frame(self)
        buttons.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self.start_btn = ttk.Button(buttons, text="Start", command=self.on_start)
        self.start_btn.grid(row=0, column=0, sticky="w")
        self.stop_btn = ttk.Button(buttons, text="Stop", command=self.request_stop)
        self.stop_btn.grid(row=0, column=1, padx=8)
        self.stop_btn.state(["disabled"])
        ttk.Label(buttons, textvariable=self.v_sent).grid(row=0, column=2, padx=8)
        row += 1

        ttk.Label(self, textvariable=self.v_status, foreground="#0a5", wraplength=380).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(
            self,
            text=f"Tip: press {STOP_KEY.upper()} anywhere to stop instantly.",
            foreground="#666",
        ).grid(row=row, column=0, sticky="w", pady=(4, 0))

        self.refresh_preview()

    # -- helpers ------------------------------------------------------------ #

    def set_status(self, text: str) -> None:
        self.v_status.set(text)

    def read_config(self) -> TypingConfig:
        def as_int(var: tk.StringVar, label: str) -> int:
            try:
                return int(float(var.get().strip() or 0))
            except ValueError:
                raise ValueError(f"{label} must be a number.")

        def as_float(var: tk.StringVar, label: str) -> float:
            try:
                return float(var.get().strip() or 0)
            except ValueError:
                raise ValueError(f"{label} must be a number.")

        cfg = TypingConfig(
            length=as_int(self.v_length, "Length"),
            interval=as_float(self.v_interval, "Interval"),
            start_delay=as_float(self.v_delay, "Start delay"),
            repeat_limit=as_int(self.v_repeat, "Repeat count"),
            press_enter=self.v_enter.get(),
            use_lowercase=self.v_lower.get(),
            use_uppercase=self.v_upper.get(),
            use_digits=self.v_digits.get(),
            use_symbols=self.v_symbols.get(),
            use_space=self.v_space.get(),
            fixed_text=self.v_fixed.get(),
            prefix=self.v_prefix.get(),
            suffix=self.v_suffix.get(),
            add_counter=self.v_counter.get(),
        )
        cfg.validate()
        return cfg

    def refresh_preview(self) -> None:
        try:
            cfg = self.read_config()
        except Exception as exc:
            self.preview_label.config(text=str(exc))
            return
        sample = build_message(cfg, 1)
        if len(sample) > 46:
            sample = sample[:43] + "..."
        self.preview_label.config(text=sample)

    # -- actions ------------------------------------------------------------ #

    def on_start(self) -> None:
        if self.worker is not None and self.worker.running:
            return
        try:
            cfg = self.read_config()
            typist = PynputTypist()
        except Exception as exc:
            messagebox.showerror("Cannot start", str(exc))
            return

        self.worker = TypingWorker(
            config=cfg,
            typist=typist,
            on_status=lambda m: self.events.put(("status", m)),
            on_sent=lambda n, t: self.events.put(("sent", n)),
            on_finished=lambda r: self.events.put(("finished", r)),
        )
        self.worker.start()
        self.start_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])
        self.v_sent.set("Sent: 0")

    def request_stop(self) -> None:
        if self.worker is not None:
            self.worker.stop()
        self.set_status("Stopping...")

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "status":
                    self.set_status(payload)
                elif kind == "sent":
                    self.v_sent.set(f"Sent: {payload}")
                elif kind == "finished":
                    self.set_status(payload)
                    self.start_btn.state(["!disabled"])
                    self.stop_btn.state(["disabled"])
        except queue.Empty:
            pass
        self.after(60, self._drain_events)

    def on_close(self) -> None:
        if self.worker is not None:
            self.worker.stop()
            self.worker.join(timeout=1.0)
        self.hotkey.stop()
        self.master.destroy()


def main() -> None:
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    AutoTyperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
