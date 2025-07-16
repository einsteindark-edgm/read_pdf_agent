# Complete Execution Flow - End-to-End Request Processing

## Context for RAG
This document traces the complete execution flow from server startup to request processing. Understanding this flow is CRITICAL for debugging and extending the system. Each step includes the actual code being executed.

## Server Startup Flow

### 1. Entry Point Execution
**File**: `__main__.py`
```python
from app.main.a2a_main import run_server

if __name__ == "__main__":
    run_server()
```

### 2. Server Initialization
**File**: `/app/main/a2a_main.py` → `run_server()`
```python
async def run_server():
    """Run the A2A server with proper lifecycle management."""
    try:
        logger.info("🚀 Starting A2A Document Extraction Server...")
        
        # Step 2.1: Get composition root (singleton)
        root = get_composition_root()
        
        # Step 2.2: Create A2A application
        app = create_a2a_app()
        
        # Step 2.3: Configure ASGI server
        config = Config(
            app=app,
            host="0.0.0.0",
            port=8080,
            log_level="info"
        )
        
        server = Server(config)
        
        # Step 2.4: Start server
        logger.info(f"🌟 A2A server running at http://0.0.0.0:8080")
        await server.serve()
```

### 3. Composition Root Initialization
**File**: `/app/main/composition_root.py` → `get_composition_root()`
```python
def get_composition_root() -> CompositionRoot:
    """Get or create the global composition root instance."""
    global _composition_root
    
    if _composition_root is None:
        _composition_root = CompositionRoot()
        _composition_root.initialize()  # Step 3.1
    
    return _composition_root
```

### 4. Dependency Creation
**File**: `/app/main/composition_root.py` → `CompositionRoot.initialize()`
```python
def initialize(self) -> None:
    """Initialize all components in the correct order."""
    if self._initialized:
        return
    
    logger.info("Initializing composition root...")
    
    # Step 4.1: Create infrastructure services
    self._create_infrastructure_services()
    
    # Step 4.2: Create adapters
    self._create_adapters()
    
    # Step 4.3: Create use cases
    self._create_use_cases()
    
    # Step 4.4: Create controllers and presenters
    self._create_controllers_and_presenters()
    
    self._initialized = True
```

### 5. Infrastructure Services Creation
```python
def _create_infrastructure_services(self) -> None:
    """Create all infrastructure services."""
    # Step 5.1: Create MCP client
    self._mcp_client = MCPClient()
    
    # Step 5.2: Create LangChain setup
    self._langchain_setup = LangChainSetup()
    
    # Step 5.3: Create composite agent service
    self._agent_service = CompositeAgentService(
        self._mcp_client,
        self._langchain_setup
    )
```

### 6. MCP Initialization (Lazy)
**Note**: MCP is NOT initialized at startup. It's initialized on first request.

## Request Processing Flow

### 1. Client Sends Request
**Example Request**:
```bash
curl -X POST http://localhost:8080/agent/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{
        "root": {
          "text": "List available PDFs"
        }
      }]
    }
  }'
```

### 2. A2A Framework Receives Request
**Framework Flow** (handled by A2A library):
1. `A2AStarletteApplication` receives POST
2. `DefaultRequestHandler` parses message
3. Creates `RequestContext` with message
4. Calls our executor

### 3. Executor Adapter Processes Request
**File**: `/app/infrastructure/web/a2a_executor_adapter.py` → `execute()`
```python
async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    """Execute A2A task."""
    logger = logging.getLogger(__name__)
    
    try:
        # Step 3.1: Extract user message
        user_message = self._extract_user_message(context)
        if not user_message:
            raise ServerError(error=InvalidParamsError())
        
        # Step 3.2: Get or create task
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        # Step 3.3: Create task updater
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        # Step 3.4: Send initial status
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                "🤖 Processing your request...",
                task.contextId,
                task.id
            )
        )
        
        # Step 3.5: Process with controller
        result = await self.controller.handle_message(user_message)
        
        # Step 3.6: Format response
        message_parts = self.presenter.format_response(result)
        
        # ... (response formatting continues)
```

### 4. Controller Handles Message
**File**: `/app/adapters/controllers/a2a_controller.py` → `handle_message()`
```python
async def handle_message(self, message: str) -> Dict[str, Any]:
    """Handle incoming A2A message."""
    # Step 4.1: Execute use case
    response_dto = await self.process_request_use_case.execute(message)
    
    # Step 4.2: Convert DTO to dictionary
    return {
        "success": response_dto.success,
        "message": response_dto.message,
        "data": response_dto.data,
        "error": response_dto.error
    }
```

