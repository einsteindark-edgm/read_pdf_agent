"""A2A Client CLI implementation for Document Extraction Agent.

This package contains the client-side CLI for interacting with the A2A server.
The actual A2A protocol implementation has been moved to app.infrastructure.a2a
following Clean Architecture principles.
"""

# Re-export client CLI components
from .client_cli.client import DocumentExtractionClient
from .client_cli.interaction import DocumentExtractionInteraction

__all__ = [
    "DocumentExtractionClient",
    "DocumentExtractionInteraction",
]