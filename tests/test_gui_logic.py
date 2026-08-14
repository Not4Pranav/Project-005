def test_gui_logic():
    """Exercise the GUI's config-reading and settings round-trip without Tk."""
    import sys, types, json, tempfile, os

    # Minimal fake tkinter so app.py imports on a headless Linux box.
    tk = types.ModuleType("tkinter")
    class _Var:
        def __init__(self, value=None, **kw): self._v = value
        def get(self): return self._v
        def set(self, v): self._v = v
    class StringVar(_Var):
        def __init__(self, value="", **kw): super().__init__(value)
    class BooleanVar(_Var):
        def __init__(self, value=False, **kw): super().__init__(value)
    tk.StringVar, tk.BooleanVar, tk.Tk, tk.TclError = StringVar, BooleanVar, object, Exception
    ttk = types.ModuleType("tkinter.ttk"); ttk.Frame = object
    mb = types.ModuleType("tkinter.messagebox")
    tk.ttk, tk.messagebox = ttk, mb
    sys.modules.update({"tkinter": tk, "tkinter.ttk": ttk, "tkinter.messagebox": mb})

    from autotyper.app import AutoTyperApp
    from autotyper.settings import save_settings, load_settings, settings_path
    from autotyper.core import build_message

    app = AutoTyperApp.__new__(AutoTyperApp)   # bypass Tk __init__
    app._build_vars()

    # 1. defaults produce a valid 10-char message at 2s interval
    cfg = app.read_config()
    assert cfg.interval == 2.0, cfg.interval
    assert cfg.length == 10
    assert len(build_message(cfg, 1)) == 10
    assert cfg.press_enter is True
    assert cfg.per_char_delay == 0.0
    print("defaults OK: len=10, interval=2.0s, enter=True, instant typing")

    # 2. every requested knob flows through: text, characters, length, speed, timing
    app.v_length.set("25"); app.v_interval.set("0.5"); app.v_charspeed.set("0.02")
    app.v_upper.set(True); app.v_symbols.set(True); app.v_digits.set(False)
    app.v_delay.set("3"); app.v_repeat.set("7")
    cfg = app.read_config()
    assert cfg.length == 25 and cfg.interval == 0.5 and cfg.per_char_delay == 0.02
    assert cfg.start_delay == 3.0 and cfg.repeat_limit == 7
    msg = build_message(cfg, 1)
    assert len(msg) == 25 and not any(c.isdigit() for c in msg)
    print("all knobs OK:", repr(msg))

    # 3. fixed text + prefix/suffix/counter
    app.v_fixed.set("buy milk"); app.v_prefix.set("["); app.v_suffix.set("]")
    app.v_counter.set(True)
    assert build_message(app.read_config(), 4) == "[buy milk] #4"
    print("fixed text OK: [buy milk] #4")

    # 4. settings round-trip
    os.environ["HOME"] = tempfile.mkdtemp()
    data = app.collect_settings()
    assert save_settings(data)
    fresh = AutoTyperApp.__new__(AutoTyperApp); fresh._build_vars()
    fresh.apply_settings(load_settings())
    assert fresh.v_length.get() == "25" and fresh.v_charspeed.get() == "0.02"
    assert fresh.v_fixed.get() == "buy milk" and fresh.v_counter.get() is True
    print("settings persist OK ->", settings_path().name)

    # 5. bad input is rejected with a readable message
    for var, val in [("v_length","0"), ("v_interval","abc"), ("v_charspeed","5")]:
        f = AutoTyperApp.__new__(AutoTyperApp); f._build_vars()
        getattr(f, var).set(val)
        try:
            f.read_config(); raise AssertionError("should have failed: "+var)
        except ValueError as e:
            print(f"rejected {var}={val!r}: {e}")
    print("\nALL GUI LOGIC TESTS PASSED")
