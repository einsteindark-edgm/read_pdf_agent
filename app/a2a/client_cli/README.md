# A2A Client CLI

This is a command-line interface client for testing the A2A Document Extraction Agent.

## Usage

### Running the Client

```bash
# From project root - Interactive mode
python -m app.a2a.client_cli

# From project root - Test mode
python -m app.a2a.client_cli --test

# Using the convenience script
python a2a_client.py
```

### Interactive Commands

When in interactive mode, you can:
- `list available pdfs` - Show all PDFs that can be processed
- `extract [filename]` - Extract data from a specific PDF
- `help` - Show example commands
- `quit` - Exit the client

### Examples

```
You: list available pdfs
Agent: Available PDF files:
- bill-of-lading-template.pdf
- pagoMorrosCuenta.pdf

You: extract bill-of-lading-template.pdf
Agent: [Extracts and shows document data]
```

## Architecture

- **client.py** - Core A2A client implementation using the A2A SDK
- **interaction.py** - Interactive CLI interface for user interaction
- **__main__.py** - Entry point for running as a module

## Note

This client is separate from the server implementation and is intended for testing purposes only.