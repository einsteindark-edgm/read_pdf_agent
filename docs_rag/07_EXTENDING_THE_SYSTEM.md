# Extending the System - Adding Features Without Breaking Architecture

## Context for RAG
This document explains how to extend the Document Extraction Agent with new features while maintaining Clean Architecture. Each example shows the RIGHT way and WRONG way to implement changes.

## Adding New MCP Tools

### Scenario: Add a tool to search PDFs by content

#### Step 1: Update MCP Server (External)
```python
# In your MCP server implementation
class PDFServer(Server):
    def __init__(self):
        super().__init__()
        
        # Add new tool registration
        self.register_tool(
            Tool(
                name="search_pdf_content",
                description="Search for text within PDF files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text to search for"
                        }
                    },
                    "required": ["query"]
                }
            ),
            self.search_content
        )
    
    async def search_content(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search PDFs for content."""
        results = []
        for pdf in self.pdf_dir.glob("*.pdf"):
            content = extract_pdf_text(pdf)
            if query.lower() in content.lower():
                results.append({
                    "filename": pdf.name,
                    "preview": extract_preview(content, query)
                })
        return {"results": results}
```

#### Step 2: No Changes Needed in Main Code!
**CRITICAL**: The system automatically discovers new tools. The LLM will use them based on user requests.

#### Step 3: Update LLM Prompt (Optional)
```python
# In /app/infrastructure/external_services/langchain_setup.py
# Add example to help LLM understand the new tool

prompt = PromptTemplate.from_template("""...
Examples of tool usage:
- To search PDFs: Use search_pdf_content with {{"query": "search term"}}
...""")
```

### WRONG Way: Hardcoding Tool Logic
```python
# DON'T DO THIS - Adding tool-specific logic
class ProcessUserRequestUseCase:
    async def execute(self, user_message: str):
        # WRONG: Hardcoding tool selection
        if "search" in user_message:
            return self.search_pdfs(user_message)
        
        # This breaks the flexibility of LLM tool selection
```

## Adding New Document Types

### Scenario: Support for Purchase Orders

#### RIGHT Way: Let the System Adapt
```python
# In /app/domain/entities/extraction_result.py
class DocumentType(Enum):
    """Valid document types in the system."""
    BILL_OF_LADING = "BILL_OF_LADING"
    INVOICE = "INVOICE"
    AIR_WAYBILL = "AIR_WAYBILL"
    CUSTOMS_FORM = "CUSTOMS_FORM"
    PURCHASE_ORDER = "PURCHASE_ORDER"  # Add new type
    UNKNOWN = "UNKNOWN"
```

**That's it!** The LLM will automatically detect and extract purchase orders.

#### WRONG Way: Creating Specific Classes
```python
# DON'T DO THIS - Creating document-specific classes
class PurchaseOrderExtractor:
    def extract_po_number(self, text: str): ...
    def extract_vendor(self, text: str): ...
    
# This creates rigid, document-specific logic
```

## Adding New Output Formats

### Scenario: Export results as XML

#### Step 1: Create New DTO
```python
# In /app/application/dto/xml_response.py
from dataclasses import dataclass
from typing import Dict, Any
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class XMLResponseDTO:
    """DTO for XML responses."""
    root_element: str
    data: Dict[str, Any]
    
    def to_xml(self) -> str:
        """Convert to XML string."""
        root = ET.Element(self.root_element)
        self._dict_to_xml(self.data, root)
        return ET.tostring(root, encoding='unicode')
    
    def _dict_to_xml(self, data: dict, parent: ET.Element):
        """Recursively convert dict to XML."""
        for key, value in data.items():
            child = ET.SubElement(parent, key)
            if isinstance(value, dict):
                self._dict_to_xml(value, child)
            else:
                child.text = str(value)
```

#### Step 2: Create XML Presenter
```python
# In /app/adapters/presenters/xml_presenter.py
from typing import Dict, Any
from app.application.dto import XMLResponseDTO

class XMLPresenter:
    """Presenter for XML format output."""
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """Format response as XML."""
        dto = XMLResponseDTO(
            root_element="extraction_result",
            data=result
        )
        return dto.to_xml()
```

#### Step 3: Add Configuration Option
```python
# In /app/main/composition_root.py
def _create_controllers_and_presenters(self) -> None:
    # Support multiple presenters
    self._a2a_presenter = A2APresenter()
    self._xml_presenter = XMLPresenter()  # New
    
    # Choose based on configuration
    output_format = os.getenv("OUTPUT_FORMAT", "a2a")
    if output_format == "xml":
        self._active_presenter = self._xml_presenter
    else:
        self._active_presenter = self._a2a_presenter
```

