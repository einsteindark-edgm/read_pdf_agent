# Common Errors and Fixes - Complete Troubleshooting Guide

## Context for RAG
This document contains all common errors, their root causes, and proven fixes. This is CRITICAL for debugging. Each error includes the exact error message, where it occurs, why it happens, and how to fix it.

## Import Errors

### Error: ModuleNotFoundError: No module named 'a2a'
**Where**: Any file importing a2a
**When**: Running without virtual environment
```bash
Traceback (most recent call last):
  File "__main__.py", line 1, in <module>
    from app.main.a2a_main import run_server
  File "/app/main/a2a_main.py", line 10, in <module>
    from a2a.server import A2AStarletteApplication
ModuleNotFoundError: No module named 'a2a'
```

**Root Cause**: Virtual environment not activated
**Fix**:
```bash
# ALWAYS activate virtual environment first
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Verify a2a is installed
pip list | grep a2a
```

### Error: ImportError: cannot import name 'DocumentReader'
**Where**: Old code trying to import removed interfaces
```python
from app.application.ports import DocumentReader  # FAILS
```

**Root Cause**: DocumentReader was removed in refactoring
**Fix**:
```python
# DocumentReader no longer exists
# Use ExtractionAgent instead
from app.application.ports import ExtractionAgent
```

### Error: Circular Import
**Where**: Between layers
```bash
ImportError: cannot import name 'SomeClass' from partially initialized module
```

**Root Cause**: Violating Clean Architecture dependency rules
**Fix**:
1. Domain should NOT import from other layers
2. Application should only import from Domain
3. Adapters should only import from Application and Domain
4. Infrastructure can import from all layers

**Example Fix**:
```python
# BAD - Domain importing from Infrastructure
# app/domain/entities/document.py
from app.infrastructure.config import settings  # WRONG!

# GOOD - Pass configuration as parameter
class Document:
    def __init__(self, filename: str, content: str, max_size_kb: int = 350):
        # Use parameter instead of importing settings
```

## Environment Configuration Errors

### Error: ValueError: GOOGLE_API_KEY not set
**Where**: Composition root initialization
```bash
ValueError: GOOGLE_API_KEY not set in .env file
```

**Root Cause**: Missing or invalid .env file
**Fix**:
```bash
# 1. Create .env file
cp .env.example .env

# 2. Edit .env and add your actual API key
GOOGLE_API_KEY=your-actual-api-key-here  # Get from https://aistudio.google.com

# 3. Verify it's loaded
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

### Error: MCP_PDF_SERVER_DIR not set
**Where**: MCP client initialization
```bash
ValueError: MCP_PDF_SERVER_DIR not set in .env file
```

**Root Cause**: Missing MCP configuration
**Fix**:
```bash
# Add to .env file
MCP_PDF_SERVER_DIR=/absolute/path/to/your/pdfs
MCP_PDF_SERVER_COMMAND=uv
MCP_PDF_SERVER_ARGS=run python mcp_documents_server.py

# Verify directory exists
ls -la $MCP_PDF_SERVER_DIR
```

## MCP Server Errors

### Error: Failed to initialize MCP server
**Where**: MCPClient.initialize()
```python
Failed to initialize MCP server: [Errno 2] No such file or directory: 'uv'
```

**Root Cause**: MCP server command not found
**Fix**:
```bash
# Option 1: Install uv
pip install uv

# Option 2: Use python directly
# In .env:
MCP_PDF_SERVER_COMMAND=python
MCP_PDF_SERVER_ARGS=mcp_documents_server.py
```

### Error: MCP server initialized but no tools found
**Where**: After MCP initialization
```
WARNING: MCP server initialized but no tools found!
```

**Root Cause**: MCP server not exposing tools correctly
**Fix**:
1. Check MCP server implementation
2. Verify server is running: `ps aux | grep mcp`
3. Check server logs for errors
4. Ensure tools are registered in server

**Example MCP Server Fix**:
```python
# MCP server must register tools
class PDFServer(Server):
    def __init__(self):
        super().__init__()
        # CRITICAL: Must register tools
        self.register_tool(
            Tool(name="list_available_pdfs", ...),
            self.list_pdfs
        )
```

### Error: Connection refused to MCP server
**Where**: Tool invocation
```
httpx.ConnectError: All connection attempts failed
```

**Root Cause**: MCP server not running or wrong transport
**Fix**:
```bash
# Check if using stdio (default) or http transport
# In .env:
MCP_PDF_TRANSPORT=stdio  # Use subprocess communication

