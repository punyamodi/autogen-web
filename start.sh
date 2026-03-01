#!/usr/bin/env bash
set -e

echo "Starting AgentForge..."

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -r backend/requirements.txt --quiet

if [ ! -f ".env" ]; then
  echo "Copying .env.example to .env..."
  cp .env.example .env
fi

echo ""
echo "  AgentForge running at http://localhost:8000"
echo "  API docs at http://localhost:8000/api/docs"
echo "  Press Ctrl+C to stop."
echo ""

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
