# API Reference - Complete Function Documentation

## Context for RAG
This document provides detailed API reference for all public functions, classes, and interfaces in the Document Extraction Agent. Each entry includes parameters, return types, exceptions, and usage examples.

## Domain Layer APIs

### Document Entity

**File**: `/app/domain/entities/document.py`

```python
class Document:
    """Domain entity representing a document.
    
    Attributes:
        filename (str): Name of the document file
        content (str): Text content of the document
        created_at (datetime): When the document was created
    """
    
    def __init__(self, filename: str, content: str):
        """Initialize a document.
        
        Args:
            filename: Name of the document file (required, non-empty)
            content: Text content of the document (required, non-empty)
            
        Raises:
            ValueError: If filename or content is empty or invalid
            
        Example:
            >>> doc = Document("invoice.pdf", "Invoice content...")
            >>> print(doc.filename)
            'invoice.pdf'
        """
    
    def is_empty(self) -> bool:
        """Check if document has no meaningful content.
        
        Returns:
            bool: True if content is empty or only whitespace
            
        Example:
            >>> doc = Document("test.pdf", "   ")
            >>> doc.is_empty()
            True
        """
    
    def exceeds_size_limit(self, limit_kb: int = 350) -> bool:
        """Check if document exceeds size limit.
        
        Args:
            limit_kb: Size limit in kilobytes (default: 350)
            
        Returns:
            bool: True if document size exceeds limit
            
        Example:
            >>> doc = Document("large.pdf", "A" * 500000)
            >>> doc.exceeds_size_limit(100)
            True
        """
    
    def get_size_kb(self) -> float:
        """Get document size in kilobytes.
        
        Returns:
            float: Size in KB (UTF-8 encoded)
            
        Example:
            >>> doc = Document("test.pdf", "Hello")
            >>> doc.get_size_kb()
            0.005
        """
```

### ExtractionResult Entity

**File**: `/app/domain/entities/extraction_result.py`

```python
class DocumentType(Enum):
    """Valid document types in the system.
    
    Values:
        BILL_OF_LADING: Bill of Lading document
        INVOICE: Invoice document
        AIR_WAYBILL: Air Waybill document
        CUSTOMS_FORM: Customs form document
        UNKNOWN: Unknown document type
    """

class ExtractionResult:
    """Domain entity representing extraction results.
    
    Attributes:
        document_type (DocumentType): Type of document
        extracted_data (Dict[str, Any]): Extracted structured data
        confidence_score (float): Confidence score (0-1)
        analysis (str): Detailed analysis text
        filename (str): Source filename
        extraction_time (datetime): When extraction occurred
    """
    
    def __init__(
        self,
        document_type: DocumentType,
        extracted_data: Dict[str, Any],
        confidence_score: float,
        analysis: str,
        filename: str
    ):
        """Initialize extraction result.
        
        Args:
            document_type: Type of document (DocumentType enum)
            extracted_data: Dictionary of extracted data
            confidence_score: Confidence score between 0 and 1
            analysis: Detailed analysis text (non-empty)
            filename: Source filename
            
        Raises:
            ValueError: If confidence_score not in [0,1] or analysis empty
            
        Example:
            >>> result = ExtractionResult(
            ...     document_type=DocumentType.INVOICE,
            ...     extracted_data={"invoice_no": "INV-123"},
            ...     confidence_score=0.95,
            ...     analysis="Successfully extracted invoice",
            ...     filename="invoice.pdf"
            ... )
        """
    
    def is_high_confidence(self) -> bool:
        """Check if extraction has high confidence.
        
        Returns:
            bool: True if confidence_score >= 0.8
            
        Example:
            >>> result.confidence_score = 0.85
            >>> result.is_high_confidence()
            True
        """
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dict containing all fields with JSON-serializable values
            
        Example:
            >>> result_dict = result.to_dict()
            >>> print(result_dict["document_type"])
            'INVOICE'
        """
```

### Domain Exceptions

