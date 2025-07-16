"""Application layer exceptions."""


class ApplicationException(Exception):
    """Base exception for all application layer errors."""
    pass


class UseCaseExecutionError(ApplicationException):
    """Raised when use case execution fails."""
    pass


class InitializationError(ApplicationException):
    """Raised when initialization of a component fails."""
    pass


class ValidationError(ApplicationException):
    """Raised when input validation fails."""
    pass


class ExternalServiceError(ApplicationException):
    """Raised when an external service call fails."""
    pass