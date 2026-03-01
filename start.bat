@echo off
echo Starting AgentForge...

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r backend\requirements.txt --quiet

if not exist ".env" (
    echo Copying .env.example to .env...
    copy .env.example .env
)

echo.
echo  AgentForge running at http://localhost:8000
echo  API docs at http://localhost:8000/api/docs
echo  Press Ctrl+C to stop.
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
