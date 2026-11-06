@echo off
setlocal
cd /d "%~dp0"

set "PAUSE_AT_END=1"
if /i "%~1"=="--no-pause" set "PAUSE_AT_END="

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
    echo.
    echo Installation failed. See the error above.
    if defined PAUSE_AT_END pause
    exit /b 1
)

echo.
echo Installation complete. Launch "garvis" from the desktop.
if defined PAUSE_AT_END pause