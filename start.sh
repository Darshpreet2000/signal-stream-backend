#!/bin/bash
# Convenient script to run the SignalStream AI backend

echo "🚀 Starting SignalStream AI Backend..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating it..."
    python -m venv venv
    echo "✓ Virtual environment created"
    
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "✓ Virtual environment found"
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your credentials before running"
    exit 1
fi

echo "✓ Configuration file found"
echo ""
echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""

# Run the application
python run.py
