"""Composition root - where all dependencies are wired together.

This is the only place in the application where concrete implementations
are instantiated and wired together. This follows the Composition Root
pattern from Dependency Injection.
"""
import logging
from typing import Optional

from app.infrastructure.external_services import MCPClient, LangChainSetup, CompositeAgentService
from app.infrastructure.config import settings
from app.adapters.gateways import LangChainExtractionAgent
from app.adapters.controllers import A2AController
from app.adapters.presenters import A2APresenter
from app.application.use_cases import ProcessUserRequestUseCase
from app.application.ports import AgentService

logger = logging.getLogger(__name__)


class CompositionRoot:
    """The composition root for the entire application.
    
    This class is responsible for:
    1. Creating all concrete instances
    2. Wiring dependencies together
    3. Managing the lifecycle of components
    """
    
    def __init__(self):
        """Initialize the composition root."""
        self._initialized = False
        
        # Infrastructure services
        self._mcp_client: Optional[MCPClient] = None
        self._langchain_setup: Optional[LangChainSetup] = None
        self._agent_service: Optional[AgentService] = None
        
        # Adapters
        self._extraction_agent: Optional[LangChainExtractionAgent] = None
        self._a2a_controller: Optional[A2AController] = None
        self._a2a_presenter: Optional[A2APresenter] = None
        
        # Use cases
        self._process_request_use_case: Optional[ProcessUserRequestUseCase] = None
    
    def initialize(self) -> None:
        """Initialize all components in the correct order."""
        if self._initialized:
            return
            
        logger.info("Initializing composition root...")
        
        # 1. Create infrastructure services
        self._create_infrastructure_services()
        
        # 2. Create adapters
        self._create_adapters()
        
        # 3. Create use cases
        self._create_use_cases()
        
        # 4. Create controllers and presenters
        self._create_controllers_and_presenters()
        
        self._initialized = True
        logger.info("Composition root initialized successfully")
    
    def _create_infrastructure_services(self) -> None:
        """Create all infrastructure services."""
        logger.debug("Creating infrastructure services...")
        
        # Create concrete implementations
        self._mcp_client = MCPClient()
        self._langchain_setup = LangChainSetup()
        
        # Create composite agent service
        self._agent_service = CompositeAgentService(
            self._mcp_client,
            self._langchain_setup
        )
    
    def _create_adapters(self) -> None:
        """Create all adapter instances."""
        logger.debug("Creating adapters...")
        
        # Create extraction agent
        self._extraction_agent = LangChainExtractionAgent(
            self._agent_service,
            None  # PDF service no longer needed
        )
    
    def _create_use_cases(self) -> None:
        """Create all use case instances."""
        logger.debug("Creating use cases...")
        
        self._process_request_use_case = ProcessUserRequestUseCase(
            extraction_agent=self._extraction_agent
        )
    
    def _create_controllers_and_presenters(self) -> None:
        """Create controllers and presenters."""
        logger.debug("Creating controllers and presenters...")
        
        self._a2a_controller = A2AController(self._process_request_use_case)
        self._a2a_presenter = A2APresenter()
    
    # Getter methods for accessing wired components
    
    @property
    def a2a_controller(self) -> A2AController:
        """Get the A2A controller."""
        if not self._initialized:
            self.initialize()
        return self._a2a_controller
    
    @property
    def a2a_presenter(self) -> A2APresenter:
        """Get the A2A presenter."""
        if not self._initialized:
            self.initialize()
        return self._a2a_presenter
    
    @property
    def process_request_use_case(self) -> ProcessUserRequestUseCase:
        """Get the process request use case."""
        if not self._initialized:
            self.initialize()
        return self._process_request_use_case
    
    async def shutdown(self) -> None:
        """Cleanup resources when shutting down."""
        logger.info("Shutting down composition root...")
        
        # Close MCP client if it exists
        if self._mcp_client:
            await self._mcp_client.close()
        
        logger.info("Composition root shutdown complete")


# Global instance
_composition_root: Optional[CompositionRoot] = None


def get_composition_root() -> CompositionRoot:
    """Get or create the global composition root instance.
    
    Returns:
        The composition root instance
    """
    global _composition_root
    
    if _composition_root is None:
        _composition_root = CompositionRoot()
        _composition_root.initialize()
    
    return _composition_root


async def shutdown_composition_root() -> None:
    """Shutdown the global composition root."""
    global _composition_root
    
    if _composition_root is not None:
        await _composition_root.shutdown()
        _composition_root = None