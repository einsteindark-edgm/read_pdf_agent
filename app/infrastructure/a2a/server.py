"""A2A server implementation for Document Extraction Agent."""
import os
import logging
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from .executor import DocumentExtractionA2AExecutor
from .card import get_agent_card


def create_a2a_app() -> A2AStarletteApplication:
    """Create and configure A2A application.
    
    Returns:
        A2AStarletteApplication configured for document extraction
    """
    request_handler = DefaultRequestHandler(
        agent_executor=DocumentExtractionA2AExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    return A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=get_agent_card()
    )


def run_server():
    """Run the A2A server with configuration from environment."""
    # Load environment
    load_dotenv()
    
    # Check environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("❌ Error: GOOGLE_API_KEY not set in .env file")
        print("   Please add your API key to the .env file")
        return
    
    # Create app
    app = create_a2a_app()
    
    # Get host and port from env or defaults
    host = os.getenv("A2A_HOST", "0.0.0.0")
    port = int(os.getenv("A2A_PORT", "8080"))
    
    print(f"🚀 Starting A2A Document Extraction Agent on {host}:{port}")
    print(f"📋 Agent card available at: http://{host}:{port}/.well-known/agent.json")
    print(f"💬 Send messages to: http://{host}:{port}/")
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run server
    uvicorn.run(app.build(), host=host, port=port)