**File**: `/app/domain/exceptions.py`

```python
class DomainError(Exception):
    """Base exception for all domain errors.
    
    All domain-specific exceptions inherit from this.
    """

class InvalidDocumentError(DomainError):
    """Raised when document is invalid.
    
    Example:
        >>> raise InvalidDocumentError("Document is corrupted")
    """

class DocumentNotFoundError(DomainError):
    """Raised when document cannot be found.
    
    Example:
        >>> raise DocumentNotFoundError("invoice.pdf not found")
    """

class ExtractionError(DomainError):
    """Raised when extraction fails.
    
    Example:
        >>> raise ExtractionError("Failed to extract: timeout")
    """
```

## Application Layer APIs

### ExtractionAgent Port (Interface)

**File**: `/app/application/ports/extraction_agent.py`

```python
class ExtractionAgent(ABC):
    """Interface for document extraction agent.
    
    This port defines the contract that any extraction
    implementation must fulfill.
    """
    
    @abstractmethod
    async def extract(self, document: Document) -> ExtractionResult:
        """Extract structured data from a document.
        
        Args:
            document: Document entity to extract data from
            
        Returns:
            ExtractionResult: Structured extraction results
            
        Raises:
            ExtractionError: If extraction fails
            
        Contract:
            - Must handle all document types
            - Must return valid ExtractionResult
            - Must raise ExtractionError on failure
        """
    
    @abstractmethod
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message.
        
        Args:
            message: User's natural language request
            
        Returns:
            Dict with keys:
                - success (bool): Whether processing succeeded
                - message (str): Response message
                - data (Optional[Dict]): Extracted data if any
                
        Example Return:
            {
                "success": True,
                "message": "Found 3 PDFs",
                "data": {"files": ["a.pdf", "b.pdf", "c.pdf"]}
            }
        """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent with necessary resources.
        
        Called once before first use. May include:
            - Loading models
            - Connecting to services
            - Discovering tools
            
        Raises:
            InitializationError: If initialization fails
        """
```

### ProcessUserRequestUseCase

**File**: `/app/application/use_cases/process_user_request.py`

```python
class ProcessUserRequestUseCase:
    """Use case for processing natural language user requests.
    
    This is the main entry point for handling user requests
    about documents. Orchestrates the extraction agent.
    """
    
    def __init__(self, extraction_agent: ExtractionAgent):
        """Initialize with extraction agent.
        
        Args:
            extraction_agent: Implementation of ExtractionAgent port
            
        Example:
            >>> agent = LangChainExtractionAgent(...)
            >>> use_case = ProcessUserRequestUseCase(agent)
        """
    
    async def execute(self, user_message: str) -> UserResponseDTO:
        """Execute the use case - process user's request.
        
        Args:
            user_message: Natural language request from user
            
        Returns:
            UserResponseDTO with fields:
                - success (bool): Whether request succeeded
                - message (str): Response message
                - data (Optional[Dict]): Any extracted data
                - error (Optional[str]): Error message if failed
                
        Example:
            >>> response = await use_case.execute("List PDFs")
            >>> print(response.success)
            True
            >>> print(response.message)
            "Found 3 PDF files"
            
        Error Handling:
            - Returns error DTO for all exceptions
            - Never raises exceptions to caller
        """
```

### Data Transfer Objects (DTOs)

**File**: `/app/application/dto/user_response.py`

```python
@dataclass(frozen=True)
class UserResponseDTO:
    """Immutable DTO for user responses.
    
    Attributes:
        success (bool): Whether operation succeeded
        message (str): Human-readable message
        data (Optional[Dict[str, Any]]): Additional data
        error (Optional[str]): Error details if failed
    """
    
    @staticmethod
    def success_response(
        message: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> 'UserResponseDTO':
        """Factory for successful responses.
        
        Args:
            message: Success message
            data: Optional data to include
            
        Returns:
            UserResponseDTO configured for success
            
        Example:
            >>> dto = UserResponseDTO.success_response(
            ...     "Extraction complete",
            ...     {"invoice_no": "INV-123"}
            ... )
        """
    
    @staticmethod
    def error_response(error: str) -> 'UserResponseDTO':
        """Factory for error responses.
        
        Args:
            error: Error message
            
        Returns:
            UserResponseDTO configured for error
            
        Example:
            >>> dto = UserResponseDTO.error_response("File not found")
        """
```

