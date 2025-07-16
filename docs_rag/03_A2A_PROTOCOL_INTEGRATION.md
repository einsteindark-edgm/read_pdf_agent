# A2A Protocol Integration - Complete Implementation Guide

## Context for RAG
This document details the A2A (Agent-to-Agent) protocol integration in the Document Extraction Agent. A2A is a standardized protocol for AI agents to communicate. This implementation uses the official A2A Python library.

## What is A2A Protocol?

### Purpose
A2A enables standardized communication between AI agents using:
- **Agent Cards** - JSON metadata describing agent capabilities
- **Structured Messages** - Typed message format with parts
- **Task Management** - Built-in task states and updates
- **Event Queues** - Async communication patterns

### CRITICAL: A2A vs REST API
- A2A is NOT a REST API
- Uses specific message formats
- Has built-in task management
- Requires agent card at `/.well-known/agent.json`

## Entry Point Implementation

### Main Entry Point
**File**: `/__main__.py`
```python
"""Entry point for A2A Document Extraction Server."""
from app.main.a2a_main import run_server

if __name__ == "__main__":
    # CRITICAL: This starts the A2A server, not a regular HTTP server
    run_server()
```

### A2A Server Setup
**File**: `/app/main/a2a_main.py`
```python
import asyncio
import logging
from uvicorn import Config, Server

from app.main.composition_root import get_composition_root, shutdown_composition_root
from app.infrastructure.a2a import get_agent_card
from app.infrastructure.web.a2a_executor_adapter import CleanArchitectureA2AExecutor
from app.infrastructure.config import settings

# CRITICAL: Import A2A components
from a2a.server import A2AStarletteApplication, DefaultRequestHandler

logger = logging.getLogger(__name__)

def create_a2a_app():
    """Create A2A application with Clean Architecture integration.
    
    CRITICAL STEPS:
    1. Get composition root (dependency injection)
    2. Create executor adapter
    3. Create A2A handler
    4. Create A2A application
    """
    # Get the initialized composition root
    root = get_composition_root()
    
    # Create our A2A executor adapter
    # ADAPTER PATTERN: Adapts our Clean Architecture to A2A protocol
    executor = CleanArchitectureA2AExecutor(
        controller=root.a2a_controller,
        presenter=root.a2a_presenter
    )
    
    # Create A2A handler with our executor
    # CRITICAL: DefaultRequestHandler manages A2A protocol details
    handler = DefaultRequestHandler(agent_executor=executor)
    
    # Get agent card
    # METADATA: Describes our agent's capabilities
    agent_card = get_agent_card()
    
    # Create A2A application
    # FRAMEWORK: Starlette-based ASGI application
    app = A2AStarletteApplication(
        request_handler=handler,
        agent_card=agent_card
    )
    
    return app

async def run_server():
    """Run the A2A server with proper lifecycle management.
    
    LIFECYCLE:
    1. Initialize composition root
    2. Create A2A app
    3. Start server
    4. Handle shutdown gracefully
    """
    try:
        logger.info("🚀 Starting A2A Document Extraction Server...")
        
        # Initialize composition root
        # DEPENDENCY INJECTION: All dependencies created here
        root = get_composition_root()
        
        # Create app
        app = create_a2a_app()
        
        # Configure server
        # CRITICAL: Must use port 8080 for A2A by default
        config = Config(
            app=app,
            host=settings.HOST,  # Default: 0.0.0.0
            port=settings.PORT,  # Default: 8080
            log_level="info"
        )
        
        server = Server(config)
        
        # Run server
        logger.info(f"🌟 A2A server running at http://{settings.HOST}:{settings.PORT}")
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        # Cleanup
        await shutdown_composition_root()
```

### ERROR: Common A2A Server Mistakes
1. **Wrong port** - A2A typically uses 8080
2. **Missing agent card** - Server won't start properly
3. **Not using A2AStarletteApplication** - Regular FastAPI won't work
4. **Forgetting async lifecycle** - Causes resource leaks

## Agent Card Implementation

### Agent Card Definition
**File**: `/app/infrastructure/a2a/card.py`
```python
from a2a.types import AgentCard

def get_agent_card() -> AgentCard:
    """Get the agent card for our document extraction agent.
    
    CRITICAL: This metadata is served at /.well-known/agent.json
    and tells other agents what we can do.
    """
    return AgentCard(
        # Basic metadata
        name="Document Extraction Agent",
        description="AI agent for extracting structured data from PDF documents",
        version="1.0.0",
        
        # Capabilities
        capabilities=[
            "pdf-extraction",
            "document-analysis",
            "structured-data-extraction"
        ],
        
        # Supported document types
        metadata={
            "supported_documents": [
                "bill_of_lading",
                "invoice", 
                "air_waybill",
                "customs_form"
            ],
            "llm_model": "gemini-2.0-flash-exp",
            "extraction_method": "mcp-tools"
        }
    )
```

