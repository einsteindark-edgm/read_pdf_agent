"""MCP client - infrastructure service for tool integration."""
import os
from typing import List, Optional
import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP client for tool integration.
    
    This infrastructure service connects to an MCP server and
    provides its tools to LangChain for the AI agent to use.
    """
    
    def __init__(self):
        """Initialize MCP client with configuration from environment."""
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
        """Initialize connection to MCP server."""
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
            config = {
                "pdf-extractor": {
                    "command": self.mcp_command,
                    "args": args,
                    "transport": self.mcp_transport,
                    "env": {}
                }
            }
            
            # Create client
            self.client = MultiServerMCPClient(config)
            
            # Get tools from MCP server
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
        
        Returns:
            List of LangChain tools from MCP server
        """
        if not self._initialized:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")
        
        return self.tools or []
    
    async def close(self) -> None:
        """Close the MCP client connection."""
        self.client = None
        self.tools = None
        self._initialized = False