## Adapter Layer APIs

### A2AController

**File**: `/app/adapters/controllers/a2a_controller.py`

```python
class A2AController:
    """Controller for A2A protocol requests.
    
    Adapts A2A messages to use case calls.
    """
    
    def __init__(self, process_request_use_case: ProcessUserRequestUseCase):
        """Initialize with use case.
        
        Args:
            process_request_use_case: Use case for processing requests
        """
    
    async def handle_message(self, message: str) -> Dict[str, Any]:
        """Handle incoming A2A message.
        
        Args:
            message: Natural language message from A2A protocol
            
        Returns:
            Dict with keys:
                - success (bool): Whether processing succeeded
                - message (str): Response message
                - data (Optional[Dict]): Extracted data
                - error (Optional[str]): Error if failed
                
        Example:
            >>> result = await controller.handle_message("List PDFs")
            >>> print(result["success"])
            True
            
        Note:
            Converts UserResponseDTO to dict for A2A compatibility
        """
```

### A2APresenter

**File**: `/app/adapters/presenters/a2a_presenter.py`

```python
class A2APresenter:
    """Presenter for formatting responses for A2A protocol.
    
    Converts internal response format to A2A message parts.
    """
    
    def format_response(self, result: Dict[str, Any]) -> List[Part]:
        """Format response for A2A protocol.
        
        Args:
            result: Internal response dictionary with keys:
                - message (str): Text message
                - data (Optional[Dict]): Structured data
                
        Returns:
            List[Part]: A2A message parts containing:
                - TextPart for message
                - DataPart for data (if present)
                
        Example:
            >>> parts = presenter.format_response({
            ...     "message": "Found invoice",
            ...     "data": {"invoice_no": "INV-123"}
            ... })
            >>> len(parts)
            2
            
        A2A Format:
            - TextPart: Human-readable message
            - DataPart: JSON data with MIME type
        """
```

### LangChainExtractionAgent

**File**: `/app/adapters/gateways/langchain_extraction_agent.py`

```python
class LangChainExtractionAgent(ExtractionAgent):
    """LangChain-based implementation of ExtractionAgent.
    
    Uses LangChain with Gemini LLM and MCP tools for
    document extraction and NLP processing.
    """
    
    def __init__(
        self, 
        agent_service: AgentService,
        pdf_service=None  # Deprecated
    ):
        """Initialize with agent service.
        
        Args:
            agent_service: Service providing LangChain agent
            pdf_service: Deprecated, kept for compatibility
            
        Example:
            >>> agent_service = CompositeAgentService(...)
            >>> agent = LangChainExtractionAgent(agent_service)
        """
    
    async def initialize(self) -> None:
        """Initialize the agent with MCP tools.
        
        Performs:
            1. Initializes agent service (starts MCP)
            2. Creates agent executor
            
        Raises:
            InitializationError: If MCP or LangChain fails
            
        Note:
            Called automatically on first request if not called manually
        """
    
    async def extract(self, document: Document) -> ExtractionResult:
        """Extract structured data from document.
        
        Args:
            document: Document entity to process
            
        Returns:
            ExtractionResult with extracted data
            
        Raises:
            ExtractionError: If extraction fails
            
        Example:
            >>> doc = Document("invoice.pdf", "Invoice content...")
            >>> result = await agent.extract(doc)
            >>> print(result.document_type)
            DocumentType.INVOICE
        """
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process natural language message.
        
        Args:
            message: User's request in natural language
            
        Returns:
            Dict with keys:
                - success (bool): Whether processing succeeded
                - message (str): LLM's response
                - data (Optional[Dict]): Extracted JSON data
                
        Example:
            >>> result = await agent.process_message("List PDFs")
            >>> print(result["message"])
            "I found 3 PDF files: invoice.pdf, report.pdf..."
            
        LLM Behavior:
            - Automatically selects appropriate MCP tools
            - Formats response in natural language
            - Extracts JSON data when relevant
        """
```