### 5. Use Case Executes Business Logic
**File**: `/app/application/use_cases/process_user_request.py` → `execute()`
```python
async def execute(self, user_message: str) -> UserResponseDTO:
    """Execute the use case - process user's request."""
    try:
        # Step 5.1: Validate input
        if not user_message or not user_message.strip():
            raise UseCaseExecutionError("User message cannot be empty")
        
        # Step 5.2: Initialize agent if needed (FIRST TIME ONLY)
        if not self._initialized:
            try:
                await self.extraction_agent.initialize()
                self._initialized = True
            except Exception as e:
                raise InitializationError(f"Failed to initialize extraction agent: {str(e)}") from e
        
        # Step 5.3: Process message with agent
        try:
            result = await self.extraction_agent.process_message(user_message)
        except Exception as e:
            raise UseCaseExecutionError(f"Agent failed to process message: {str(e)}") from e
        
        # Step 5.4: Return DTO
        return UserResponseDTO.success_response(
            message=result.get("message", "Request processed successfully"),
            data=result.get("data")
        )
```

### 6. Extraction Agent Initialization (First Time)
**File**: `/app/adapters/gateways/langchain_extraction_agent.py` → `initialize()`
```python
async def initialize(self) -> None:
    """Initialize the agent with MCP tools."""
    if self._initialized:
        return
    
    # Step 6.1: Initialize agent service
    if hasattr(self.agent_service, 'initialize'):
        await self.agent_service.initialize()
    
    # Step 6.2: Create agent executor
    self.agent_executor = self.agent_service.create_agent_executor()
    
    self._initialized = True
```

### 7. Composite Agent Service Initialization
**File**: `/app/infrastructure/external_services/composite_agent_service.py` → `initialize()`
```python
async def initialize(self) -> None:
    """Initialize MCP and set tools in LangChain."""
    if self._initialized:
        return
    
    # Step 7.1: Initialize MCP client (STARTS MCP SERVER)
    await self.mcp_client.initialize()
    
    # Step 7.2: Get tools from MCP
    tools = self.mcp_client.get_langchain_tools()
    
    # Step 7.3: Set tools in LangChain
    self.langchain_setup.set_tools(tools)
    
    self._initialized = True
```

### 8. MCP Client Initialization
**File**: `/app/infrastructure/external_services/mcp_client.py` → `initialize()`
```python
async def initialize(self) -> None:
    """Initialize connection to MCP server."""
    try:
        logger.info("Initializing MCP PDF server connection...")
        
        # Step 8.1: Build command args
        args = []
        if self.mcp_directory:
            args.extend(["--directory", self.mcp_directory])
        args.extend(self.mcp_args)
        
        # Step 8.2: Configure MCP client
        config = {
            "pdf-extractor": {
                "command": self.mcp_command,
                "args": args,
                "transport": self.mcp_transport,
                "env": {}
            }
        }
        
        # Step 8.3: Create client (STARTS SUBPROCESS)
        self.client = MultiServerMCPClient(config)
        
        # Step 8.4: Get tools from server
        self.tools = await self.client.get_tools()
        
        logger.info(f"MCP server initialized with {len(self.tools)} tools: {[t.name for t in self.tools]}")
```

### 9. Agent Processes Message
**File**: `/app/adapters/gateways/langchain_extraction_agent.py` → `process_message()`
```python
async def process_message(self, message: str) -> Dict[str, Any]:
    """Process a natural language message using LangChain agent."""
    try:
        # Step 9.1: Invoke LangChain agent
        result = await self.agent_executor.ainvoke({"input": message})
        
        # Step 9.2: Extract output
        output = result.get("output", "")
        
        # Step 9.3: Structure response
        response = {
            "success": True,
            "message": output,
            "data": None
        }
        
        # Step 9.4: Extract JSON if present
        if "{" in output and "}" in output:
            try:
                json_data = self._extract_json_from_response(output)
                if json_data:
                    response["data"] = json_data
            except:
                pass
        
        return response
```

### 10. LangChain Agent Reasoning
**Internal LangChain Flow**:
```
1. Agent receives: {"input": "List available PDFs"}
2. Formats prompt with available tools
3. Sends to Gemini LLM
4. LLM responds:
   Thought: I need to list the available PDF files
   Action: list_available_pdfs
   Action Input: {}
5. Parser extracts action
6. Tool invoked via MCP
7. Result returned to agent
8. Agent formats final answer
```

### 11. MCP Tool Invocation
**MCP Flow**:
```
1. LangChain calls tool.ainvoke({})
2. MCP client sends request to server
3. MCP server executes tool
4. Returns result: {"pdfs": ["invoice.pdf", "report.pdf"]}
5. Result passed back to agent
```

### 12. Response Formatting
**File**: `/app/adapters/presenters/a2a_presenter.py` → `format_response()`
```python
def format_response(self, result: Dict[str, Any]) -> List[Part]:
    """Format response for A2A protocol."""
    parts = []
    
    # Step 12.1: Add message as text part
    if "message" in result:
        parts.append(
            Part(root=TextPart(text=result["message"]))
        )
    
    # Step 12.2: Add data as data part
    if result.get("data"):
        parts.append(
            Part(root=DataPart(
                data=json.dumps(result["data"], indent=2),
                mimeType="application/json",
                name="extraction_result"
            ))
        )
    
    return parts
```

