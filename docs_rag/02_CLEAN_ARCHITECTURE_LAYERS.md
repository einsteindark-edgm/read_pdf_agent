# Clean Architecture Implementation - Detailed Layer Documentation

## Context for RAG
This document details the Clean Architecture implementation in the Document Extraction Agent. Each layer has specific responsibilities and strict dependency rules. Understanding these layers is CRITICAL for maintaining the architecture.

## Layer 1: Domain Layer (innermost)

### Location: `/app/domain/`

### Purpose
Contains business entities and domain-specific logic. This layer knows NOTHING about external frameworks, databases, or protocols.

### Domain Entities

#### Document Entity
**File**: `/app/domain/entities/document.py`
```python
from typing import Optional
from datetime import datetime

class Document:
    """Domain entity representing a document.
    
    CRITICAL: This is a domain entity, not a data transfer object.
    It contains business logic and validation.
    """
    
    def __init__(self, filename: str, content: str):
        """Initialize document with validation.
        
        Args:
            filename: Name of the document file
            content: Text content of the document
            
        Raises:
            ValueError: If filename or content is invalid
        """
        if not filename or not filename.strip():
            raise ValueError("Document filename cannot be empty")
        
        if not content or not content.strip():
            raise ValueError("Document content cannot be empty")
        
        self.filename = filename.strip()
        self.content = content.strip()
        self.created_at = datetime.utcnow()
    
    def is_empty(self) -> bool:
        """Check if document has no meaningful content."""
        return len(self.content.strip()) == 0
    
    def exceeds_size_limit(self, limit_kb: int = 350) -> bool:
        """Check if document exceeds size limit.
        
        BUSINESS RULE: Documents over 350KB may cause token limit issues.
        """
        size_kb = self.get_size_kb()
        return size_kb > limit_kb
    
    def get_size_kb(self) -> float:
        """Get document size in KB."""
        return len(self.content.encode('utf-8')) / 1024
```

#### ExtractionResult Entity
**File**: `/app/domain/entities/extraction_result.py`
```python
from typing import Dict, Any
from enum import Enum
from datetime import datetime

class DocumentType(Enum):
    """Valid document types in the system."""
    BILL_OF_LADING = "BILL_OF_LADING"
    INVOICE = "INVOICE"
    AIR_WAYBILL = "AIR_WAYBILL"
    CUSTOMS_FORM = "CUSTOMS_FORM"
    UNKNOWN = "UNKNOWN"

class ExtractionResult:
    """Domain entity representing extraction results.
    
    CRITICAL: Contains business logic for extraction validation.
    """
    
    def __init__(
        self,
        document_type: DocumentType,
        extracted_data: Dict[str, Any],
        confidence_score: float,
        analysis: str,
        filename: str
    ):
        """Initialize with validation.
        
        BUSINESS RULES:
        - Confidence score must be between 0 and 1
        - Analysis cannot be empty
        - Extracted data must be a dictionary
        """
        if not 0 <= confidence_score <= 1:
            raise ValueError(f"Confidence score must be between 0 and 1, got {confidence_score}")
        
        if not analysis or not analysis.strip():
            raise ValueError("Analysis cannot be empty")
        
        if not isinstance(extracted_data, dict):
            raise ValueError("Extracted data must be a dictionary")
        
        self.document_type = document_type
        self.extracted_data = extracted_data
        self.confidence_score = confidence_score
        self.analysis = analysis
        self.filename = filename
        self.extraction_time = datetime.utcnow()
    
    def is_high_confidence(self) -> bool:
        """Check if extraction has high confidence.
        
        BUSINESS RULE: High confidence is >= 0.8
        """
        return self.confidence_score >= 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        NOTE: This is NOT a DTO, just a utility method.
        """
        return {
            "document_type": self.document_type.value,
            "extracted_data": self.extracted_data,
            "confidence_score": self.confidence_score,
            "analysis": self.analysis,
            "filename": self.filename,
            "extraction_time": self.extraction_time.isoformat()
        }
```

### Domain Exceptions

**File**: `/app/domain/exceptions.py`
```python
class DomainError(Exception):
    """Base exception for domain errors."""
    pass

class InvalidDocumentError(DomainError):
    """Raised when document is invalid."""
    pass

class DocumentNotFoundError(DomainError):
    """Raised when document cannot be found."""
    pass

class ExtractionError(DomainError):
    """Raised when extraction fails."""
    pass
```

