"""Extraction agent port - interface for document extraction."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.domain.entities import Document, ExtractionResult


class ExtractionAgent(ABC):
    """Interface for document extraction agent.
    
    This port defines how the application layer interacts with
    the extraction functionality, regardless of the implementation
    (LangChain, custom ML, etc).
    """
    
    @abstractmethod
    async def extract(self, document: Document) -> ExtractionResult:
        """Extract structured data from a document.
        
        Args:
            document: Document entity to extract data from
            
        Returns:
            ExtractionResult with structured data
            
        Raises:
            ExtractionError: If extraction fails
        """
        pass
    
    @abstractmethod
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message.
        
        This allows the agent to handle general requests, not just extraction.
        
        Args:
            message: User's natural language request
            
        Returns:
            Response dictionary with results
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent with necessary resources.
        
        This might include loading models, connecting to services, etc.
        """
        pass