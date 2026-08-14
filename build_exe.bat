@echo off
REM Build AutoTyper.exe (single file, no console window).
setlocal
echo Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt || goto :error

echo Building executable...
python -m PyInstaller --noconfirm --onefile --windowed --name AutoTyper ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    main.py || goto :error

echo.
echo Done. Your executable is at: dist\AutoTyper.exe
pause
exit /b 0

:error
echo.
echo Build failed. See the messages above.
pause
exit /b 1