### ERROR: Agent Card Mistakes
1. **Invalid metadata** - Must be JSON-serializable
2. **Missing required fields** - name, description, version required
3. **Not accessible at /.well-known/agent.json** - A2A standard

## A2A Executor Implementation

### Executor Adapter
**File**: `/app/infrastructure/web/a2a_executor_adapter.py`
```python
from typing import Dict, Any, Protocol, List
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, InvalidParamsError, InternalError
from a2a.utils import new_agent_text_message, new_agent_parts_message, new_data_artifact, new_task
from a2a.utils.errors import ServerError
import logging

# PROTOCOLS: Define expected interfaces
class Controller(Protocol):
    """Protocol for controller."""
    async def handle_message(self, message: str) -> Dict[str, Any]: ...

class MessagePart(Protocol):
    """Protocol for message part."""
    root: Any

class Presenter(Protocol):
    """Protocol for presenter."""
    def format_response(self, result: Dict[str, Any]) -> List[MessagePart]: ...

class CleanArchitectureA2AExecutor(AgentExecutor):
    """A2A executor that adapts Clean Architecture to A2A protocol.
    
    CRITICAL: This is the bridge between A2A protocol and our
    Clean Architecture implementation.
    """
    
    def __init__(self, controller: Controller, presenter: Presenter):
        """Initialize with controller and presenter.
        
        DEPENDENCY INJECTION: We depend on protocols, not concrete classes.
        """
        self.controller = controller
        self.presenter = presenter
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute A2A task.
        
        PROTOCOL IMPLEMENTATION: This method is called by A2A
        when a message is received.
        
        Args:
            context: Request context with message and task info
            event_queue: Queue for sending events back to client
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Extract message from context
            # CRITICAL: Must handle A2A message format
            user_message = self._extract_user_message(context)
            if not user_message:
                raise ServerError(error=InvalidParamsError())
            
            # Get or create task
            # TASK MANAGEMENT: A2A tracks task states
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            # Create TaskUpdater for managing responses
            # STATUS UPDATES: Keeps client informed
            updater = TaskUpdater(event_queue, task.id, task.contextId)
            
            # Send initial status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "🤖 Processing your request...",
                    task.contextId,
                    task.id
                )
            )
            
            # Use controller to handle the message
            # CLEAN ARCHITECTURE: Controller handles business logic
            result = await self.controller.handle_message(user_message)
            
            # Use presenter to format response
            # CLEAN ARCHITECTURE: Presenter formats for A2A
            message_parts = self.presenter.format_response(result)
            
            # Convert to A2A format
            # PROTOCOL ADAPTATION: Our format to A2A format
            a2a_parts = []
            for part in message_parts:
                if hasattr(part.root, 'text'):
                    a2a_parts.append(part.root.text)
                elif hasattr(part.root, 'data'):
                    artifact = new_data_artifact(
                        part.root.data,
                        part.root.mimeType,
                        part.root.name
                    )
                    a2a_parts.append(artifact)
            
            # Create response message
            if len(a2a_parts) > 1:
                response = new_agent_parts_message(
                    a2a_parts,
                    task.contextId,
                    task.id
                )
            else:
                response = new_agent_text_message(
                    a2a_parts[0] if a2a_parts else "No response",
                    task.contextId,
                    task.id
                )
            
            # Send final response
            # TASK COMPLETION: Mark as completed with response
            await updater.update_status(
                TaskState.completed,
                response,
                final=True
            )
            
        except ServerError:
            # A2A errors are re-raised
            raise
        except Exception as e:
            # Unexpected errors wrapped in A2A format
            logger.error(f"Error in CleanArchitectureA2AExecutor: {e}", exc_info=True)
            raise ServerError(error=InternalError())
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel A2A task.
        
        PROTOCOL REQUIREMENT: Must implement cancel method.
        """
        from a2a.types import UnsupportedOperationError
        raise ServerError(error=UnsupportedOperationError())
    
    def _extract_user_message(self, context: RequestContext) -> str:
        """Extract user message from A2A context.
        
        MESSAGE FORMAT: A2A messages have parts with text/data.
        """
        if not context.message:
            return ""
        
        # Extract text from message parts
        if hasattr(context.message, 'parts') and context.message.parts:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    return part.root.text
        
        return ""
```

### ERROR: A2A Executor Common Mistakes
1. **Not handling task states** - Client expects status updates
2. **Wrong message extraction** - A2A has specific format
3. **Not using TaskUpdater** - Status updates won't work
4. **Forgetting error transformation** - Must use ServerError

## A2A Message Flow

