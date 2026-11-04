@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python not found. Install Python 3.12+ from python.org
        echo and enable "Add python.exe to PATH".
        pause
        exit /b 1
    )
    python main.py
)

echo.
echo Exit code: %ERRORLEVEL%
pause