## Adding New LLM Providers

### Scenario: Use OpenAI instead of Gemini

#### Step 1: Create New Agent Service
```python
# In /app/infrastructure/external_services/openai_setup.py
from langchain_openai import ChatOpenAI
from app.application.ports import AgentService, Tool, AgentExecutor

class OpenAISetup(AgentService):
    """OpenAI implementation of AgentService."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7
        )
        self.tools: List[Tool] = []
    
    def set_tools(self, tools: List[Tool]) -> None:
        """Set available tools."""
        self.tools = tools
    
    def create_agent_executor(self) -> AgentExecutor:
        """Create OpenAI-based agent."""
        # Similar to LangChainSetup but with OpenAI
        # Different prompt format for GPT-4
        prompt = PromptTemplate.from_template("""
        You are an assistant with access to tools.
        
        Tools: {tools}
        
        Use this format:
        Thought: reasoning
        Action: tool_name
        Action Input: {{"key": "value"}}
        
        Human: {input}
        Assistant: {agent_scratchpad}
        """)
        
        # Rest of implementation...
```

#### Step 2: Update Composition Root
```python
# In /app/main/composition_root.py
def _create_infrastructure_services(self) -> None:
    # Choose LLM provider
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    
    if llm_provider == "openai":
        self._llm_setup = OpenAISetup()
    else:
        self._llm_setup = LangChainSetup()  # Gemini
    
    # Rest stays the same
    self._agent_service = CompositeAgentService(
        self._mcp_client,
        self._llm_setup
    )
```

## Adding Authentication

### Scenario: Add API key authentication for A2A

#### Step 1: Create Auth Middleware
```python
# In /app/infrastructure/web/auth_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key
    
    async def dispatch(self, request, call_next):
        # Skip auth for agent card
        if request.url.path == "/.well-known/agent.json":
            return await call_next(request)
        
        # Check API key
        provided_key = request.headers.get("X-API-Key")
        if provided_key != self.api_key:
            return JSONResponse(
                {"error": "Invalid API key"},
                status_code=401
            )
        
        return await call_next(request)
```

#### Step 2: Add to A2A App
```python
# In /app/main/a2a_main.py
def create_a2a_app():
    # ... existing code ...
    
    # Add authentication if configured
    api_key = os.getenv("A2A_API_KEY")
    if api_key:
        app.add_middleware(APIKeyMiddleware, api_key=api_key)
    
    return app
```

## Adding Caching

### Scenario: Cache extraction results

#### Step 1: Create Cache Port
```python
# In /app/application/ports/cache.py
from abc import ABC, abstractmethod
from typing import Optional, Any

class Cache(ABC):
    """Interface for caching."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL."""
        pass
```

#### Step 2: Implement Redis Cache
```python
# In /app/infrastructure/external_services/redis_cache.py
import json
import redis.asyncio as redis
from app.application.ports import Cache

class RedisCache(Cache):
    """Redis implementation of Cache."""
    
    def __init__(self, url: str = "redis://localhost"):
        self.redis = redis.from_url(url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from Redis."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set in Redis with TTL."""
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )
```

#### Step 3: Add Caching to Use Case
```python
# In /app/application/use_cases/process_user_request.py
class ProcessUserRequestUseCase:
    def __init__(
        self,
        extraction_agent: ExtractionAgent,
        cache: Optional[Cache] = None  # Optional dependency
    ):
        self.extraction_agent = extraction_agent
        self.cache = cache
        self._initialized = False
    
    async def execute(self, user_message: str) -> UserResponseDTO:
        # Check cache first
        if self.cache:
            cache_key = f"request:{hash(user_message)}"
            cached = await self.cache.get(cache_key)
            if cached:
                return UserResponseDTO(**cached)
        
        # ... existing processing ...
        
        # Cache successful results
        if self.cache and response_dto.success:
            await self.cache.set(
                cache_key,
                response_dto.__dict__,
                ttl=300  # 5 minutes
            )
        
        return response_dto
```

## Adding Metrics and Monitoring

### Scenario: Track request metrics

#### Step 1: Create Metrics Port
```python
# In /app/application/ports/metrics.py
from abc import ABC, abstractmethod

class Metrics(ABC):
    """Interface for metrics collection."""
    
    @abstractmethod
    async def increment(self, metric: str, tags: dict = None) -> None:
        """Increment a counter."""
        pass
    
    @abstractmethod
    async def timing(self, metric: str, duration: float, tags: dict = None) -> None:
        """Record timing."""
        pass
```