# If using http, ensure server is listening on correct port
```

## LangChain and LLM Errors

### Error: Invalid API Key
**Where**: LangChain Gemini initialization
```
google.api_core.exceptions.InvalidArgument: 400 API key not valid
```

**Root Cause**: Invalid Google API key
**Fix**:
1. Get valid key from https://aistudio.google.com
2. Update .env file
3. Restart server

### Error: Rate Limit Exceeded
**Where**: During LLM calls
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Root Cause**: Too many requests to Gemini
**Fix**:
```python
# Add retry logic in langchain_setup.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_llm(self, prompt):
    return await self.llm.ainvoke(prompt)
```

### Error: Parser Output Error
**Where**: PydanticReActOutputParser
```
OutputParserException: Could not parse agent output
```

**Root Cause**: LLM output doesn't match expected format
**Fix in `/app/infrastructure/external_services/pydantic_parser.py`**:
```python
def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
    # Add more flexible parsing
    text = text.strip()
    
    # Handle common LLM variations
    # Sometimes Gemini uses "Action:" sometimes "action:"
    action_match = re.search(
        r"(?:Action|action):\s*(.+?)\n+(?:Action Input|action input):\s*(.+?)(?:\n|$)",
        text,
        re.DOTALL | re.IGNORECASE  # Case insensitive
    )
```

### Error: Tool Not Found
**Where**: Agent trying to use tool
```
ValueError: Tool 'read_pdf' not found. Available tools: ['read_doc_contents', 'list_available_pdfs']
```

**Root Cause**: LLM using wrong tool name
**Fix**: Update prompt to be more explicit
```python
# In langchain_setup.py prompt
"""
IMPORTANT: Use EXACTLY these tool names:
- list_available_pdfs (NOT list_pdfs or list_documents)
- read_doc_contents (NOT read_pdf or read_document)
"""
```

## A2A Protocol Errors

### Error: InvalidParamsError
**Where**: A2A executor
```
a2a.utils.errors.ServerError: InvalidParamsError
```

**Root Cause**: Can't extract message from A2A format
**Fix**: Check message extraction logic
```python
def _extract_user_message(self, context: RequestContext) -> str:
    # Handle different A2A message formats
    if not context.message:
        return ""
    
    # Try multiple extraction methods
    # Method 1: Direct text
    if hasattr(context.message, 'text'):
        return context.message.text
    
    # Method 2: Parts format
    if hasattr(context.message, 'parts'):
        for part in context.message.parts:
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                return part.root.text
    
    return ""
```

### Error: Task State Not Updated
**Where**: Client waiting for response
**Symptom**: Client hangs, no response

**Root Cause**: Not sending task updates
**Fix**: Always use TaskUpdater
```python
# In executor
updater = TaskUpdater(event_queue, task.id, task.contextId)

# CRITICAL: Send working status
await updater.update_status(
    TaskState.working,
    new_agent_text_message("Processing...", task.contextId, task.id)
)

# ... do work ...

# CRITICAL: Send completion with final=True
await updater.update_status(
    TaskState.completed,
    response,
    final=True  # This tells client we're done
)
```

## Architecture Violations

### Error: Use case depending on infrastructure
**Bad Code**:
```python
# app/application/use_cases/process_user_request.py
from app.infrastructure.external_services import MCPClient  # WRONG!

class ProcessUserRequestUseCase:
    def __init__(self, mcp_client: MCPClient):  # WRONG!
```

**Fix**: Depend on interfaces
```python
from app.application.ports import ExtractionAgent  # Interface

class ProcessUserRequestUseCase:
    def __init__(self, extraction_agent: ExtractionAgent):  # Correct
```

### Error: Domain knowing about frameworks
**Bad Code**:
```python
# app/domain/entities/document.py
from pydantic import BaseModel  # WRONG! External framework

class Document(BaseModel):  # WRONG!
```

**Fix**: Pure Python in domain
```python
class Document:
    """Pure Python class, no external dependencies."""
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content
```

## Async/Await Errors

### Error: RuntimeWarning: coroutine was never awaited
**Where**: Calling async functions
```python
# Bad
result = extraction_agent.process_message(msg)  # Missing await!

# Good  
result = await extraction_agent.process_message(msg)
```

**Fix**: Always await async functions
```python
# Check function definition
async def process_message(self, message: str):  # async = needs await
    ...
```

### Error: Cannot run async function from sync context
**Where**: Testing or debugging
```python
# Bad
result = process_message("test")  # Can't call directly

