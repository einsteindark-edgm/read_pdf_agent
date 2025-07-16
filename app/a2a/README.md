# A2A Protocol Implementation

This module implements the A2A (Agent-to-Agent) protocol for the Document Extraction Agent, allowing other AI agents to request PDF extraction services.

## Overview

The A2A implementation exposes two main capabilities:
1. **Extract PDF by Name** - Extract structured data from PDFs in the `data/pdfs/` folder
2. **List Available PDFs** - Get a list of all PDFs available for extraction

## Quick Start

### Automated Test (Recommended)
```bash
# Run complete test suite with virtual environment
./run_a2a_test.sh
```

### Manual Setup

1. **Create virtual environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start the A2A server**:
```bash
# Main entry point
python3 __main__.py

# As Python module
python3 -m app.a2a

# Custom configuration
python3 __main__.py  # (port and host can be set via environment variables)
```

4. **Run the client** (in another terminal):
```bash
# Interactive mode
python3 a2a_client.py

# Automated tests
python3 a2a_client.py --test
```

## Testing with A2A Client

The `a2a_client.py` provides a clean A2A SDK-based client with:
- Proper A2A protocol implementation
- Interactive chat mode
- Automated test suite
- Pretty-printed responses

### Interactive Mode
```bash
python3 a2a_client.py
```
Then type commands like:
- `list available pdfs`
- `extract invoice.pdf`
- `help` - Show examples
- `quit` - Exit

### Test Mode
```bash
python3 a2a_client.py --test
```

## Message Examples

### Extraction Requests
- "extract invoice.pdf"
- "analyze bill-of-lading-template.pdf"
- "what's in document-2024.pdf?"
- "get data from customs-form.pdf"

### Listing Requests
- "list available pdfs"
- "what pdfs can you extract?"
- "show me available documents"

## Architecture

```
app/a2a/
├── __init__.py         # Module initialization
├── __main__.py         # Server entry point for python -m app.a2a
├── card.py             # Agent capabilities definition
├── executor.py         # Request processing logic (MCP integration)
├── message_handler.py  # Message routing and formatting
├── server.py           # HTTP server setup (unused - using main entry)
├── client_cli/         # CLI Client for testing (separate from server)
│   ├── __init__.py
│   ├── __main__.py     # Client entry point
│   ├── client.py       # A2A client implementation
│   └── interaction.py  # Interactive CLI interface
└── README.md           # This file
```

### Server Components
- **card.py**: Defines agent capabilities advertised to other agents
- **executor.py**: Core logic that processes requests using MCP tools
- **message_handler.py**: Handles message routing and response formatting

### Client CLI (Testing)
The `client_cli` directory contains a separate client implementation for testing:
- Run with: `python -m app.a2a.client_cli`
- Or directly: `python app/a2a/client_cli/interaction.py`

## Response Format

The agent returns structured responses including:
1. **Task Status** - Working/completed/failed status updates
2. **JSON Artifact** - Extracted data in JSON format
3. **Text Analysis** - Natural language analysis of the document
4. **Summary** - Extraction summary with confidence score

## Security Notes

- Only PDFs in the `data/pdfs/` directory can be accessed
- No file uploads are supported (by design)
- Path traversal protection is implemented
- File size limits apply (350KB default)