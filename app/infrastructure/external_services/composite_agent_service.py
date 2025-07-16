"""Composite agent service that combines MCP tools with LangChain."""
from typing import List
from app.application.ports import AgentService, Tool, AgentExecutor
from .langchain_setup import LangChainSetup
from .mcp_client import MCPClient


class CompositeAgentService(AgentService):
    """Composite service that combines MCP tools with LangChain agent.
    
    This service initializes MCP to get tools, then passes them to
    LangChain to create an agent that can use those tools.
    """
    
    def __init__(self, mcp_client: MCPClient, langchain_setup: LangChainSetup):
        """Initialize with MCP client and LangChain setup.
        
        Args:
            mcp_client: MCP client for getting tools
            langchain_setup: LangChain setup for creating agent
        """
        self.mcp_client = mcp_client
        self.langchain_setup = langchain_setup
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize MCP and set tools in LangChain."""
        if self._initialized:
            return
        
        # Initialize MCP to get tools
        await self.mcp_client.initialize()
        
        # Get LangChain tools from MCP
        tools = self.mcp_client.get_langchain_tools()
        
        # Set tools in LangChain
        self.langchain_setup.set_tools(tools)
        
        self._initialized = True
    
    def set_tools(self, tools: List[Tool]) -> None:
        """Set the tools available to the agent.
        
        Args:
            tools: List of tools the agent can use
        """
        self.langchain_setup.set_tools(tools)
    
    def create_agent_executor(self) -> AgentExecutor:
        """Create an agent executor for processing requests.
        
        Returns:
            Configured agent executor
        """
        return self.langchain_setup.create_agent_executor()
    
    def get_tools(self) -> List[Tool]:
        """Get the list of available tools.
        
        Returns:
            List of tools available to the agent
        """
        return self.langchain_setup.get_tools()