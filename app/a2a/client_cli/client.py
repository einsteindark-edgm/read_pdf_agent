"""A2A Client for Document Extraction Agent."""
import uuid
from typing import Optional, Any

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)


class DocumentExtractionClient:
    """Client for interacting with Document Extraction Agent via A2A protocol."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize the client.
        
        Args:
            base_url: Base URL of the A2A agent
        """
        self.base_url = base_url
        self.agent_card: Optional[AgentCard] = None
    
    async def connect(self) -> AgentCard:
        """Connect to the agent and fetch its card.
        
        Returns:
            The agent card
            
        Raises:
            Exception: If connection fails
        """
        async with httpx.AsyncClient() as httpx_client:
            print(f"🔗 Connecting to agent at: {self.base_url}")
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.base_url,
            )
            
            try:
                self.agent_card = await resolver.get_agent_card()
                print(f"✅ Connected to: {self.agent_card.name}")
                print(f"   Version: {self.agent_card.version}")
                print(f"   Description: {self.agent_card.description}")
                print("\n📋 Available skills:")
                for skill in self.agent_card.skills:
                    print(f"   - {skill.name}: {skill.description}")
                    print(f"     Examples: {', '.join(skill.examples[:3])}")
                print()
                return self.agent_card
            except Exception as e:
                print(f"❌ Failed to connect: {e}")
                raise
    
    async def send_message(self, text: str) -> Any:
        """Send a message to the agent.
        
        Args:
            text: Text message to send
            
        Returns:
            The response from the agent
            
        Raises:
            RuntimeError: If not connected
        """
        if not self.agent_card:
            raise RuntimeError("Not connected. Call connect() first.")
        
        # Use longer timeout for PDF extraction operations
        # The agent needs time to: connect to MCP, read PDF, analyze with LLM
        timeout = httpx.Timeout(120.0, connect=10.0, read=120.0)
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=self.agent_card
            )
            
            # Create message
            message = Message(
                role=Role.user,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(text=text))]
            )
            
            # Create request
            request = SendMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(message=message)
            )
            
            # Send message - the A2A client handles streaming internally
            response = await client.send_message(request)
            
            # The response can be different types depending on the server implementation
            # 1. Task object (when using TaskUpdater pattern)
            # 2. SendMessageResponse with events
            # 3. Other formats
            
            # Check if response is a Task object directly
            if type(response).__name__ == 'Task':
                # Return the Task object for proper processing
                return response
            
            # Check for events in response
            if hasattr(response, 'events'):
                return {"events": response.events}
            elif hasattr(response, 'root') and hasattr(response.root, 'result'):
                # JSONRPC result format
                result = response.root.result
                
                # Check if result is a Task
                if type(result).__name__ == 'Task':
                    return result
                
                if hasattr(result, 'events'):
                    return {"events": result.events}
                else:
                    # Return the full result for processing
                    return result
            else:
                # Return raw response for debugging
                return response