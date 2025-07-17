"""A2A executor adapter for Clean Architecture."""
from typing import Dict, Any, Protocol, List
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, InvalidParamsError, InternalError
from a2a.utils import new_agent_text_message, new_agent_parts_message, new_data_artifact, new_task
from a2a.utils.errors import ServerError
import logging


class Controller(Protocol):
    """Protocol for controller."""
    async def handle_message(self, message: str) -> Dict[str, Any]: ...


class MessagePart(Protocol):
    """Protocol for message part."""
    root: Any


class Presenter(Protocol):
    """Protocol for presenter."""
    def format_response(self, result: Dict[str, Any]) -> List[MessagePart]: ...


class CleanArchitectureA2AExecutor(AgentExecutor):
    """A2A executor that adapts Clean Architecture to A2A protocol.
    
    This is an infrastructure adapter that connects the A2A protocol
    to our Clean Architecture implementation.
    """
    
    def __init__(self, controller: Controller, presenter: Presenter):
        """Initialize with controller and presenter.
        
        Args:
            controller: Controller that handles messages
            presenter: Presenter that formats responses
        """
        self.controller = controller
        self.presenter = presenter
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute A2A task.
        
        Args:
            context: Request context
            event_queue: Event queue for responses
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Extract message from context
            user_message = self._extract_user_message(context)
            if not user_message:
                raise ServerError(error=InvalidParamsError())
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            # Create TaskUpdater for managing responses
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
            
            # Use controller to handle the message
            result = await self.controller.handle_message(user_message)
            
            # Use presenter to format response
            message_parts = self.presenter.format_response(result)
            
            # Process response based on parts
            text_content = None
            data_artifact = None
            
            for part in message_parts:
                if hasattr(part.root, 'text'):
                    text_content = part.root.text
                elif hasattr(part.root, 'data'):
                    data_artifact = new_data_artifact(
                        "extraction_result",  # name
                        part.root.data,       # data (dict)
                        "Invoice data extracted from PDF"  # description
                    )
            
            # Create response message with both text and data if available
            if text_content and data_artifact:
                # Combine text with a note about the attached data
                full_message = text_content
                if not "structured data" in text_content.lower():
                    full_message += "\n\n📎 Structured data has been extracted and is available in JSON format."
                
                response = new_agent_text_message(
                    full_message,
                    task.contextId,
                    task.id
                )
                
                # Update task with artifact after sending text message
                # The artifact will be available to the client even though it's not in the message
                task.artifacts = task.artifacts or []
                task.artifacts.append(data_artifact)
                
            elif text_content:
                # Only text response
                response = new_agent_text_message(
                    text_content,
                    task.contextId,
                    task.id
                )
            else:
                # Default response
                response = new_agent_text_message(
                    "No response generated",
                    task.contextId,
                    task.id
                )
            
            # Send final response
            await updater.update_status(
                TaskState.completed,
                response,
                final=True
            )
            
        except ServerError:
            raise
        except Exception as e:
            logger.error(f"Error in CleanArchitectureA2AExecutor: {e}", exc_info=True)
            raise ServerError(error=InternalError())
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel A2A task."""
        from a2a.types import UnsupportedOperationError
        raise ServerError(error=UnsupportedOperationError())
    
    def _extract_user_message(self, context: RequestContext) -> str:
        """Extract user message from context."""
        if not context.message:
            return ""
        
        # Extract text from message parts
        if hasattr(context.message, 'parts') and context.message.parts:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    return part.root.text
        
        return ""