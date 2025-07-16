# MCP Integration - Model Context Protocol for PDF Operations

## Context for RAG
This document details the MCP (Model Context Protocol) integration in the Document Extraction Agent. MCP provides a standardized way to expose tools to LLMs. Our system uses MCP to access PDF files without direct file system access.

## What is MCP?

### Purpose
MCP (Model Context Protocol) enables:
- **Tool Discovery** - LLMs can discover available tools
- **Standardized Interface** - Consistent tool invocation
- **Security** - Controlled access to resources
- **Flexibility** - Easy to add new tools

### CRITICAL: MCP vs Direct File Access
- MCP runs as separate process
- Tools are exposed via stdio/HTTP
- LLM decides which tools to use
- No hardcoded file paths in main code

## MCP Client Implementation

### MCP Client Service
**File**: `/app/infrastructure/external_services/mcp_client.py`
```python
import os
from typing import List, Optional
import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class MCPClient:
    """MCP client for tool integration.
    
    CRITICAL: This connects to an external MCP server that
    provides PDF reading tools. The server must be running
    for this to work.
    """
    
    def __init__(self):
        """Initialize MCP client with configuration from environment.
        
        ENVIRONMENT VARIABLES REQUIRED:
        - MCP_PDF_SERVER_DIR: Directory containing PDFs
        - MCP_PDF_SERVER_COMMAND: Command to run server (e.g., "uv")
        - MCP_PDF_SERVER_ARGS: Arguments for command
        """
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: Optional[List[BaseTool]] = None
        self._initialized = False
        
        # Get configuration from environment
        self.mcp_command = os.getenv("MCP_PDF_SERVER_COMMAND", "uv")
        self.mcp_args = os.getenv("MCP_PDF_SERVER_ARGS", "").split()
        self.mcp_directory = os.getenv("MCP_PDF_SERVER_DIR", "")
        self.mcp_transport = os.getenv("MCP_PDF_TRANSPORT", "stdio")
        
        # Set default args if not provided
        if not self.mcp_args and not os.getenv("MCP_PDF_SERVER_ARGS"):
            self.mcp_args = ["run", "python", "mcp_documents_server.py"]
    
    async def initialize(self) -> None:
        """Initialize connection to MCP server.
        
        PROCESS MANAGEMENT: This starts the MCP server as a
        subprocess and establishes communication.
        
        CRITICAL: The MCP server must be available at the
        configured path or this will fail.
        """
        if self._initialized:
            return
            
        try:
            logger.info("Initializing MCP PDF server connection...")
            
            # Build args including directory if specified
            args = []
            if self.mcp_directory:
                args.extend(["--directory", self.mcp_directory])
            args.extend(self.mcp_args)
            
            logger.info(f"MCP command: {self.mcp_command} {' '.join(args)}")
            
            # Configure MCP client
            # SERVER CONFIG: Defines how to start and connect to MCP server
            config = {
                "pdf-extractor": {  # Server name
                    "command": self.mcp_command,
                    "args": args,
                    "transport": self.mcp_transport,  # stdio or http
                    "env": {}  # Additional environment variables
                }
            }
            
            # Create client
            # CRITICAL: MultiServerMCPClient manages server lifecycle
            self.client = MultiServerMCPClient(config)
            
            # Get tools from MCP server
            # TOOL DISCOVERY: Automatically discovers available tools
            self.tools = await self.client.get_tools()
            
            if self.tools:
                tool_names = [tool.name for tool in self.tools]
                logger.info(f"MCP server initialized with {len(self.tools)} tools: {tool_names}")
            else:
                logger.warning("MCP server initialized but no tools found!")
                self.tools = []
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise
    
    def get_langchain_tools(self) -> List[BaseTool]:
        """Get MCP tools as LangChain tools.
        
        INTEGRATION: MCP tools are automatically converted
        to LangChain's BaseTool format by langchain_mcp_adapters.
        
        Returns:
            List of LangChain tools from MCP server
        """
        if not self._initialized:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")
        
        return self.tools or []
    
    async def close(self) -> None:
        """Close the MCP client connection.
        
        CLEANUP: Properly shuts down the MCP server subprocess.
        """
        self.client = None
        self.tools = None
        self._initialized = False
```