### ERROR: Common Domain Layer Mistakes
1. **Importing external libraries** - Domain should be pure Python
2. **Depending on frameworks** - No FastAPI, Django, etc.
3. **Database operations** - Domain doesn't know about persistence
4. **Network calls** - Domain is isolated from I/O

## Layer 2: Application Layer

### Location: `/app/application/`

### Purpose
Contains use cases and defines interfaces (ports) for external dependencies. Orchestrates domain entities but doesn't know HOW things are implemented.

### Use Cases

#### ProcessUserRequestUseCase
**File**: `/app/application/use_cases/process_user_request.py`
```python
from app.application.ports import ExtractionAgent
from app.application.dto import UserResponseDTO
from app.application.exceptions import UseCaseExecutionError, InitializationError

class ProcessUserRequestUseCase:
    """Use case for processing natural language user requests.
    
    CRITICAL: This is the main entry point for business logic.
    It knows WHAT to do but not HOW to do it.
    """
    
    def __init__(self, extraction_agent: ExtractionAgent):
        """Initialize with required dependencies.
        
        DEPENDENCY INJECTION: We depend on the interface, not implementation.
        
        Args:
            extraction_agent: Port for extraction and NLP processing
        """
        self.extraction_agent = extraction_agent
        self._initialized = False
    
    async def execute(self, user_message: str) -> UserResponseDTO:
        """Execute the use case - process user's request.
        
        ORCHESTRATION: Coordinates the extraction process without
        knowing the implementation details.
        
        Args:
            user_message: Natural language request from user
            
        Returns:
            UserResponseDTO with results
        """
        try:
            # Validate input
            if not user_message or not user_message.strip():
                raise UseCaseExecutionError("User message cannot be empty")
            
            # Ensure agent is initialized
            if not self._initialized:
                try:
                    await self.extraction_agent.initialize()
                    self._initialized = True
                except Exception as e:
                    raise InitializationError(f"Failed to initialize extraction agent: {str(e)}") from e
            
            # Let the agent handle the request
            # CRITICAL: We don't know if it's using LangChain, OpenAI, etc.
            try:
                result = await self.extraction_agent.process_message(user_message)
            except Exception as e:
                raise UseCaseExecutionError(f"Agent failed to process message: {str(e)}") from e
            
            # Convert result to DTO
            return UserResponseDTO.success_response(
                message=result.get("message", "Request processed successfully"),
                data=result.get("data")
            )
            
        except (UseCaseExecutionError, InitializationError) as e:
            # Return error DTO for application exceptions
            return UserResponseDTO.error_response(str(e))
        except Exception as e:
            # Unexpected error
            return UserResponseDTO.error_response(f"Unexpected error: {str(e)}")
```

### Ports (Interfaces)

#### ExtractionAgent Port
**File**: `/app/application/ports/extraction_agent.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.domain.entities import Document, ExtractionResult

class ExtractionAgent(ABC):
    """Interface for document extraction agent.
    
    CRITICAL: This is a PORT - an interface that defines
    what the application needs from the outside world.
    """
    
    @abstractmethod
    async def extract(self, document: Document) -> ExtractionResult:
        """Extract structured data from a document.
        
        INTERFACE CONTRACT: Implementations MUST:
        1. Handle all document types
        2. Return valid ExtractionResult
        3. Raise ExtractionError on failure
        """
        pass
    
    @abstractmethod
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message.
        
        FLEXIBILITY: Allows the agent to handle any request,
        not just extraction.
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent with necessary resources.
        
        LAZY LOADING: Allows expensive initialization
        to be deferred until needed.
        """
        pass
```

#### AgentService Port
**File**: `/app/application/ports/agent_service.py`
```python
from abc import ABC, abstractmethod
from typing import List, Protocol

class Tool(Protocol):
    """Protocol for a tool that can be used by the agent."""
    name: str
    description: str
    
    async def ainvoke(self, input: dict) -> Any: ...

class AgentExecutor(Protocol):
    """Protocol for agent executor."""
    
    async def ainvoke(self, input: dict) -> dict: ...

class AgentService(ABC):
    """Interface for agent service.
    
    SEPARATION: Separates tool management from extraction logic.
    """
    
    @abstractmethod
    def set_tools(self, tools: List[Tool]) -> None:
        """Set the tools available to the agent."""
        pass
    
    @abstractmethod
    def create_agent_executor(self) -> AgentExecutor:
        """Create an agent executor for processing requests."""
        pass
```

