"""A2A protocol controller."""
from typing import Dict, Any
from app.application.use_cases import ProcessUserRequestUseCase


class A2AController:
    """Controller for handling A2A protocol requests.
    
    This adapter translates A2A protocol messages into use case calls
    and formats the responses appropriately.
    """
    
    def __init__(self, process_request_use_case: ProcessUserRequestUseCase):
        """Initialize with use case.
        
        Args:
            process_request_use_case: Use case for processing requests
        """
        self.process_request_use_case = process_request_use_case
    
    async def handle_message(self, message: str) -> Dict[str, Any]:
        """Handle incoming A2A message.
        
        Args:
            message: Natural language message from A2A protocol
            
        Returns:
            Response formatted for A2A protocol
        """
        # Execute use case
        response_dto = await self.process_request_use_case.execute(message)
        
        # Convert DTO to dictionary for A2A protocol
        return response_dto.to_dict()