### ERROR: MCP Client Common Issues
1. **MCP server not found** - Check MCP_PDF_SERVER_COMMAND path
2. **No tools discovered** - MCP server might be misconfigured
3. **Directory not found** - MCP_PDF_SERVER_DIR must exist
4. **Import errors** - Need langchain_mcp_adapters installed

## MCP Server Example

### Sample MCP Server Implementation
**File**: `/examples/MCP/mcp_documents_server.py` (for reference)
```python
"""Example MCP server that provides PDF tools.

CRITICAL: This is what the MCP client connects to.
Your actual server might be different but must follow
the MCP protocol.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

from mcp import Server, Tool

class PDFServer(Server):
    """MCP server providing PDF access tools."""
    
    def __init__(self, pdf_directory: str):
        super().__init__()
        self.pdf_dir = Path(pdf_directory)
        
        # Register tools
        self.register_tool(
            Tool(
                name="list_available_pdfs",
                description="List all available PDF files",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            ),
            self.list_pdfs
        )
        
        self.register_tool(
            Tool(
                name="read_doc_contents", 
                description="Read the contents of a PDF document",
                input_schema={
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "Name of the PDF file to read"
                        }
                    },
                    "required": ["doc_id"]
                }
            ),
            self.read_pdf
        )
    
    async def list_pdfs(self, **kwargs) -> Dict[str, Any]:
        """List available PDF files.
        
        TOOL IMPLEMENTATION: Returns list of PDFs in directory.
        """
        pdfs = list(self.pdf_dir.glob("*.pdf"))
        return {
            "pdfs": [pdf.name for pdf in pdfs]
        }
    
    async def read_pdf(self, doc_id: str, **kwargs) -> Dict[str, Any]:
        """Read PDF contents.
        
        TOOL IMPLEMENTATION: Extracts text from PDF.
        """
        pdf_path = self.pdf_dir / doc_id
        if not pdf_path.exists():
            return {"error": f"PDF not found: {doc_id}"}
        
        # PDF extraction logic here
        text = extract_pdf_text(pdf_path)  # Your implementation
        
        return {
            "content": text,
            "filename": doc_id
        }
```

## Tool Integration with LangChain

### Composite Agent Service
**File**: `/app/infrastructure/external_services/composite_agent_service.py`
```python
from typing import List
from app.application.ports import AgentService, Tool, AgentExecutor
from .langchain_setup import LangChainSetup
from .mcp_client import MCPClient

class CompositeAgentService(AgentService):
    """Composite service that combines MCP tools with LangChain agent.
    
    CRITICAL: This is where MCP tools are provided to LangChain
    so the LLM can use them.
    """
    
    def __init__(self, mcp_client: MCPClient, langchain_setup: LangChainSetup):
        """Initialize with MCP client and LangChain setup.
        
        DEPENDENCY: Needs both MCP (for tools) and LangChain (for agent).
        """
        self.mcp_client = mcp_client
        self.langchain_setup = langchain_setup
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize MCP and set tools in LangChain.
        
        INITIALIZATION FLOW:
        1. Initialize MCP client (starts server, gets tools)
        2. Get tools as LangChain format
        3. Provide tools to LangChain agent
        """
        if self._initialized:
            return
        
        # Initialize MCP to get tools
        # CRITICAL: This starts the MCP server subprocess
        await self.mcp_client.initialize()
        
        # Get LangChain tools from MCP
        # TOOL CONVERSION: MCP tools → LangChain BaseTool
        tools = self.mcp_client.get_langchain_tools()
        
        # Set tools in LangChain
        # TOOL INJECTION: Makes tools available to agent
        self.langchain_setup.set_tools(tools)
        
        self._initialized = True
    
    def set_tools(self, tools: List[Tool]) -> None:
        """Set the tools available to the agent.
        
        FLEXIBILITY: Allows manual tool setting if needed.
        """
        self.langchain_setup.set_tools(tools)
    
    def create_agent_executor(self) -> AgentExecutor:
        """Create an agent executor for processing requests.
        
        AGENT CREATION: Returns configured LangChain agent
        with MCP tools available.
        """
        return self.langchain_setup.create_agent_executor()
```

## LangChain Integration