## Infrastructure Layer APIs

### MCPClient

**File**: `/app/infrastructure/external_services/mcp_client.py`

```python
class MCPClient:
    """MCP client for tool integration.
    
    Manages connection to MCP server and provides
    tools as LangChain-compatible format.
    """
    
    def __init__(self):
        """Initialize MCP client.
        
        Reads configuration from environment:
            - MCP_PDF_SERVER_DIR: PDF directory path
            - MCP_PDF_SERVER_COMMAND: Command to run server
            - MCP_PDF_SERVER_ARGS: Server arguments
            - MCP_PDF_TRANSPORT: Transport type (stdio/http)
        """
    
    async def initialize(self) -> None:
        """Initialize connection to MCP server.
        
        Performs:
            1. Starts MCP server subprocess
            2. Establishes communication
            3. Discovers available tools
            
        Raises:
            RuntimeError: If server fails to start
            
        Example:
            >>> client = MCPClient()
            >>> await client.initialize()
            >>> print(f"Tools: {len(client.tools)}")
            Tools: 2
            
        Tools Discovered:
            - read_doc_contents: Read PDF content
            - list_available_pdfs: List PDFs
        """
    
    def get_langchain_tools(self) -> List[BaseTool]:
        """Get MCP tools as LangChain tools.
        
        Returns:
            List[BaseTool]: Tools compatible with LangChain
            
        Raises:
            RuntimeError: If not initialized
            
        Example:
            >>> tools = client.get_langchain_tools()
            >>> for tool in tools:
            ...     print(f"{tool.name}: {tool.description}")
        """
    
    async def close(self) -> None:
        """Close MCP client connection.
        
        Shuts down MCP server subprocess cleanly.
        """
```

### CompositeAgentService

**File**: `/app/infrastructure/external_services/composite_agent_service.py`

```python
class CompositeAgentService(AgentService):
    """Combines MCP tools with LangChain agent.
    
    Orchestrates initialization of MCP and LangChain
    to create a tool-enabled agent.
    """
    
    def __init__(
        self, 
        mcp_client: MCPClient,
        langchain_setup: LangChainSetup
    ):
        """Initialize with MCP and LangChain.
        
        Args:
            mcp_client: Client for MCP tools
            langchain_setup: LangChain configuration
        """
    
    async def initialize(self) -> None:
        """Initialize MCP and set tools in LangChain.
        
        Flow:
            1. Initialize MCP (starts server, gets tools)
            2. Get tools as LangChain format
            3. Set tools in LangChain agent
            
        Example:
            >>> service = CompositeAgentService(mcp, langchain)
            >>> await service.initialize()
        """
    
    def create_agent_executor(self) -> AgentExecutor:
        """Create agent executor with tools.
        
        Returns:
            AgentExecutor: Configured LangChain agent
            
        Note:
            Agent has access to all MCP tools
        """
```

### A2A Executor Adapter

**File**: `/app/infrastructure/web/a2a_executor_adapter.py`

