"""Dependency injection container."""
import os
from dotenv import load_dotenv

# Infrastructure imports
from app.infrastructure.external_services import MCPClient, LangChainSetup, CompositeAgentService

# Application imports
from app.application.use_cases import ProcessUserRequestUseCase
from app.application.ports import AgentService

# Adapter imports
from app.adapters.gateways import LangChainExtractionAgent
from app.adapters.controllers import A2AController
from app.adapters.presenters import A2APresenter


class DependencyContainer:
    """Manages all application dependencies.
    
    This is where we wire everything together, connecting
    the ports to their implementations.
    """
    
    def __init__(self):
        """Initialize container and load configuration."""
        # Load environment variables
        load_dotenv()
        
        # Check required environment variables
        self._validate_environment()
        
        # Infrastructure services
        self.mcp_client = MCPClient()
        self.langchain_setup = LangChainSetup()
        
        # Services implementing ports
        self.agent_service: AgentService = CompositeAgentService(
            self.mcp_client,
            self.langchain_setup
        )
        
        # Gateways (adapters)
        self.extraction_agent = LangChainExtractionAgent(
            self.agent_service,
            None  # pdf_service parameter kept for compatibility
        )
        
        # Use cases
        self.process_request_use_case = ProcessUserRequestUseCase(
            extraction_agent=self.extraction_agent
        )
        
        # Controllers
        self.a2a_controller = A2AController(self.process_request_use_case)
        
        # Presenters
        self.a2a_presenter = A2APresenter()
    
    def _validate_environment(self):
        """Validate required environment variables."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            raise ValueError("GOOGLE_API_KEY not set in .env file")
        
        mcp_dir = os.getenv("MCP_PDF_SERVER_DIR")
        if not mcp_dir:
            raise ValueError("MCP_PDF_SERVER_DIR not set in .env file")
    
    async def initialize(self):
        """Initialize all async components."""
        # For now, initialization happens on demand in use cases
        pass