### 13. A2A Response Sent
**Final A2A Response**:
```json
{
  "contextId": "ctx-123",
  "taskId": "task-456",
  "state": "completed",
  "message": {
    "parts": [
      {
        "root": {
          "text": "I found 2 PDF files available:\n- invoice.pdf\n- report.pdf"
        }
      },
      {
        "root": {
          "data": "[\"invoice.pdf\", \"report.pdf\"]",
          "mimeType": "application/json",
          "name": "extraction_result"
        }
      }
    ]
  }
}
```

## Complete Flow Diagram

```
CLIENT                          SERVER                              INFRASTRUCTURE
  |                               |                                      |
  |------ POST /agent/messages -->|                                      |
  |                               |                                      |
  |                               |--- A2AStarletteApplication          |
  |                               |    DefaultRequestHandler            |
  |                               |    CleanArchitectureA2AExecutor --->|
  |                               |                                      |
  |                               |<--- Extract Message                 |
  |                               |     Create Task                     |
  |                               |     Send "Processing..." Status     |
  |                               |                                      |
  |                               |--- A2AController.handle_message --->|
  |                               |                                      |
  |                               |<--- ProcessUserRequestUseCase       |
  |                               |     (First time: Initialize)        |
  |                               |                                      |
  |                               |                          MCP Init -->|--- Start MCP Server
  |                               |                                      |<-- Get Tools
  |                               |                                      |
  |                               |<--- LangChainExtractionAgent        |
  |                               |     agent_executor.ainvoke()        |
  |                               |                                      |
  |                               |                       LangChain ---->|--- Gemini LLM
  |                               |                                      |<-- "Use list_pdfs"
  |                               |                                      |
  |                               |                          MCP Tool -->|--- MCP Server
  |                               |                                      |<-- Tool Result
  |                               |                                      |
  |                               |<--- Format Response                  |
  |                               |     A2APresenter                     |
  |                               |                                      |
  |<------ A2A Response -----------|                                      |
  |       (Task Completed)         |                                      |
```

## Critical Initialization Order

### First Request is Special
1. **MCP NOT started at server startup** - Lazy initialization
2. **First request triggers**:
   - MCP server subprocess start
   - Tool discovery
   - LangChain agent creation
3. **Subsequent requests** use already initialized components

### ERROR: Common Flow Issues
1. **MCP fails to start** - First request fails
2. **No tools discovered** - Agent has nothing to work with
3. **LLM timeout** - Gemini might be slow
4. **Tool invocation fails** - MCP server error

## Performance Characteristics

### Startup Time
- **Server startup**: ~1 second (just ASGI server)
- **First request**: ~3-5 seconds (MCP init + tool discovery)
- **Subsequent requests**: ~1-2 seconds (just LLM + tool calls)

### Memory Usage
- **Base server**: ~50MB
- **With MCP**: ~100MB (subprocess)
- **After LangChain init**: ~200MB

### Concurrency
- **A2A server**: Async, handles multiple requests
- **MCP client**: Single connection, queued requests
- **LangChain**: Thread-safe, but LLM calls are sequential

## Debugging the Flow

### Enable Verbose Logging
```python
# In langchain_setup.py
agent_executor = LangChainAgentExecutor(
    verbose=True,  # Shows all reasoning steps
    # ...
)
```

### Check MCP Connection
```python
# Add logging in mcp_client.py
logger.info(f"MCP tools discovered: {[t.name for t in self.tools]}")
```

### Monitor A2A Events
```python
# In executor adapter
logger.info(f"Task state: {task.state}")
logger.info(f"User message: {user_message}")
```

### Common Debug Points
1. **MCP init fails** - Check `mcp_client.py` → `initialize()`
2. **No tools available** - Check `composite_agent_service.py`
3. **LLM errors** - Check `langchain_setup.py` prompts
4. **Parser errors** - Check `pydantic_parser.py`

## Error Handling Flow

### Layer-by-Layer Error Handling
1. **Domain** - Raises `DomainError` subclasses
2. **Application** - Catches and wraps in `ApplicationError`
3. **Adapters** - Convert to protocol-specific errors
4. **Infrastructure** - Handles framework errors
5. **A2A** - Converts to `ServerError` with proper codes

### Example Error Flow
```
PDFNotFoundError (Domain)
  ↓
UseCaseExecutionError (Application)
  ↓
Controller returns error DTO
  ↓
A2A formats as error response
  ↓
Client receives structured error
```

## Summary: Key Execution Points

1. **Server Start**: `__main__.py` → `run_server()`
2. **Dependency Setup**: `CompositionRoot.initialize()`
3. **Request Entry**: `CleanArchitectureA2AExecutor.execute()`
4. **Business Logic**: `ProcessUserRequestUseCase.execute()`
5. **MCP Init**: `MCPClient.initialize()` (first request only)
6. **LLM Processing**: `LangChainExtractionAgent.process_message()`
7. **Tool Usage**: LangChain → MCP tools
8. **Response Format**: `A2APresenter.format_response()`

## Next: Read 06_COMMON_ERRORS_AND_FIXES.md
For comprehensive error scenarios and solutions.