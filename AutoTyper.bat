@echo off
REM ===============================================================
REM   AutoTyper - just double-click this file.
REM   No installation, no downloads, works offline.
REM ===============================================================
setlocal
cd /d "%~dp0"

REM pyw.exe / pythonw.exe launch without a black console window.
where pyw >nul 2>&1
if %errorlevel%==0 (
    start "AutoTyper" pyw "%~dp0main.py"
    exit /b 0
)

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "AutoTyper" pythonw "%~dp0main.py"
    exit /b 0
)

REM Fall back to console Python so any error stays visible.
where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0main.py"
    if errorlevel 1 pause
    exit /b 0
)

echo.
echo   Python was not found on this computer.
echo.
echo   1. Go to  https://www.python.org/downloads/
echo   2. Run the installer and TICK "Add python.exe to PATH"
echo   3. Double-click AutoTyper.bat again
echo.
pause
exit /b 1
