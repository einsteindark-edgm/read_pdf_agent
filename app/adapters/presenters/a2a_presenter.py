"""A2A protocol presenter."""
from typing import Dict, Any, List
from a2a.types import Part, TextPart, DataPart
import json


class A2APresenter:
    """Presenter for formatting responses for A2A protocol.
    
    This adapter formats use case responses into the format
    expected by the A2A protocol.
    """
    
    def format_response(self, result: Dict[str, Any]) -> List[Part]:
        """Format use case result for A2A protocol.
        
        Args:
            result: Result from use case execution
            
        Returns:
            List of Part objects for A2A response
        """
        parts = []
        
        # Add main message as text part
        if "message" in result:
            parts.append(Part(root=TextPart(
                text=result["message"]
            )))
        
        # Add structured data as data part if present
        if result.get("data"):
            parts.append(Part(root=DataPart(
                mimeType="application/json",
                data=json.dumps(result["data"], indent=2),
                name="extraction_result"
            )))
        
        return parts