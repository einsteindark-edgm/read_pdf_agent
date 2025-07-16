# Document Extraction Agent - Complete Project Overview

## Context for RAG
This document provides a complete overview of the Document Extraction Agent project. This is an A2A (Agent-to-Agent) protocol server that uses MCP (Model Context Protocol) for PDF operations and LangChain with Google Gemini for intelligent document processing.

## Project Location and Structure
```
/Users/edgm/Documents/Projects/AI/read_pdf_agent/
├── __main__.py                    # Entry point
├── a2a_client.py                  # Test client
├── app/                           # Main application code
│   ├── domain/                    # Business logic layer
│   ├── application/               # Use cases and ports
│   ├── adapters/                  # Interface implementations
│   ├── infrastructure/            # External services
│   └── main/                      # Composition and entry points
├── .env                          # Environment configuration
└── requirements.txt              # Python dependencies
```

## CRITICAL: What This Project Does
1. **Receives requests via A2A protocol** - Natural language requests about PDFs
2. **Uses LLM to understand intent** - Gemini decides what to do
3. **Automatically selects MCP tools** - LLM chooses read_doc_contents or list_available_pdfs
4. **Returns structured responses** - Via A2A protocol with proper formatting

## CRITICAL: What This Project Does NOT Do
1. **Does NOT read PDFs directly** - All PDF access is through MCP tools
2. **Does NOT have hardcoded logic** - LLM decides everything
3. **Does NOT use Chainlit** - Only A2A protocol
4. **Does NOT require specific document schemas** - Flexible extraction

## Required Environment Setup

### CRITICAL: Virtual Environment Required
```bash
# MUST use virtual environment - project uses specific A2A and MCP libraries
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

### Environment Variables (.env file)
```bash
# REQUIRED - Without these, the system will NOT work
GOOGLE_API_KEY=your-actual-api-key-here       # From Google AI Studio
MCP_PDF_SERVER_DIR=/path/to/pdf/directory     # Where PDFs are stored
MCP_PDF_SERVER_COMMAND=uv                     # Command to run MCP server
MCP_PDF_SERVER_ARGS=run python mcp_documents_server.py
GEMINI_MODEL=models/gemini-2.0-flash-exp      # Specific model version
```

### ERROR: Common Environment Mistakes
1. **Missing GOOGLE_API_KEY** - Results in 401 errors
2. **Wrong MCP_PDF_SERVER_DIR** - MCP server can't find PDFs
3. **Not activating virtual environment** - ImportError for a2a, langchain_mcp_adapters

## Dependencies (requirements.txt)
```txt
# Core dependencies - EXACT versions matter
a2a==0.1.0                        # A2A protocol implementation
langchain-mcp-adapters==0.1.0     # MCP integration for LangChain
langchain-google-genai==2.0.7     # Google Gemini integration
python-dotenv==1.0.1              # Environment variable management
pydantic==2.10.4                  # Data validation
uvicorn==0.34.0                   # ASGI server
```

## Running the System

### Start the A2A Server
```bash
# ALWAYS activate virtual environment first
source .venv/bin/activate

# Method 1: Direct execution
python3 __main__.py

# Method 2: Using convenience script
./run_server.sh  # Includes environment checks
```

### Server Output When Working
```
🚀 Starting A2A Document Extraction Server...
✅ Environment validated
📦 Initializing composition root...
🔌 Initializing MCP client...
Connected to MCP server with tools: ['read_doc_contents', 'list_available_pdfs']
🌟 A2A server running at http://localhost:8080
```

### ERROR: Common Startup Failures
1. **"ModuleNotFoundError: No module named 'a2a'"**
   - Solution: Activate virtual environment
   
2. **"ValueError: GOOGLE_API_KEY not set"**
   - Solution: Create .env file with valid key
   
3. **"Failed to initialize MCP server"**
   - Solution: Check MCP_PDF_SERVER_DIR exists and contains PDFs

## Testing the System

### Using the A2A Client
```bash
# Interactive mode
python3 a2a_client.py

# Automated tests
python3 a2a_client.py --test
```

### Example Interactions
```
User: "What PDFs are available?"
System: [Uses list_available_pdfs tool automatically]

User: "Read invoice.pdf"
System: [Uses read_doc_contents tool with doc_id="invoice.pdf"]

User: "Extract data from bill_of_lading.pdf"
System: [Reads PDF and extracts structured data]
```

## Architecture Philosophy

### Clean Architecture Layers
1. **Domain** - Business entities (Document, ExtractionResult)
2. **Application** - Use cases and interfaces (ports)
3. **Adapters** - Implementations of interfaces
4. **Infrastructure** - External services (MCP, LangChain, A2A)

### CRITICAL: Dependency Rule
- Dependencies ONLY point inward
- Domain knows nothing about other layers
- Application knows only about Domain
- Adapters know about Application and Domain
- Infrastructure knows about all layers

### ERROR: Architecture Violations to Avoid
1. **Domain importing from Infrastructure** - NEVER do this
2. **Application depending on concrete implementations** - Use interfaces
3. **Circular dependencies** - Will cause import errors

## Key Design Decisions

### Why MCP for PDF Access?
- Standardized tool protocol
- LLM can discover and use tools automatically
- Separation of concerns

### Why A2A Protocol?
- Standard agent communication
- Built-in message formatting
- Async request handling

### Why Clean Architecture?
- Testability
- Maintainability  
- Flexibility to change implementations

## Next Steps for Understanding
1. Read **02_CLEAN_ARCHITECTURE_LAYERS.md** for detailed architecture
2. Read **03_A2A_PROTOCOL_INTEGRATION.md** for A2A details
3. Read **04_MCP_INTEGRATION.md** for MCP tool usage
4. Read **05_EXECUTION_FLOW.md** for complete request flow

## Common Integration Points
- **Entry Point**: `__main__.py` starts everything
- **Main Orchestration**: `app/main/composition_root.py` wires dependencies
- **Request Handling**: `app/infrastructure/web/a2a_executor_adapter.py`
- **Business Logic**: `app/application/use_cases/process_user_request.py`
- **LLM Integration**: `app/adapters/gateways/langchain_extraction_agent.py`