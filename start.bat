@echo off
REM ==============================================================================
REM NexusAI - Easy Launch Script (Windows)
REM ==============================================================================

cd /d "%~dp0"

IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r backend\requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

echo ==========================================================
echo Starting NexusAI Enterprise BI and News Platform...
echo URL: http://localhost:8000
echo ==========================================================

set PYTHONPATH=%cd%
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