### Incoming Message Processing
```
1. Client sends A2A message to server
2. A2AStarletteApplication receives request
3. DefaultRequestHandler validates and parses
4. CleanArchitectureA2AExecutor.execute() called
5. Message extracted from A2A format
6. Controller processes message
7. Presenter formats response
8. Response sent via event queue
```

### Message Format Examples

#### Incoming A2A Message
```json
{
  "contextId": "ctx-123",
  "taskId": "task-456",
  "message": {
    "parts": [
      {
        "root": {
          "text": "List available PDFs"
        }
      }
    ]
  }
}
```

#### Outgoing A2A Response
```json
{
  "contextId": "ctx-123",
  "taskId": "task-456",
  "state": "completed",
  "message": {
    "parts": [
      {
        "root": {
          "text": "Found 3 PDF files"
        }
      },
      {
        "root": {
          "data": "[\"invoice.pdf\", \"report.pdf\", \"contract.pdf\"]",
          "mimeType": "application/json",
          "name": "pdf_list"
        }
      }
    ]
  }
}
```

## Testing A2A Integration

### A2A Client Implementation
**File**: `/a2a_client.py`
```python
"""Test client for Document Extraction Agent."""
import asyncio
import sys

from app.a2a.client_cli.interaction import DocumentExtractionInteraction

async def main():
    """Main entry point for test client.
    
    USAGE:
    - python3 a2a_client.py          # Interactive mode
    - python3 a2a_client.py --test   # Run automated tests
    """
    interaction = DocumentExtractionInteraction()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated tests
        await interaction.run_tests()
    else:
        # Run interactive session
        await interaction.interactive_session()

if __name__ == "__main__":
    print("🚀 A2A Document Extraction Client")
    print("Make sure the A2A server is running: python __main__.py")
    print("Run with --test flag for automated tests\n")
    
    asyncio.run(main())
```

### Client Interaction Handler
**File**: `/app/a2a/client_cli/interaction.py`
```python
from typing import Optional
from app.a2a import DocumentExtractionClient

class DocumentExtractionInteraction:
    """Handles interaction with the Document Extraction Agent.
    
    TESTING: Provides both interactive and automated testing.
    """
    
    def __init__(self, agent_url: str = "http://localhost:8080"):
        """Initialize with agent URL.
        
        DEFAULT: Assumes A2A server at localhost:8080
        """
        self.client = DocumentExtractionClient(agent_url)
    
    async def interactive_session(self):
        """Run interactive session with the agent.
        
        INTERACTIVE: User types messages, sees responses.
        """
        print("🔗 Connecting to agent...")
        
        try:
            await self.client.connect()
            print("✅ Connected! Type 'exit' to quit.\n")
            
            while True:
                # Get user input
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                if not user_input:
                    continue
                
                # Send to agent
                print("Agent: ", end="", flush=True)
                response = await self.client.send_message(user_input)
                print(response)
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await self.client.close()
    
    async def run_tests(self):
        """Run automated tests.
        
        AUTOMATED: Tests common scenarios.
        """
        test_messages = [
            "What PDFs are available?",
            "Read invoice.pdf",
            "Extract data from the first available PDF"
        ]
        
        try:
            await self.client.connect()
            print("✅ Connected to agent\n")
            
            for msg in test_messages:
                print(f"Test: {msg}")
                response = await self.client.send_message(msg)
                print(f"Response: {response}\n")
                await asyncio.sleep(1)  # Rate limiting
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            await self.client.close()
```

### ERROR: A2A Client Common Issues
1. **Server not running** - Start server first
2. **Wrong URL** - Default is http://localhost:8080
3. **Missing virtual environment** - A2A library required
4. **Rate limiting** - Don't spam the server

## A2A Protocol Benefits

### Why Use A2A?
1. **Standardized** - Works with any A2A-compatible agent
2. **Task Management** - Built-in state tracking
3. **Event-Driven** - Async by design
4. **Type-Safe** - Strong typing with protocol

### When NOT to Use A2A
1. **Simple REST APIs** - Overkill for basic CRUD
2. **Non-Agent Systems** - Designed for AI agents
3. **Synchronous Only** - A2A is async-first

## Integration Summary

### Key Components
1. **A2AStarletteApplication** - ASGI app for A2A
2. **DefaultRequestHandler** - Handles A2A protocol
3. **CleanArchitectureA2AExecutor** - Our adapter
4. **Agent Card** - Metadata about capabilities
5. **Task Management** - State tracking

### Flow Summary
```
Client → A2A Protocol → Executor Adapter → Controller → Use Case → Agent
   ↑                                                                    ↓
   ←────────────── Event Queue ←── Presenter ←── Response ←────────────
```

## Next: Read 04_MCP_INTEGRATION.md
To understand how MCP tools are integrated for PDF operations.