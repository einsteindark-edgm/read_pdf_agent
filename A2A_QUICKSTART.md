# A2A Protocol Quick Start Guide

This guide will help you get the A2A Document Extraction Agent running quickly.

## 🚀 Quick Setup

### 1. Set up the environment

```bash
# Create and activate virtual environment (requires Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your-actual-api-key-here
```

### 3. Run Quick Test

```bash
# This will verify everything is working
./run_quick_test.sh
```

## 📖 Manual Usage

### Start the Server (Terminal 1)

```bash
# Activate virtual environment
source .venv/bin/activate

# install depend
pip install -r requirements.txt

# Start the A2A server
python3 __main__.py
```

You should see:
```
🚀 Starting A2A Document Extraction Agent on 0.0.0.0:8080
📋 Agent card available at: http://0.0.0.0:8080/.well-known/agent.json
💬 Send messages to: http://0.0.0.0:8080/
```

### Use the Client (Terminal 2)

```bash
# Activate virtual environment
source .venv/bin/activate

# install depend
pip install -r requirements.txt

# Run interactive client
python3 a2a_client.py

# Or run automated tests
python3 a2a_client.py --test
```

Available commands:
- `list available pdfs` - Show all PDFs in the data/pdfs folder
- `extract [filename]` - Extract data from a specific PDF
- `help` - Show available commands
- `quit` - Exit the client

## 🛠️ Troubleshooting

### Port Already in Use

If you see "Port 8080 is already in use":

```bash
# Kill all processes using port 8080
./kill_a2a_servers.sh
```

### Server Not Starting

1. Check your Google API key is set correctly in `.env`
2. Ensure Python 3.11+ is installed: `python3 --version`
3. Check the virtual environment is activated (you should see `(.venv)` in your prompt)

### Client Connection Issues

1. Ensure the server is running in another terminal
2. Wait for the server to fully start before connecting
3. Check the server logs for any errors

## 📁 Adding PDFs

Place PDF files in the `data/pdfs/` directory:

```bash
# Create directory if it doesn't exist
mkdir -p data/pdfs

# Copy your PDFs
cp your-document.pdf data/pdfs/
```

## 🔍 Example Session

```
You: list available pdfs

📂 Available PDFs (1):
• bill-of-lading-template.pdf

You: extract bill-of-lading-template.pdf

📋 Extracting data from: bill-of-lading-template.pdf
📄 Extracted Data - BILL_OF_LADING (application/json)
{
  "document_type": "BILL_OF_LADING",
  "confidence_score": 0.95,
  "extracted_data": {
    "document_number": "BL-2024-001",
    "vessel_name": "MSC CONTAINER",
    ...
  }
}
```