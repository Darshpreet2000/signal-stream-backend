#!/bin/bash
# Script to run the comprehensive API tests

echo "🧪 SupportPulse AI Backend - Test Suite"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./start.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Check if API is running
echo "Checking if API is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API is running"
else
    echo "⚠️  API is not running. Please start it first with:"
    echo "   ./start.sh"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Running comprehensive API tests..."
echo "===================================="
echo ""

# Run the test script
python test_api.py

echo ""
echo "✓ Test execution completed"
