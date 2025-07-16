"""Agent service port - interface for AI agent operations."""
from abc import ABC, abstractmethod
from typing import List, Any, Protocol


class Tool(Protocol):
    """Protocol for agent tools."""
    name: str
    description: str
    
    async def ainvoke(self, input: dict) -> Any:
        """Invoke the tool asynchronously."""
        ...


class AgentExecutor(Protocol):
    """Protocol for agent executor."""
    
    async def ainvoke(self, input: dict) -> dict:
        """Execute the agent with given input."""
        ...


class AgentService(ABC):
    """Abstract interface for AI agent operations.
    
    This port defines the contract for any service that provides
    agent capabilities for document processing. Infrastructure 
    implementations should implement this interface.
    """
    
    @abstractmethod
    def set_tools(self, tools: List[Tool]) -> None:
        """Set the tools available to the agent.
        
        Args:
            tools: List of tools the agent can use
        """
        pass
    
    @abstractmethod
    def create_agent_executor(self) -> AgentExecutor:
        """Create an agent executor for processing requests.
        
        Returns:
            Configured agent executor
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Get the list of available tools.
        
        Returns:
            List of tools available to the agent
        """
        pass