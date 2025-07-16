"""A2A protocol infrastructure components."""
from .server import create_a2a_app, run_server
from .executor import DocumentExtractionA2AExecutor
from .message_handler import MessageHandler
from .card import get_agent_card

__all__ = [
    "create_a2a_app",
    "run_server",
    "DocumentExtractionA2AExecutor",
    "MessageHandler",
    "get_agent_card"
]