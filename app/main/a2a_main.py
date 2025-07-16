"""Main entry point for A2A server with Clean Architecture."""
import logging
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from app.infrastructure.config import settings
from app.infrastructure.web import CleanArchitectureA2AExecutor
from app.infrastructure.a2a import get_agent_card
from .composition_root import get_composition_root, shutdown_composition_root

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_a2a_app() -> A2AStarletteApplication:
    """Create A2A application with Clean Architecture.
    
    Returns:
        Configured A2A application
    """
    # Get composition root
    root = get_composition_root()
    
    # Create A2A executor adapter
    executor = CleanArchitectureA2AExecutor(
        controller=root.a2a_controller,
        presenter=root.a2a_presenter
    )
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A application
    return A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=get_agent_card()
    )


def run_server():
    """Run the A2A server."""
    try:
        # Validate configuration by initializing composition root
        root = get_composition_root()
        
        # Create application
        app = create_a2a_app()
        
        # Server configuration
        host = settings.a2a_host
        port = settings.a2a_port
        
        print(f"🚀 Starting A2A Document Extraction Agent (Clean Architecture)")
        print(f"📍 Server: http://{host}:{port}")
        print(f"📋 Agent card: http://{host}:{port}/.well-known/agent.json")
        print(f"💬 Send messages to: http://{host}:{port}/")
        print(f"🏗️  Using Clean Architecture implementation")
        
        # Run server
        uvicorn.run(app.build(), host=host, port=port)
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise
    finally:
        # Cleanup on shutdown
        import asyncio
        asyncio.run(shutdown_composition_root())


if __name__ == "__main__":
    run_server()