```python
class CleanArchitectureA2AExecutor(AgentExecutor):
    """Adapts Clean Architecture to A2A protocol.
    
    Bridge between A2A server expectations and our
    controller/presenter architecture.
    """
    
    def __init__(
        self,
        controller: Controller,
        presenter: Presenter
    ):
        """Initialize with controller and presenter.
        
        Args:
            controller: Handles business logic
            presenter: Formats responses
        """
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """Execute A2A task.
        
        Args:
            context: A2A request context containing:
                - message: User's message
                - current_task: Task tracking info
            event_queue: Queue for sending responses
            
        Flow:
            1. Extract message from A2A format
            2. Create/update task
            3. Send "working" status
            4. Process with controller
            5. Format with presenter
            6. Send completed response
            
        Raises:
            ServerError: A2A protocol errors
            
        Example A2A Message:
            {
                "message": {
                    "parts": [{
                        "root": {"text": "List PDFs"}
                    }]
                }
            }
        """
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """Cancel A2A task (not supported).
        
        Raises:
            UnsupportedOperationError: Always
        """
```

## Composition Root API

**File**: `/app/main/composition_root.py`

```python
class CompositionRoot:
    """Central dependency injection container.
    
    The ONLY place where concrete implementations
    are instantiated and wired together.
    """
    
    def __init__(self):
        """Initialize empty composition root."""
    
    def initialize(self) -> None:
        """Initialize all components in correct order.
        
        Order:
            1. Infrastructure services (MCP, LangChain)
            2. Adapters (gateways)
            3. Use cases
            4. Controllers and presenters
            
        Example:
            >>> root = CompositionRoot()
            >>> root.initialize()
        """
    
    @property
    def a2a_controller(self) -> A2AController:
        """Get A2A controller (lazy init)."""
    
    @property
    def a2a_presenter(self) -> A2APresenter:
        """Get A2A presenter (lazy init)."""
    
    async def shutdown(self) -> None:
        """Cleanup resources when shutting down.
        
        Closes:
            - MCP client connections
            - Any open resources
        """

def get_composition_root() -> CompositionRoot:
    """Get or create global composition root.
    
    Returns:
        CompositionRoot: Singleton instance
        
    Example:
        >>> root = get_composition_root()
        >>> controller = root.a2a_controller
    """

async def shutdown_composition_root() -> None:
    """Shutdown global composition root.
    
    Example:
        >>> await shutdown_composition_root()
    """
```

## Entry Points

### Main Server Entry

**File**: `__main__.py`

```python
if __name__ == "__main__":
    """Start the A2A server.
    
    Usage:
        python __main__.py
        
    Starts:
        - A2A server on port 8080
        - MCP client (on first request)
        - All configured services
    """
    from app.main.a2a_main import run_server
    run_server()
```

### A2A Client Entry

**File**: `a2a_client.py`

```python
async def main():
    """Run A2A client for testing.
    
    Usage:
        python a2a_client.py          # Interactive mode
        python a2a_client.py --test   # Run tests
        
    Interactive Mode:
        - Type messages to send to agent
        - See responses in real-time
        - Type 'exit' to quit
        
    Test Mode:
        - Runs predefined test messages
        - Shows all responses
        - Exits automatically
    """
```

## Usage Examples

### Basic Usage
```python
# Start server
$ python __main__.py

# In another terminal, use client
$ python a2a_client.py
You: List available PDFs
Agent: I found 3 PDF files: invoice.pdf, report.pdf, contract.pdf

You: Read invoice.pdf
Agent: Here's the content of invoice.pdf: [content]
```

### Programmatic Usage
```python
# Direct use (not recommended in production)
from app.main.composition_root import get_composition_root

async def example():
    root = get_composition_root()
    controller = root.a2a_controller
    
    result = await controller.handle_message("List PDFs")
    print(result["message"])
```

### Testing Individual Components
```python
# Test MCP tools
from app.infrastructure.external_services import MCPClient

async def test_mcp():
    client = MCPClient()
    await client.initialize()
    
    tools = client.get_langchain_tools()
    print(f"Available tools: {[t.name for t in tools]}")
    
    await client.close()
```

## Summary

The API follows Clean Architecture principles:
1. **Domain** - Pure business entities and logic
2. **Application** - Use cases and interfaces (ports)
3. **Adapters** - Implementations and protocol adapters
4. **Infrastructure** - External service integrations

All components are wired in the composition root and accessed through well-defined interfaces.