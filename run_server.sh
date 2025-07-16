#!/bin/bash
# Script to run the A2A server with proper environment setup

echo "🚀 Starting A2A Document Extraction Server..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one with:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your actual values"
    exit 1
fi

# Check required environment variables
echo "🔧 Checking environment variables..."
source .env

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-api-key-here" ]; then
    echo "❌ GOOGLE_API_KEY not set in .env file"
    exit 1
fi

if [ -z "$MCP_PDF_SERVER_DIR" ]; then
    echo "❌ MCP_PDF_SERVER_DIR not set in .env file"
    exit 1
fi

echo "✅ Environment setup complete"

# Set PYTHONPATH
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Run the server
echo "🏃 Starting server..."
python3 __main__.py