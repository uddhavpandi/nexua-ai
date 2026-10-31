#!/usr/bin/env bash
# ==============================================================================
# NexusAI - Easy Launch Script (macOS / Linux)
# ==============================================================================

cd "$(dirname "$0")"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv .venv || python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r backend/requirements.txt
fi

echo "=========================================================="
echo "⚡ Starting NexusAI Enterprise BI & News Platform..."
echo "🌐 URL: http://localhost:8000"
echo "=========================================================="

PYTHONPATH=. .venv/bin/uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
