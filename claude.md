# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Description

Document Extraction Agent is an intelligent PDF processing system powered by Google's Gemini Flash 2.0 that automatically extracts relevant structured data from documents. The system uses MCP (Model Context Protocol) for PDF access and Clean Architecture for maintainable code structure.

## Key Features

- 🔍 **Automatic Tool Selection**: LLM intelligently chooses MCP tools based on user requests
- 📊 **Flexible Data Extraction**: Extracts data without rigid schemas
- 🤖 **MCP Integration**: Uses external MCP server for PDF operations
- 📄 **A2A Protocol**: Agent-to-Agent protocol for standardized communication
- 🏗️ **Clean Architecture**: Domain, Application, Adapters, and Infrastructure layers

## Common Development Commands

### Setup & Installation
```bash
python3 -m venv .venv               # Create virtual environment
source .venv/bin/activate           # Activate environment
pip install -r requirements.txt     # Install dependencies
cp .env.example .env               # Create environment file (add your keys)
```

### Running the Server
```bash
python3 __main__.py                # Start A2A server
# Or use the convenience script:
./run_server.sh                    # Runs with environment checks
```

### Testing
```bash
python3 a2a_client.py              # Interactive client
python3 a2a_client.py --test       # Run automated tests
```

## Clean Architecture

### Layer Structure
```
app/
├── domain/              # Business entities and rules
│   ├── entities/       # Document, ExtractionResult
│   └── exceptions/     # Domain-specific errors
├── application/         # Use cases and ports
│   ├── use_cases/      # ProcessUserRequestUseCase
│   ├── ports/          # ExtractionAgent, AgentService interfaces
│   ├── dto/            # Data transfer objects
│   └── exceptions/     # Application errors
├── adapters/           # Interface adapters
│   ├── controllers/    # A2AController
│   ├── presenters/     # A2APresenter
│   └── gateways/       # LangChainExtractionAgent
├── infrastructure/     # External services
│   ├── external_services/  # MCPClient, LangChainSetup
│   ├── web/               # A2A protocol adapter
│   └── a2a/               # A2A server components
└── main/               # Composition root and entry points
```

### Request Flow
```
User Request → A2A Protocol → Controller → Use Case → Agent → LangChain → MCP Tools
```

### Environment Variables
```bash
# Required in .env
GOOGLE_API_KEY=                    # Google AI Studio key
MCP_PDF_SERVER_DIR=               # Directory with PDFs
MCP_PDF_SERVER_COMMAND=uv         # Command to run MCP server
MCP_PDF_SERVER_ARGS=run python mcp_documents_server.py
GEMINI_MODEL=models/gemini-2.0-flash-exp
```

## Code Patterns & Conventions

### Dependency Injection
```python
# All dependencies flow inward
# Infrastructure → Application → Domain
# Composition root wires everything together
```

### Port/Adapter Pattern
```python
# Application defines ports (interfaces)
class ExtractionAgent(ABC):
    async def process_message(self, message: str) -> Dict[str, Any]

# Adapters implement ports
class LangChainExtractionAgent(ExtractionAgent):
    # Implementation using LangChain
```

### MCP Tool Integration
```python
# MCP tools are automatically discovered and provided to LangChain
# The LLM decides which tools to use based on the user's request
```

## Project-Specific Notes

- **A2A Protocol**: Uses Agent-to-Agent protocol for communication
- **MCP Server**: External server provides PDF reading tools
- **No Direct File Access**: All PDF operations go through MCP tools
- **LLM Tool Selection**: The AI agent automatically chooses appropriate tools
- **Clean Separation**: Each layer has clear responsibilities

## Adding New Features

### To Add New MCP Tools
1. Update the MCP server to expose new tools
2. The system will automatically discover and use them

### To Change AI Provider
1. Create new implementation of `AgentService` port
2. Update composition root to use new implementation
3. No changes needed in other layers

### To Add New Use Cases
1. Create use case in `app/application/use_cases/`
2. Define any needed ports in `app/application/ports/`
3. Implement ports in appropriate adapter layer
4. Wire in composition root

## Testing Strategy

- **Integration**: Use `a2a_client.py` for end-to-end testing
- **Startup**: Check system initialization without full server
- **Architecture**: Verify dependency rules are followed

## Performance Considerations

- **Async I/O**: All operations are async
- **MCP Connection**: Single persistent connection to MCP server
- **Token Limits**: Configured in LangChain setup
- **Tool Timeout**: MCP tools have configurable timeouts

## Glossary

- **MCP** – Model Context Protocol for tool integration
- **A2A** – Agent-to-Agent communication protocol
- **Port** – Interface defined in application layer
- **Adapter** – Implementation of a port
- **Use Case** – Application-specific business logic
- **Entity** – Domain object with business rules