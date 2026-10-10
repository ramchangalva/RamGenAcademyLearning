#!/bin/bash

echo "Starting Wealth Management Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env and set your SECRET_KEY!"
    echo ""
    read -p "Press enter to continue..."
fi

# Install dependencies if needed
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python3 -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

echo ""
echo "Starting application..."
echo "Open http://localhost:9000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
