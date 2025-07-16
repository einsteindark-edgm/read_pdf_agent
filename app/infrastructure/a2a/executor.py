"""A2A Agent Executor for document extraction."""
import json
import logging

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    TaskState,
    InvalidParamsError,
    InternalError,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_agent_parts_message,
    new_data_artifact,
    new_task,
)
from a2a.utils.errors import ServerError

from app.infrastructure.config import DependencyContainer
from .message_handler import MessageHandler

# Setup logging
logger = logging.getLogger(__name__)


class DocumentExtractionA2AExecutor(AgentExecutor):
    """A2A executor for document extraction agent.
    
    This class is responsible for:
    - Receiving A2A protocol messages
    - Passing messages to the AI agent for processing
    - Sending events back through the event queue
    """
    
    def __init__(self):
        """Initialize the executor with Clean Architecture dependencies."""
        self.container = DependencyContainer()
        self.controller = self.container.a2a_controller
        self.presenter = self.container.a2a_presenter
        self.message_handler = MessageHandler()
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure all components are initialized."""
        if not self._initialized:
            logger.info("Initializing Clean Architecture components...")
            await self.container.initialize()
            self._initialized = True
            logger.info("Components initialized successfully")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute extraction request via A2A protocol.
        
        Args:
            context: Request context with message
            event_queue: Queue for sending events back to client
        """
        logger.info("=== EXECUTOR STARTED ===")
        logger.info(f"Context: {context}")
        logger.info(f"Context.current_task: {context.current_task}")
        
        # Ensure MCP is initialized before processing requests
        await self._ensure_initialized()
        
        try:
            # Extract text from message using handler
            text = self.message_handler.extract_user_text(context.message)
            if not text:
                raise ServerError(error=InvalidParamsError())
            
            # Pass the message directly to the agent to process
            await self._handle_agent_request(context, event_queue, text)
            
        except ServerError:
            # Re-raise A2A errors to be handled by the framework
            raise
        except Exception as e:
            # Handle unexpected errors as InternalError
            logger.error(f"Unexpected error in execute: {e}", exc_info=True)
            raise ServerError(error=InternalError())
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation.
        
        Args:
            context: Request context
            event_queue: Event queue for responses
        """
        # Cancellation not supported for extraction tasks
        logger.info("Cancel requested but not supported")
        raise ServerError(error=UnsupportedOperationError())
    
    async def _handle_agent_request(self, context: RequestContext, event_queue: EventQueue, user_message: str) -> None:
        """Handle any user request by passing it to the agent.
        
        Args:
            context: Request context
            event_queue: Event queue for responses
            user_message: The user's natural language message
        """
        try:
            logger.info(f"Processing user message: {user_message}")
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            # Create TaskUpdater for managing long-running operation
            updater = TaskUpdater(event_queue, task.id, task.contextId)
            
            # Send initial status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "🤖 Processing your request...",
                    task.contextId,
                    task.id
                )
            )
            
            # Use controller to process the message
            result = await self.controller.handle_message(user_message)
            
            # Use presenter to format the response
            message_parts = self.presenter.format_response(result)
            
            # Convert presenter output to A2A message format
            a2a_parts = []
            for part in message_parts:
                if hasattr(part.root, 'text'):
                    a2a_parts.append(part.root.text)
                elif hasattr(part.root, 'data'):
                    # Create data artifact
                    artifact = new_data_artifact(
                        part.root.data,
                        part.root.mimeType,
                        part.root.name
                    )
                    a2a_parts.append(artifact)
            
            # Create response message
            if len(a2a_parts) > 1:
                response = new_agent_parts_message(
                    a2a_parts,
                    task.contextId,
                    task.id
                )
            else:
                response = new_agent_text_message(
                    a2a_parts[0] if a2a_parts else "No response",
                    task.contextId,
                    task.id
                )
            
            # Send final response and complete task
            await updater.update_status(
                TaskState.completed,
                response,
                final=True
            )
            logger.info("Request processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            
            # Update task status to failed
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"❌ Error: {str(e)}",
                    task.contextId,
                    task.id
                ),
                final=True
            )
            
            # Re-raise as ServerError for A2A protocol
            raise ServerError(error=InternalError())
    
