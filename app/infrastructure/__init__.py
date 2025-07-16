"""Infrastructure layer - External dependencies and frameworks."""
from .config import settings, DependencyContainer
from .web import CleanArchitectureA2AExecutor

__all__ = ["settings", "DependencyContainer", "CleanArchitectureA2AExecutor"]
