"""Domain-specific exceptions."""


class DomainException(Exception):
    """Base exception for all domain errors."""
    pass


class DocumentNotFoundError(DomainException):
    """Raised when a requested document cannot be found."""
    pass


class InvalidDocumentError(DomainException):
    """Raised when a document is invalid or corrupted."""
    pass


class ExtractionError(DomainException):
    """Raised when extraction fails."""
    pass


class DocumentSizeExceededError(DomainException):
    """Raised when document exceeds size limits."""
    pass


class UnsupportedDocumentTypeError(DomainException):
    """Raised when document type is not supported."""
    pass