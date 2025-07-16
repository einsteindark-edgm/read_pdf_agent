"""Process user request use case."""
from app.application.ports import ExtractionAgent
from app.application.dto import UserResponseDTO
from app.application.exceptions import UseCaseExecutionError, InitializationError


class ProcessUserRequestUseCase:
    """Use case for processing natural language user requests.
    
    This is the main entry point for handling user requests about documents.
    It orchestrates other use cases and the extraction agent.
    """
    
    def __init__(self, extraction_agent: ExtractionAgent):
        """Initialize with required dependencies.
        
        Args:
            extraction_agent: Port for extraction and NLP processing
        """
        self.extraction_agent = extraction_agent
        self._initialized = False
    
    async def execute(self, user_message: str) -> UserResponseDTO:
        """Execute the use case - process user's request.
        
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
            # The agent has access to tools and can decide what to do
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