#### Step 2: Add Metrics to Use Case
```python
# In /app/application/use_cases/process_user_request.py
import time

class ProcessUserRequestUseCase:
    def __init__(
        self,
        extraction_agent: ExtractionAgent,
        metrics: Optional[Metrics] = None
    ):
        self.extraction_agent = extraction_agent
        self.metrics = metrics
    
    async def execute(self, user_message: str) -> UserResponseDTO:
        start_time = time.time()
        
        try:
            # Track request count
            if self.metrics:
                await self.metrics.increment("requests.total")
            
            # ... existing processing ...
            
            # Track success
            if self.metrics and response_dto.success:
                await self.metrics.increment("requests.success")
            
            return response_dto
            
        finally:
            # Track timing
            if self.metrics:
                duration = time.time() - start_time
                await self.metrics.timing("requests.duration", duration)
```

## Testing Extensions

### Unit Testing New Features
```python
# In /tests/test_xml_presenter.py
import pytest
from app.adapters.presenters import XMLPresenter

def test_xml_presenter_formats_correctly():
    """Test XML presenter output."""
    presenter = XMLPresenter()
    
    result = {
        "success": True,
        "message": "Extracted data",
        "data": {
            "document_type": "INVOICE",
            "invoice_number": "INV-123"
        }
    }
    
    xml = presenter.format_response(result)
    
    assert "<success>True</success>" in xml
    assert "<invoice_number>INV-123</invoice_number>" in xml
```

### Integration Testing
```python
# In /tests/test_integration.py
@pytest.mark.asyncio
async def test_new_mcp_tool():
    """Test that new MCP tool is discovered."""
    client = MCPClient()
    await client.initialize()
    
    tools = client.get_langchain_tools()
    tool_names = [t.name for t in tools]
    
    assert "search_pdf_content" in tool_names
```

## Anti-Patterns to Avoid

### 1. Breaking Layer Boundaries
```python
# WRONG: Use case accessing infrastructure directly
class ProcessUserRequestUseCase:
    async def execute(self, message: str):
        # DON'T access MCP directly from use case
        mcp_client = MCPClient()  # WRONG!
        tools = mcp_client.get_tools()  # WRONG!
```

### 2. Tight Coupling
```python
# WRONG: Depending on concrete implementations
class NewFeature:
    def __init__(self, gemini_setup: LangChainSetup):  # WRONG!
        # Should depend on AgentService interface
```

### 3. Modifying Core Without Need
```python
# WRONG: Adding feature-specific logic to domain
class Document:
    def export_to_xml(self):  # WRONG!
        # Domain shouldn't know about export formats
```

### 4. Skipping Composition Root
```python
# WRONG: Creating instances outside composition root
class SomeAdapter:
    def __init__(self):
        self.cache = RedisCache()  # WRONG!
        # Should be injected
```

## Extension Checklist

When adding a new feature, verify:

- [ ] **Layer boundaries respected** - No upward dependencies
- [ ] **Interfaces used** - Depend on abstractions
- [ ] **Composition root updated** - All wiring in one place
- [ ] **Tests added** - Unit and integration tests
- [ ] **Documentation updated** - Including this RAG doc
- [ ] **Error handling added** - At appropriate layers
- [ ] **Configuration externalized** - Via environment variables
- [ ] **Backward compatibility** - Existing features still work

## Example: Complete Feature Addition

### Adding PDF Encryption Support

1. **Domain Layer** - Add encryption status
```python
class Document:
    def __init__(self, filename: str, content: str, is_encrypted: bool = False):
        self.is_encrypted = is_encrypted
```

2. **Application Layer** - Handle encrypted docs
```python
class ProcessUserRequestUseCase:
    async def execute(self, user_message: str):
        # Existing logic handles it via agent
```

3. **Infrastructure Layer** - MCP server handles decryption
```python
# In MCP server
async def read_pdf(self, doc_id: str, password: Optional[str] = None):
    if is_encrypted(pdf_path) and password:
        content = decrypt_and_extract(pdf_path, password)
```

4. **No changes needed in core flow!** The LLM will handle password requests.

## Summary

The system is designed for extension:
1. **MCP tools** - Add to server, automatically discovered
2. **Document types** - Add enum value, LLM adapts
3. **Output formats** - New presenter, wire in composition root
4. **LLM providers** - Implement AgentService, configure
5. **Cross-cutting concerns** - Use ports and dependency injection

Always maintain Clean Architecture principles when extending.

## Next: Read 08_DEPLOYMENT_AND_OPERATIONS.md
For production deployment guidelines.