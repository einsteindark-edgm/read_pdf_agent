"""DTO for user requests."""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class UserRequestDTO:
    """Data Transfer Object for user requests.
    
    This DTO encapsulates user input for processing requests.
    """
    message: str
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message": self.message,
            "context": self.context
        }