### LangChain Setup with Tools
**File**: `/app/infrastructure/external_services/langchain_setup.py`
```python
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor as LangChainAgentExecutor
from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.prompts import PromptTemplate

from app.application.ports import Tool, AgentExecutor
from .pydantic_parser import PydanticReActOutputParser

class LangChainSetup:
    """Sets up LangChain with Gemini and tools.
    
    CRITICAL: This creates the ReAct agent that decides
    which MCP tools to use based on user input.
    """
    
    def __init__(self):
        """Initialize LangChain setup."""
        self.llm = None
        self.tools: List[Tool] = []
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup the Gemini LLM.
        
        MODEL: Uses Gemini Flash 2.0 for fast responses.
        """
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash-exp",
            temperature=0.7,
            max_output_tokens=2000
        )
    
    def set_tools(self, tools: List[Tool]) -> None:
        """Set the tools available to the agent.
        
        TOOL AVAILABILITY: These are the MCP tools the
        agent can choose from.
        """
        self.tools = tools
    
    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor.
        
        REACT AGENT: Creates a ReAct (Reasoning + Acting)
        agent that thinks step-by-step about which tools to use.
        """
        # Create ReAct prompt
        # CRITICAL: This prompt teaches the LLM how to use tools
        prompt = PromptTemplate.from_template("""You are a helpful document extraction assistant with access to PDF tools.

You have access to the following tools:
{tools}

Use EXACTLY this format:

Thought: I need to think about what to do
Action: [tool name from the list above]
Action Input: [input for the tool]
Observation: [result from the tool]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have the final answer
Final Answer: [your response to the user]

IMPORTANT RULES:
1. Always use the exact tool names provided
2. For read_doc_contents, use the format: {{"doc_id": "filename.pdf"}}
3. For list_available_pdfs, use empty input: {{}}
4. Think step by step about which tool to use

Question: {input}
{agent_scratchpad}""")
        
        # Create agent with custom parser
        # PARSER: Handles Gemini's output format
        agent = (
            {
                "input": lambda x: x["input"],
                "tools": lambda x: self._format_tools(),
                "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"])
            }
            | prompt
            | self.llm
            | PydanticReActOutputParser()  # Custom parser for Gemini
        )
        
        # Create executor
        # EXECUTION: Manages the agent's reasoning loop
        agent_executor = LangChainAgentExecutor(
            agent=agent,
            tools=self.tools if self.tools else [],
            verbose=True,  # Shows reasoning steps
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=5  # Prevents infinite loops
        )
        
        # Wrap in our protocol-compliant executor
        return AgentExecutorAdapter(agent_executor)
    
    def _format_tools(self) -> str:
        """Format tools for prompt.
        
        TOOL DESCRIPTION: Tells LLM what each tool does.
        """
        if not self.tools:
            return "No tools available"
        
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
```

### ERROR: LangChain Integration Issues
1. **Tools not available** - Check MCP initialization
2. **Parser errors** - Gemini output format varies
3. **Infinite loops** - Set max_iterations
4. **Wrong tool inputs** - LLM needs clear examples

## Custom Parser for Tool Inputs