### DTOs (Data Transfer Objects)

**File**: `/app/application/dto/user_response.py`
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class UserResponseDTO:
    """DTO for user responses.
    
    CRITICAL: DTOs are immutable data carriers.
    They have NO business logic.
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @staticmethod
    def success_response(message: str, data: Optional[Dict[str, Any]] = None) -> 'UserResponseDTO':
        """Factory method for success responses."""
        return UserResponseDTO(
            success=True,
            message=message,
            data=data,
            error=None
        )
    
    @staticmethod
    def error_response(error: str) -> 'UserResponseDTO':
        """Factory method for error responses."""
        return UserResponseDTO(
            success=False,
            message="Error occurred",
            data=None,
            error=error
        )
```

### ERROR: Common Application Layer Mistakes
1. **Implementing business logic in DTOs** - DTOs are just data
2. **Depending on concrete implementations** - Use interfaces
3. **Knowing about frameworks** - Application is framework-agnostic
4. **Direct database access** - Goes through ports

## Layer 3: Adapters Layer

### Location: `/app/adapters/`

### Purpose
Implements the ports defined by the application layer and adapts external formats to internal ones.

### Controllers

#### A2AController
**File**: `/app/adapters/controllers/a2a_controller.py`
```python
from typing import Dict, Any
from app.application.use_cases import ProcessUserRequestUseCase

class A2AController:
    """Controller for A2A protocol requests.
    
    RESPONSIBILITY: Adapts A2A messages to use case calls.
    """
    
    def __init__(self, process_request_use_case: ProcessUserRequestUseCase):
        """Initialize with use case.
        
        DEPENDENCY: Depends on use case, not implementation details.
        """
        self.process_request_use_case = process_request_use_case
    
    async def handle_message(self, message: str) -> Dict[str, Any]:
        """Handle incoming A2A message.
        
        ADAPTATION: Converts string message to use case call
        and DTO response to dictionary.
        
        Args:
            message: Natural language message from A2A protocol
            
        Returns:
            Dictionary response for A2A protocol
        """
        # Execute use case
        response_dto = await self.process_request_use_case.execute(message)
        
        # Convert DTO to dictionary for A2A
        return {
            "success": response_dto.success,
            "message": response_dto.message,
            "data": response_dto.data,
            "error": response_dto.error
        }
```

### Presenters

#### A2APresenter
**File**: `/app/adapters/presenters/a2a_presenter.py`
```python
from typing import Dict, Any, List
from dataclasses import dataclass
import json

# CRITICAL: These imports are from A2A library, not our domain
from a2a.types import Part, TextPart, DataPart

class A2APresenter:
    """Presenter for formatting responses for A2A protocol.
    
    RESPONSIBILITY: Converts internal format to A2A format.
    """
    
    def format_response(self, result: Dict[str, Any]) -> List[Part]:
        """Format response for A2A protocol.
        
        PROTOCOL ADAPTATION: Converts our dictionary format
        to A2A's Part format.
        
        Args:
            result: Internal response dictionary
            
        Returns:
            List of A2A Parts
        """
        parts = []
        
        # Add message as text part
        if "message" in result:
            parts.append(
                Part(root=TextPart(text=result["message"]))
            )
        
        # Add data as data part if present
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

### Gateways

#### LangChainExtractionAgent
**File**: `/app/adapters/gateways/langchain_extraction_agent.py`
```python
from typing import Dict, Any
from app.application.ports import ExtractionAgent, AgentService
from app.domain.entities import Document, ExtractionResult, DocumentType
from app.domain.exceptions import ExtractionError
import json

class LangChainExtractionAgent(ExtractionAgent):
    """LangChain-based implementation of ExtractionAgent.
    
    CRITICAL: This is an ADAPTER that implements the
    ExtractionAgent port using LangChain.
    """
    
    def __init__(self, agent_service: AgentService, pdf_service=None):
        """Initialize with service interfaces.
        
        DEPENDENCY INJECTION: We depend on AgentService interface,
        not on LangChain directly.
        
        Args:
            agent_service: Agent service that implements AgentService port
            pdf_service: Deprecated - kept for compatibility but not used
        """
        self.agent_service = agent_service
        self.agent_executor = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the agent with MCP tools.
        
        LAZY INITIALIZATION: Defers expensive setup until needed.
        """
        if self._initialized:
            return
        
        # Initialize agent service (which will initialize MCP and get tools)
        if hasattr(self.agent_service, 'initialize'):
            await self.agent_service.initialize()
        
        # Create agent executor
        self.agent_executor = self.agent_service.create_agent_executor()
        
        self._initialized = True
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message using LangChain agent.
        
        IMPLEMENTATION: Uses LangChain's ReAct agent to process
        the message and decide which tools to use.
        
        Args:
            message: User's natural language request
            
        Returns:
            Response dictionary with results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Let the agent handle the request
            # CRITICAL: The agent decides which MCP tools to use
            result = await self.agent_executor.ainvoke({"input": message})
            
            # Extract the output
            output = result.get("output", "")
            
            # Structure the response
            response = {
                "success": True,
                "message": output,
                "data": None
            }
            
            # Try to extract structured data if present
            if "{" in output and "}" in output:
                try:
                    json_data = self._extract_json_from_response(output)
                    if json_data:
                        response["data"] = json_data
                except:
                    pass  # If JSON extraction fails, keep raw output
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}",
                "data": None
            }
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON data from agent response.
        
        UTILITY: Handles messy LLM output that might contain JSON.
        """
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}
```

### ERROR: Common Adapter Layer Mistakes
1. **Business logic in adapters** - Adapters only adapt
2. **Depending on specific framework versions** - Keep it flexible
3. **Not implementing all interface methods** - Must fulfill contract
4. **Mixing protocols** - Keep A2A separate from HTTP, etc.

## Layer 4: Infrastructure Layer

### Location: `/app/infrastructure/`

### Purpose
Contains all external service implementations, framework-specific code, and I/O operations.

### CRITICAL: Infrastructure Details in Next Documents
Due to the complexity of infrastructure, it's covered in:
- **03_A2A_PROTOCOL_INTEGRATION.md** - A2A server setup
- **04_MCP_INTEGRATION.md** - MCP client and tools
- **05_EXECUTION_FLOW.md** - How it all connects

## Composition Root

### Location: `/app/main/composition_root.py`

### Purpose
The ONLY place where concrete implementations are created and wired together.

```python
from app.infrastructure.external_services import MCPClient, LangChainSetup, CompositeAgentService
from app.adapters.gateways import LangChainExtractionAgent
from app.adapters.controllers import A2AController
from app.adapters.presenters import A2APresenter
from app.application.use_cases import ProcessUserRequestUseCase

class CompositionRoot:
    """The composition root for the entire application.
    
    CRITICAL: This is the ONLY place where we:
    1. Create concrete instances
    2. Wire dependencies together
    3. Know about all layers
    """
    
    def __init__(self):
        """Initialize the composition root."""
        self._initialized = False
        
        # Infrastructure services
        self._mcp_client = None
        self._langchain_setup = None
        self._agent_service = None
        
        # Adapters
        self._extraction_agent = None
        self._a2a_controller = None
        self._a2a_presenter = None
        
        # Use cases
        self._process_request_use_case = None
    
    def initialize(self) -> None:
        """Initialize all components in the correct order.
        
        ORDER MATTERS: Infrastructure → Adapters → Use Cases → Controllers
        """
        if self._initialized:
            return
        
        # 1. Create infrastructure services
        self._mcp_client = MCPClient()
        self._langchain_setup = LangChainSetup()
        
        # 2. Create composite agent service
        self._agent_service = CompositeAgentService(
            self._mcp_client,
            self._langchain_setup
        )
        
        # 3. Create adapters
        self._extraction_agent = LangChainExtractionAgent(
            self._agent_service,
            None  # PDF service no longer needed
        )
        
        # 4. Create use cases
        self._process_request_use_case = ProcessUserRequestUseCase(
            extraction_agent=self._extraction_agent
        )
        
        # 5. Create controllers and presenters
        self._a2a_controller = A2AController(self._process_request_use_case)
        self._a2a_presenter = A2APresenter()
        
        self._initialized = True
```

### ERROR: Composition Root Anti-patterns
1. **Creating instances outside composition root** - Breaks DI
2. **Circular dependencies** - Causes import errors
3. **Not following initialization order** - Causes runtime errors
4. **Exposing mutable state** - Use property getters

## Summary: Dependency Flow

```
Infrastructure ← Adapters ← Application ← Domain
     ↓              ↓           ↓           ↓
   Knows all    Knows app    Knows      Knows
   layers       & domain     domain     nothing
```

## Next: Read 03_A2A_PROTOCOL_INTEGRATION.md
To understand how the A2A protocol server is implemented in the infrastructure layer.