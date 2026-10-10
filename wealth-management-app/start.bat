@echo off
echo Starting Wealth Management Application...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env and set your SECRET_KEY!
    echo.
    pause
)

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

echo.
echo Starting application...
echo Open http://localhost:9000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 9000

pause
