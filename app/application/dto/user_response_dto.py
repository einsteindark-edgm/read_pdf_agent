"""DTO for user responses."""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class UserResponseDTO:
    """Data Transfer Object for responses to user requests.
    
    This DTO encapsulates the response data from processing
    a user request.
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "message": self.message
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if self.error is not None:
            result["error"] = self.error
            
        return result
    
    @classmethod
    def success_response(cls, message: str, data: Optional[Dict[str, Any]] = None) -> "UserResponseDTO":
        """Create a success response."""
        return cls(
            success=True,
            message=message,
            data=data,
            error=None
        )
    
    @classmethod
    def error_response(cls, error_message: str) -> "UserResponseDTO":
        """Create an error response."""
        return cls(
            success=False,
            message="Error processing request",
            data=None,
            error=error_message
        )