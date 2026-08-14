@echo off
setlocal

set "APP_DIR=%~dp0"
set "PYTHON=%APP_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Cannot find the app's local Python environment.
    echo Please open this project in Codex and ask Codex to repair the launcher.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"
echo Starting Credit Card Statement Analyzer...
echo Your browser should open automatically. Keep this window open while using the app.
echo.
"%PYTHON%" -m streamlit run "%APP_DIR%app.py" --server.address 127.0.0.1

echo.
echo The app has stopped.
pause
