@echo off
REM ---------------------------------------------------------------
REM  Double-click this file to run AutoTyper.
REM  No installation, no downloads - uses the Python already on your PC.
REM ---------------------------------------------------------------
cd /d "%~dp0"

REM Prefer the py launcher, fall back to python on PATH.
where py >nul 2>&1 && (
    start "" pyw main.py
    exit /b 0
)
where python >nul 2>&1 && (
    start "" pythonw main.py
    exit /b 0
)

echo.
echo Python was not found on this computer.
echo.
echo Install it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH" during setup), then run this file again.
echo.
pause