# Good
import asyncio
result = asyncio.run(process_message("test"))
```

## Tool Input Format Errors

### Error: Tool expects dict but got string
**Where**: MCP tool invocation
```
TypeError: read_doc_contents() got str, expected dict
```

**Root Cause**: LLM provided wrong format
**Fix in `MCPToolInputs.convert_input()`**:
```python
@staticmethod
def convert_input(action: str, action_input: Union[str, Dict]) -> Dict[str, Any]:
    if action == "read_doc_contents":
        if isinstance(action_input, str):
            # Convert "invoice.pdf" to {"doc_id": "invoice.pdf"}
            return {"doc_id": action_input.strip('"')}
        
        # Handle other common formats
        # "doc_id: invoice.pdf" -> {"doc_id": "invoice.pdf"}
        if ":" in str(action_input):
            key, value = str(action_input).split(":", 1)
            return {key.strip(): value.strip()}
```

## Memory and Performance Issues

### Error: Server becomes slow after many requests
**Root Cause**: Memory leak or too many agent instances
**Fix**: Ensure single instances
```python
# In composition_root.py
_composition_root: Optional[CompositionRoot] = None  # Singleton

def get_composition_root() -> CompositionRoot:
    global _composition_root
    if _composition_root is None:
        _composition_root = CompositionRoot()
        _composition_root.initialize()
    return _composition_root  # Always return same instance
```

### Error: MCP subprocess zombies
**Root Cause**: MCP processes not cleaned up
**Fix**: Implement proper shutdown
```python
async def shutdown_composition_root() -> None:
    """Shutdown the global composition root."""
    global _composition_root
    if _composition_root is not None:
        await _composition_root.shutdown()  # Closes MCP
        _composition_root = None
```

## Debugging Strategies

### Enable All Logging
```python
import logging

# At startup
logging.basicConfig(level=logging.DEBUG)

# In specific modules
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### Add Checkpoints
```python
# In complex flows
logger.info(f"Checkpoint 1: Message received: {message}")
logger.info(f"Checkpoint 2: Tools available: {[t.name for t in tools]}")
logger.info(f"Checkpoint 3: LLM response: {response}")
```

### Test Individual Components
```python
# Test MCP separately
async def test_mcp():
    client = MCPClient()
    await client.initialize()
    tools = client.get_langchain_tools()
    print(f"Tools: {[t.name for t in tools]}")

# Test without A2A
async def test_direct():
    root = CompositionRoot()
    root.initialize()
    controller = root.a2a_controller
    result = await controller.handle_message("List PDFs")
    print(f"Result: {result}")
```

## Prevention Strategies

### 1. Always Use Virtual Environment
```bash
# In every new terminal
source .venv/bin/activate
```

### 2. Validate Environment Early
```python
def _validate_environment(self):
    """Validate required environment variables."""
    required = ["GOOGLE_API_KEY", "MCP_PDF_SERVER_DIR"]
    for var in required:
        if not os.getenv(var):
            raise ValueError(f"{var} not set in environment")
```

### 3. Use Type Hints
```python
from typing import Dict, Any, Optional

async def process_message(self, message: str) -> Dict[str, Any]:
    """Type hints prevent many errors."""
```

### 4. Handle Errors at Boundaries
```python
# In adapters
try:
    result = await use_case.execute(message)
except DomainError as e:
    # Convert to protocol-specific error
    return {"error": str(e)}
```

### 5. Test Error Paths
```python
# Test with invalid input
response = await client.send_message("")  # Empty message
assert response["success"] is False

# Test with missing PDF
response = await client.send_message("Read nonexistent.pdf")
assert "not found" in response["message"].lower()
```

## Error Response Formats

### A2A Error Response
```json
{
  "contextId": "ctx-123",
  "taskId": "task-456", 
  "state": "failed",
  "error": {
    "code": "InvalidParams",
    "message": "User message cannot be empty"
  }
}
```

### Internal Error DTO
```python
UserResponseDTO(
    success=False,
    message="Error occurred",
    data=None,
    error="Specific error details"
)
```

## Summary: Most Common Issues

1. **Virtual environment not activated** - 90% of import errors
2. **Missing environment variables** - Check .env file
3. **MCP server not starting** - Check command and path
4. **LLM using wrong tool names** - Update prompt
5. **Async functions not awaited** - Add await keyword

## Next: Read 07_EXTENDING_THE_SYSTEM.md
For guidelines on adding new features while maintaining architecture.