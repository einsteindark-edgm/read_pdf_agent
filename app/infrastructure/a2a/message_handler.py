"""Message handling utilities for A2A protocol."""
from typing import Optional
from a2a.types import Message, TextPart


class MessageHandler:
    """Handles message parsing for the A2A protocol."""
    
    @staticmethod
    def extract_user_text(message: Message) -> Optional[str]:
        """Extract text content from an A2A message.
        
        Args:
            message: The A2A message to extract text from
            
        Returns:
            The extracted text or None if no text found
        """
        if not message.parts:
            return None
            
        # Direct access is safe in executor context
        for part in message.parts:
            if isinstance(part.root, TextPart):
                return part.root.text
                
        return None