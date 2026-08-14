@echo off
REM Build a standalone AutoTyper.exe. Requires internet only for PyInstaller.
setlocal
cd /d "%~dp0"

echo Installing PyInstaller...
python -m pip install --upgrade pip
python -m pip install pyinstaller || goto :error

echo.
echo Building AutoTyper.exe ...
python -m PyInstaller --noconfirm --onefile --windowed --name AutoTyper main.py || goto :error

echo.
echo ============================================
echo  Done!  Your app:  dist\AutoTyper.exe
echo  Copy that single file anywhere and run it.
echo ============================================
pause
exit /b 0

:error
echo.
echo Build failed - see the messages above.
pause
exit /b 1
