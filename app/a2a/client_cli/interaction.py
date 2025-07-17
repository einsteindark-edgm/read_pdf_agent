"""Interactive session and testing utilities for Document Extraction A2A Client."""
import asyncio
from typing import Dict, Any

from .client import DocumentExtractionClient


class DocumentExtractionInteraction:
    """Handles interactive sessions and testing for Document Extraction Agent."""
    
    def __init__(self, base_url: str = "http://localhost:8005"):
        """Initialize the interaction handler.
        
        Args:
            base_url: Base URL of the A2A agent
        """
        self.client = DocumentExtractionClient(base_url)
    
    async def interactive_session(self) -> None:
        """Run an interactive session with the agent."""
        # Connect to agent
        await self.client.connect()
        
        print("\n🤖 Document Extraction Agent - Interactive Mode")
        print("Type 'help' for examples, 'quit' to exit\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if user_input.lower() == "quit":
                    print("👋 Goodbye!")
                    break
                    
                elif user_input.lower() == "help":
                    print("\n📚 Examples:")
                    print("  - list available pdfs")
                    print("  - extract invoice.pdf")
                    print("  - analyze bill-of-lading-template.pdf")
                    print("  - what's in shipment.pdf?")
                    print()
                    continue
                    
                elif not user_input:
                    continue
                
                # Send message and process response
                print()
                response = await self.client.send_message(user_input)
                await self._process_response(response)
                print("\n" + "=" * 60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    async def run_tests(self) -> None:
        """Run automated tests."""
        # Connect
        await self.client.connect()
        
        # Test cases
        test_messages = [
            "list available pdfs",
            "extract bill-of-lading-template.pdf",
            "what's in invoice.pdf?",
            "extract non-existent.pdf",  # Test error handling
        ]
        
        print("\n🧪 Running automated tests...\n")
        
        for msg in test_messages:
            print(f"\n{'='*60}")
            print(f"Test: {msg}")
            print('='*60 + "\n")
            
            response = await self.client.send_message(msg)
            await self._process_response(response)
            await asyncio.sleep(2)  # Small delay between tests to ensure server processes requests
    
    async def _process_response(self, response: Any) -> None:
        """Process and display the response from the agent.
        
        Args:
            response: Response from the agent
        """
        print(f"📤 Sent message")
        print("-" * 60)
        
        # Handle dict with events (from streaming)
        if isinstance(response, dict) and 'events' in response:
            events = response['events']
            if not events:
                print("⚠️  No events received")
                return
                
            for event in events:
                await self._process_streaming_event(event)
            return
        
        # Handle SendMessageResponse type
        if type(response).__name__ == 'SendMessageResponse':
            # SendMessageResponse contains a JSONRPC response in root
            if hasattr(response, 'root'):
                root = response.root
                
                # Check for error
                if hasattr(root, 'error') and root.error:
                    print(f"❌ Server error: {root.error}")
                    return
                
                # The response from the A2A server comes as streaming events
                # We need to collect events from the server
                print("⏳ Waiting for response from agent...")
                
                # The actual events will come through the streaming connection
                # This is just the acknowledgment that the message was sent
                # The real response will come later
            else:
                print("⚠️  SendMessageResponse has no root")
            return
            
        # Process response - check different response formats
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            # JSONRPC success response with nested structure
            result = response.root.result
            
            # Check if result is a Task (from TaskUpdater)
            if hasattr(result, 'kind') and result.kind == 'task':
                # This is a task response
                if hasattr(result, 'status') and result.status:
                    # Show task status
                    print(f"\n📋 Task Status: {result.status.state}")
                    
                    # Get the final message from status
                    if hasattr(result.status, 'message') and result.status.message:
                        for part in result.status.message.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                print(f"\n{part.root.text}")
                
                # Also show history if needed
                if hasattr(result, 'history') and len(result.history) > 2:
                    print(f"\n📜 Processing steps: {len(result.history)}")
                    
            elif hasattr(result, 'events'):
                # Event-based response
                for event in result.events:
                    await self._process_event(event)
            elif hasattr(result, 'parts'):
                # Direct message response
                for part in result.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        print(f"\n💬 {part.root.text}")
            else:
                print("⚠️  Unexpected result format")
        elif hasattr(response, 'error'):
            # JSONRPC error response
            print(f"❌ Server error: {response.error}")
        # Handle Task response directly
        elif type(response).__name__ == 'Task':
            # This is a Task object from the A2A protocol
            # Structure: Task -> status -> message -> parts -> [Part(root=TextPart(text='...'))]
            
            if hasattr(response, 'status') and response.status:
                status = response.status
                
                # The status has a message attribute
                if hasattr(status, 'message') and status.message:
                    message = status.message
                    
                    # Message has parts
                    if hasattr(message, 'parts') and message.parts:
                        for part in message.parts:
                            # Each part has root which is a TextPart
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                print(f"\n💬 Agent: {part.root.text}")
                            elif hasattr(part, 'text'):
                                # Fallback if structure is different
                                print(f"\n💬 Agent: {part.text}")
                    else:
                        # No parts found
                        print("⚠️  No message parts found")
                else:
                    # No message in status
                    print("⚠️  No message found in status")
            else:
                # No status
                print("⚠️  No status found in Task")
                
                # Also check history for agent messages
                if hasattr(response, 'history') and response.history:
                    # Process all events in history
                    for event in response.history:
                        if hasattr(event, 'kind'):
                            if event.kind == 'agent_message':
                                if hasattr(event, 'message') and hasattr(event.message, 'parts'):
                                    for part in event.message.parts:
                                        if hasattr(part, 'text'):
                                            print(f"\n💬 {part.text}")
                                        elif hasattr(part, 'data') and hasattr(part, 'mimeType'):
                                            # Handle data artifacts
                                            print(f"\n📄 Data artifact ({part.mimeType})")
                                            if part.mimeType == 'application/json':
                                                try:
                                                    import json
                                                    data = json.loads(part.data)
                                                    print(json.dumps(data, indent=2))
                                                except:
                                                    print(part.data[:200] + "..." if len(part.data) > 200 else part.data)
        else:
            print(f"⚠️  Unexpected response type: {type(response)}")
    
    async def _process_result(self, result) -> None:
        """Process the result from SendMessageResponse.
        
        Args:
            result: The result object from the response
        """
        # Check if result has events (streaming response)
        if hasattr(result, 'events') and result.events:
            for event in result.events:
                # Process each event
                if hasattr(event, 'root'):
                    event_data = event.root
                    
                    # Handle task events
                    if hasattr(event_data, 'kind') and event_data.kind == 'task':
                        if hasattr(event_data, 'status'):
                            print(f"\n⏳ Task [{event_data.id[:8]}]: {event_data.status}")
                            
                            # Check for message in status
                            if hasattr(event_data, 'statusMessage') and event_data.statusMessage:
                                if hasattr(event_data.statusMessage, 'parts'):
                                    for part in event_data.statusMessage.parts:
                                        if hasattr(part.root, 'text'):
                                            print(f"\n{part.root.text}")
                    
                    # Handle message events
                    elif hasattr(event_data, 'kind') and event_data.kind == 'message':
                        if hasattr(event_data, 'message') and hasattr(event_data.message, 'parts'):
                            for part in event_data.message.parts:
                                if hasattr(part.root, 'text'):
                                    print(f"\n💬 {part.root.text}")
                                elif hasattr(part.root, 'data'):
                                    # Handle data artifacts
                                    print(f"\n📄 Data artifact: {part.root.name or 'data'}")
        else:
            print("⚠️  No events in result")
    
    async def _process_streaming_event(self, event) -> None:
        """Process a streaming event from the A2A server.
        
        Args:
            event: Event from the streaming response
        """
        # Check event type
        if hasattr(event, 'root'):
            root = event.root
            
            # Handle task events
            if hasattr(root, 'task'):
                task = root.task
                if hasattr(task, 'status') and hasattr(task, 'id'):
                    status = task.status
                    task_id = task.id[:8]
                    
                    # Show task status
                    if status == 'working':
                        print(f"\n⏳ Task [{task_id}]: {status}")
                    elif status == 'completed':
                        print(f"\n✅ Task [{task_id}]: {status}")
                    elif status == 'failed':
                        print(f"\n❌ Task [{task_id}]: {status}")
                    
                    # Check for status message
                    if hasattr(task, 'statusMessage') and task.statusMessage:
                        if hasattr(task.statusMessage, 'parts'):
                            for part in task.statusMessage.parts:
                                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                    print(f"\n{part.root.text}")
            
            # Handle message events  
            elif hasattr(root, 'message'):
                message = root.message
                if hasattr(message, 'parts'):
                    for part in message.parts:
                        if hasattr(part, 'root'):
                            part_root = part.root
                            if hasattr(part_root, 'text'):
                                print(f"\n💬 {part_root.text}")
                            elif hasattr(part_root, 'data'):
                                # Handle data artifacts
                                name = part_root.name if hasattr(part_root, 'name') else 'data'
                                print(f"\n📄 Data artifact: {name}")
                                if hasattr(part_root, 'data'):
                                    # Try to display JSON data
                                    try:
                                        import json
                                        data = json.loads(part_root.data)
                                        print(json.dumps(data, indent=2))
                                    except:
                                        print(part_root.data[:200] + "..." if len(part_root.data) > 200 else part_root.data)
        else:
            # Debug unknown event
            print(f"⚠️  Unknown event type: {type(event)}")
    
    async def _process_event_object(self, event) -> None:
        """Process an event object from SendMessageResponse.
        
        Args:
            event: Event object with various attributes
        """
        # Handle different event types
        if hasattr(event, 'kind'):
            kind = event.kind
            
            if kind == 'task':
                # Handle task events
                task_id = event.id[:8] if hasattr(event, 'id') else 'unknown'
                status = event.status if hasattr(event, 'status') else 'unknown'
                print(f"\n⏳ Task [{task_id}]: {status}")
                
                # Check for status message
                if hasattr(event, 'statusMessage') and event.statusMessage:
                    if hasattr(event.statusMessage, 'parts'):
                        for part in event.statusMessage.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                print(f"\n{part.root.text}")
                            elif hasattr(part, 'text'):
                                print(f"\n{part.text}")
            
            elif kind == 'message':
                # Handle message events
                if hasattr(event, 'message'):
                    message = event.message
                    if hasattr(message, 'parts'):
                        for part in message.parts:
                            if hasattr(part, 'root'):
                                if hasattr(part.root, 'text'):
                                    print(f"\n💬 {part.root.text}")
                                elif hasattr(part.root, 'data'):
                                    print(f"\n📄 Data: {part.root.name or 'artifact'}")
                            elif hasattr(part, 'text'):
                                print(f"\n💬 {part.text}")
            else:
                print(f"\n📌 Event: {kind}")
        else:
            # Debug unknown event structure
            print(f"⚠️  Unknown event structure: {[attr for attr in dir(event) if not attr.startswith('_')]}")
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single event from the response.
        
        Args:
            event: Event dictionary
        """
        kind = event.get("kind")
        
        if kind == "task":
            task = event.get("task", {})
            status = task.get("status", "unknown")
            task_id = task.get("id", "")[:8]  # Short ID for display
            
            status_emoji = {
                "working": "⏳",
                "completed": "✅",
                "failed": "❌"
            }.get(status, "❓")
            
            print(f"{status_emoji} Task [{task_id}]: {status}")
            
        elif kind == "agent_message":
            message = event.get("message", {})
            for part in message.get("parts", []):
                part_kind = part.get("kind")
                
                if part_kind == "text":
                    text = part.get("text", "")
                    print(f"\n💬 {text}")
                    
                elif part_kind == "artifact":
                    title = part.get("title", "Artifact")
                    mime_type = part.get("mimeType", "")
                    data = part.get("data", "")
                    
                    print(f"\n📄 {title} ({mime_type})")
                    if mime_type == "application/json":
                        # Pretty print JSON
                        import json
                        try:
                            parsed = json.loads(data)
                            print(json.dumps(parsed, indent=2))
                        except:
                            print(data)
                    else:
                        print(data)


async def main():
    """Main entry point for interaction utilities."""
    import sys
    
    interaction = DocumentExtractionInteraction()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated tests
        await interaction.run_tests()
    else:
        # Run interactive session
        await interaction.interactive_session()


if __name__ == "__main__":
    print("🚀 A2A Document Extraction Client")
    print("Make sure the A2A server is running: python __main__.py\n")
    
    asyncio.run(main())