### Pydantic ReAct Parser
**File**: `/app/infrastructure/external_services/pydantic_parser.py`
```python
import re
from typing import Dict, Any, Union
from langchain.agents.agent import AgentOutputParser
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException

class MCPToolInputs:
    """Converts natural language inputs to MCP tool format.
    
    CRITICAL: LLMs often provide inputs in wrong format.
    This class fixes common issues.
    """
    
    @staticmethod
    def convert_input(action: str, action_input: Union[str, Dict]) -> Dict[str, Any]:
        """Convert action input to proper format for MCP tools.
        
        CONVERSION RULES:
        1. read_doc_contents: string → {"doc_id": string}
        2. list_available_pdfs: anything → {}
        """
        if action == "read_doc_contents":
            if isinstance(action_input, str):
                # Convert string to proper format
                # COMMON ISSUE: LLM provides just "invoice.pdf"
                return {"doc_id": action_input.strip('"')}
            elif isinstance(action_input, dict) and "doc_id" in action_input:
                return {"doc_id": action_input["doc_id"]}
            else:
                # Try to extract filename
                input_str = str(action_input)
                # Look for .pdf extension
                if ".pdf" in input_str:
                    # Extract filename
                    match = re.search(r'[\w\-]+\.pdf', input_str)
                    if match:
                        return {"doc_id": match.group()}
                return {"doc_id": input_str}
                
        elif action == "list_available_pdfs":
            # This tool takes no input
            return {}
        
        # Default: return as-is
        if isinstance(action_input, dict):
            return action_input
        return {"input": action_input}

class PydanticReActOutputParser(AgentOutputParser):
    """Parser for ReAct agent with Pydantic models.
    
    GEMINI COMPATIBILITY: Handles Gemini's output variations.
    """
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the agent output.
        
        PARSING STRATEGY:
        1. Look for Final Answer → AgentFinish
        2. Look for Action/Action Input → AgentAction
        3. Handle various format variations
        """
        # Clean the text
        text = text.strip()
        
        # Check for Final Answer
        final_answer_match = re.search(
            r"Final Answer:\s*(.*)",
            text,
            re.DOTALL | re.IGNORECASE
        )
        if final_answer_match:
            return AgentFinish(
                return_values={"output": final_answer_match.group(1).strip()},
                log=text
            )
        
        # Look for Action and Action Input
        action_match = re.search(
            r"Action:\s*(.+?)\n+Action Input:\s*(.+?)(?:\n|$)",
            text,
            re.DOTALL
        )
        
        if action_match:
            action = action_match.group(1).strip()
            action_input_raw = action_match.group(2).strip()
            
            # Parse action input
            try:
                # Try to parse as JSON
                import json
                if action_input_raw.startswith("{"):
                    action_input = json.loads(action_input_raw)
                else:
                    action_input = action_input_raw
            except:
                # If not valid JSON, use as string
                action_input = action_input_raw
            
            # Convert input format for MCP tools
            # CRITICAL: Ensures tool inputs are correct
            converted_input = MCPToolInputs.convert_input(action, action_input)
            
            return AgentAction(
                tool=action,
                tool_input=converted_input,
                log=text
            )
        
        # If no clear format, raise error
        raise OutputParserException(
            f"Could not parse agent output: {text}",
            observation="Invalid output format. Please use:\nThought: [reasoning]\nAction: [tool_name]\nAction Input: [input]\n\nOr:\nFinal Answer: [answer]",
            llm_output=text
        )
```

## MCP Tool Usage Examples

### Example 1: Listing PDFs
```
User: "What PDFs are available?"

LLM Reasoning:
Thought: I need to list the available PDF files
Action: list_available_pdfs
Action Input: {}

MCP Tool Called: list_available_pdfs()
Result: {"pdfs": ["invoice.pdf", "report.pdf", "contract.pdf"]}

Final Answer: I found 3 PDF files available:
- invoice.pdf
- report.pdf  
- contract.pdf
```

### Example 2: Reading PDF
```
User: "Read invoice.pdf"

LLM Reasoning:
Thought: I need to read the contents of invoice.pdf
Action: read_doc_contents
Action Input: invoice.pdf

Parser Converts to: {"doc_id": "invoice.pdf"}

MCP Tool Called: read_doc_contents(doc_id="invoice.pdf")
Result: {"content": "Invoice #12345..."}

Final Answer: Here's the content of invoice.pdf: [content]
```

### ERROR: Common Tool Usage Errors
1. **Wrong tool name** - Must match exactly
2. **Wrong input format** - Parser tries to fix
3. **Missing doc_id key** - Required for read_doc_contents
4. **Tool not found** - Check MCP server tools

## MCP Configuration

### Environment Variables
```bash
# Required MCP configuration
MCP_PDF_SERVER_DIR=/path/to/pdfs          # Where PDFs are stored
MCP_PDF_SERVER_COMMAND=uv                 # Command to run server
MCP_PDF_SERVER_ARGS=run python server.py  # Server arguments
MCP_PDF_TRANSPORT=stdio                   # Communication method
```

### MCP Server Requirements
1. Must implement MCP protocol
2. Must expose tools with schemas
3. Must handle tool invocations
4. Should validate inputs

## Integration Flow Summary

```
1. MCPClient starts MCP server subprocess
2. MCP server exposes tools (list_pdfs, read_pdf)
3. MCPClient gets tools as LangChain BaseTool
4. CompositeAgentService provides tools to LangChain
5. LangChain ReAct agent has tools available
6. User message → Agent decides which tool
7. Tool invocation → MCP server → Result
8. Result formatted and returned to user
```

## Benefits of MCP Integration

1. **Security** - No direct file access in main code
2. **Flexibility** - Easy to add new tools
3. **Standardization** - Works with any MCP server
4. **Separation** - PDF logic separate from agent logic

## Next: Read 05_EXECUTION_FLOW.md
To see the complete end-to-end execution flow with all components.